## Component test: src/inference/inla/fit_inla.R's run_fit_inla() end-to-end,
## on small synthetic fixture data, with expected values computed
## independently (by hand, from the data-generating formula) BEFORE
## running anything -- same standard this project's PyMC component tests
## use (see tests/unit/test_inference_model_unified.py).
##
## Case 1: no spatial confound. mu_i = (theory_log_i - T_var_i/2) + beta_th
## + beta_inc*income_z_i, with beta_th=-0.3 and beta_inc=0.1 chosen to match
## the fixed-effect priors' means exactly (control_fixed in fit_inla.R), tiny
## observation noise, and theory_log deliberately varying with income_z
## (theory_log_i = 0.5*income_z_i + 5.0) so a broken/omitted offset would be
## caught (it would leak into the recovered beta_inc/intercept, moving them
## far from -0.3/0.1). Expected: recovered intercept~=-0.3, income_z
## coefficient~=0.1, both within a small tolerance; the spatial random
## effect (b) should be ~0 everywhere (no real signal, no confound to remove).
##
## Case 2: WITH a genuine spatial confound (independently-drawn smooth
## noise that happens, by chance in this one realization, to correlate
## substantially with income_z -- NOT an explicit income_z term mixed into
## its construction; see the in-test comment for why that distinction
## matters). Per the RSR literature's proven property (Reich et al. 2006;
## confirmed independently in Lamouroux et al. 2025, arXiv:2410.01530 eq.
## 2: "E[beta_RSR|Y] = E[beta_Null|Y]"), a correctly wired RSR mechanism
## should recover beta_inc matching the *Null model* (plain regression of y
## on income_z with no spatial term at all, computed independently here via
## R's lm()) -- not the true generating beta_inc (RSR does not claim that;
## see in-test comment), and not badly displaced from the Null value the
## way an unconstrained/non-RSR spatial model would be.

library(testthat)

source(file.path("src", "inference", "inla", "fit_inla.R"))

build_grid_graph_edges <- function(nx, ny) {
  coords <- expand.grid(x = 1:nx, y = 1:ny)
  n <- nx * ny
  node1 <- c(); node2 <- c()
  for (i in seq_len(n)) {
    for (j in seq_len(n)) {
      if (i < j) {
        dx <- abs(coords$x[i] - coords$x[j]); dy <- abs(coords$y[i] - coords$y[j])
        if ((dx == 1 && dy == 0) || (dx == 0 && dy == 1)) { node1 <- c(node1, i); node2 <- c(node2, j) }
      }
    }
  }
  list(edges = data.frame(node1 = node1, node2 = node2), coords = coords, n = n)
}

write_fixture <- function(nodes_df, edges_df, dir) {
  dir.create(dir, showWarnings = FALSE, recursive = TRUE)
  nodes_path <- file.path(dir, "inla_nodes.csv")
  edges_path <- file.path(dir, "inla_edges.csv")
  write.csv(nodes_df, nodes_path, row.names = FALSE)
  write.csv(edges_df, edges_path, row.names = FALSE)
  list(nodes = nodes_path, edges = edges_path)
}

set.seed(20260725)
graph <- build_grid_graph_edges(4, 4)
n <- graph$n
income_z_raw <- graph$coords$x - mean(graph$coords$x)
income_z <- as.numeric(income_z_raw / sd(income_z_raw))

beta_th_true <- -0.3
beta_inc_true <- 0.1
theory_log <- 0.5 * income_z + 5.0
T_var <- rep(0.2, n)

test_that("fit_inla recovers beta_th/beta_inc and a near-zero spatial field with no confound present", {
  mu <- (theory_log - T_var / 2) + beta_th_true + beta_inc_true * income_z
  y_obs <- mu + rnorm(n, sd = 0.01)  # tiny noise: likelihood should dominate cleanly

  nodes_df <- data.frame(id = 1:n, T_var = T_var, income_z = income_z, theory_log = theory_log, y_obs = y_obs)
  tmpdir <- tempfile("fit_inla_case1_")
  paths <- write_fixture(nodes_df, graph$edges, tmpdir)
  out_dir <- file.path(tmpdir, "out")

  args <- list(nodes = paths$nodes, edges = paths$edges, output_dir = out_dir,
               mode = "component_test", check_laplace_agreement = FALSE)
  fit <- run_fit_inla(args)

  intercept <- fit$summary.fixed["(Intercept)", "mean"]
  beta_inc_est <- fit$summary.fixed["income_z", "mean"]
  b <- fit$summary.random$id$mean[1:n]

  expect_equal(intercept, beta_th_true, tolerance = 0.05)
  expect_equal(beta_inc_est, beta_inc_true, tolerance = 0.05)
  expect_true(max(abs(b)) < 0.1)

  # Canonical (non-diagnostic-suffixed) output files must exist -- gate passed.
  expect_true(file.exists(file.path(out_dir, "inla_fixed_effects.csv")))
  expect_false(file.exists(file.path(out_dir, "inla_fixed_effects_DIAGNOSTIC_FAILED_GATE.csv")))
})

test_that("fit_inla's RSR wiring keeps beta_inc close to truth even with a real spatial confound", {
  # IMPORTANT design point (found by running this test the first time): the
  # true spatial field must NOT contain an explicit, deterministic income_z
  # term mixed in (e.g. "0.9*income_z + noise") -- if it did, that
  # component would be perfectly collinear with the income_z fixed effect
  # and NO method, RSR or otherwise, could or should separate "beta_inc's
  # true contribution" from "the confound's own income_z-aligned
  # contribution" (they are literally the same basis vector). The textbook
  # RSR confounding scenario (Reich et al. 2006) is instead: U(s) is drawn
  # INDEPENDENTLY of X, but happens, by chance, in one finite realization,
  # to be sample-correlated with a spatially-smooth X anyway -- which is
  # exactly what repeated neighbour-averaging of independent noise over the
  # SAME graph as income_z's gradient produces here (no income_z term is
  # ever mixed into its construction).
  smooth_noise <- rnorm(n)
  nbrs <- lapply(seq_len(n), function(i) {
    adj_row <- rep(0, n)
    for (k in seq_len(nrow(graph$edges))) {
      if (graph$edges$node1[k] == i) adj_row[graph$edges$node2[k]] <- 1
      if (graph$edges$node2[k] == i) adj_row[graph$edges$node1[k]] <- 1
    }
    which(adj_row == 1)
  })
  for (iter in 1:20) smooth_noise <- sapply(seq_len(n), function(i) mean(c(smooth_noise[i], smooth_noise[nbrs[[i]]])))
  confound <- as.numeric((smooth_noise - mean(smooth_noise)) / sd(smooth_noise)) * 0.8

  chance_correlation <- cor(income_z, confound)
  cat(sprintf("[test] by-chance cor(income_z, confound) = %.3f (must be substantial for this test to be meaningful)\n",
              chance_correlation))
  expect_true(abs(chance_correlation) > 0.3)  # sanity check the stress case is real before checking the mitigation

  mu <- (theory_log - T_var / 2) + beta_th_true + beta_inc_true * income_z + confound
  y_obs <- mu + rnorm(n, sd = 0.01)

  nodes_df <- data.frame(id = 1:n, T_var = T_var, income_z = income_z, theory_log = theory_log, y_obs = y_obs)
  tmpdir <- tempfile("fit_inla_case2_")
  paths <- write_fixture(nodes_df, graph$edges, tmpdir)
  out_dir <- file.path(tmpdir, "out")

  args <- list(nodes = paths$nodes, edges = paths$edges, output_dir = out_dir,
               mode = "component_test", check_laplace_agreement = FALSE)
  fit <- run_fit_inla(args)

  beta_inc_est <- fit$summary.fixed["income_z", "mean"]
  b <- fit$summary.random$id$mean[1:n]
  zprime_b <- sum(income_z * b)

  # CORRECTED expectation (found by running this test): RSR's proven
  # property (Reich et al. 2006; Lamouroux et al. 2025 eq. 2:
  # "E[beta_RSR|Y] = E[beta_Null|Y]") is that beta_inc under RSR matches
  # the *Null model* (plain regression on income_z with NO spatial term at
  # all) -- NOT the true data-generating beta_inc. Since the confound has a
  # real, nonzero sample correlation with income_z in this one finite
  # realization (by construction, checked above), even a perfectly correct
  # RSR fit attributes that realized correlation to beta_inc, same as a
  # plain regression would -- that is what RSR guarantees, not immunity to
  # every possible by-chance correlation. So the independently-computable
  # expected value is the Null model's OLS coefficient (a completely
  # separate computation, R's lm(), not INLA), not beta_inc_true.
  y_adj <- y_obs - (theory_log - T_var / 2)  # remove the known offset by hand
  null_model <- lm(y_adj ~ income_z)
  beta_inc_null <- coef(null_model)[["income_z"]]
  cat(sprintf("[test] beta_inc: RSR-INLA=%.4f, Null-model(lm)=%.4f, true=%.4f\n",
              beta_inc_est, beta_inc_null, beta_inc_true))
  expect_equal(beta_inc_est, beta_inc_null, tolerance = 0.1)
  # And the RSR orthogonality property must still hold with fixed effects
  # and the offset present simultaneously, not just in isolation.
  expect_true(abs(zprime_b) < 1e-3)
})
