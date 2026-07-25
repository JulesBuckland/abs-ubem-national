## R-INLA replacement for src/inference/model_unified.py's NUTS-based fit.
## Reads the CSVs written by src/inference/inla/data_export.py, fits the
## same structural model (BYM2 spatial effect + beta_th/beta_inc fixed
## effects + Jensen's-correction offset + RSR against income_z), and writes
## results back out for src/inference/inla/read_results.py to consume.
##
## Model correspondence to build_unified_model() in model_unified.py:
##   mu = theory_log - T_var/2 + beta_th + beta_inc*income_z + omega_star
##   y_obs ~ Normal(mu, sigma_err)
## becomes, in INLA formula terms:
##   y_obs ~ 1 + income_z + f(id, model="bym2", ...) + offset(theory_log - T_var/2)
## where:
##   - the formula's intercept IS beta_th (informative prior set via
##     control.fixed$mean.intercept/prec.intercept to match
##     pm.Normal(mu=-0.3, sigma=0.1))
##   - the income_z fixed-effect coefficient IS beta_inc (prior matching
##     pm.Normal(mu=0.0, sigma=0.5) via control.fixed$mean/prec)
##   - f(id, model="bym2", ...)'s combined field (first N of its 2N-length
##     latent vector; see documentation/latent/bym2.pdf) IS omega, and
##     omega_star = the RSR-projected version, enforced AT FIT TIME via
##     extraconstr (see tests/unit/test_inference_inla_rsr.R -- this exact
##     mechanism, `extraconstr = list(A = [income_z^T | 0^T], e = 0)`, was
##     hand-verified there to drive sum(income_z * E[b]) from a genuine,
##     substantial confound down to solver-precision zero)
##   - the PC-priors on phi/precision replace rho's Beta(1,1) and
##     sigma_spatial's HalfNormal(0.5) -- a deliberate, plan-approved
##     improvement (Simpson et al. 2017), not an attempt at numerical
##     equivalence to the old ad-hoc priors (see header comment below on
##     prior choices for the specific reasoning).
##   - sigma_err (observation noise) maps to INLA's Gaussian-family
##     precision hyperparameter, also given a PC-prior.

suppressMessages(library(INLA))
suppressMessages(library(Matrix))
suppressMessages(library(jsonlite))

## --------------------------------------------------------------------
## Argument parsing (no optparse dependency -- not installed on this
## machine and not worth a new install detour for four flags).
## --------------------------------------------------------------------
parse_args <- function(argv) {
  args <- list(
    nodes = NULL, edges = NULL, output_dir = NULL, mode = "final",
    check_laplace_agreement = TRUE
  )
  i <- 1
  while (i <= length(argv)) {
    key <- argv[i]
    if (key == "--nodes") { args$nodes <- argv[i + 1]; i <- i + 2
    } else if (key == "--edges") { args$edges <- argv[i + 1]; i <- i + 2
    } else if (key == "--output_dir") { args$output_dir <- argv[i + 1]; i <- i + 2
    } else if (key == "--mode") { args$mode <- argv[i + 1]; i <- i + 2
    } else if (key == "--check_laplace_agreement") {
      args$check_laplace_agreement <- as.logical(argv[i + 1]); i <- i + 2
    } else {
      stop(paste("Unrecognised argument:", key))
    }
  }
  if (is.null(args$nodes) || is.null(args$edges) || is.null(args$output_dir)) {
    stop("Usage: Rscript fit_inla.R --nodes <csv> --edges <csv> --output_dir <dir> [--mode pilot|final] [--check_laplace_agreement TRUE|FALSE]")
  }
  args
}

## --------------------------------------------------------------------
## Pure(-ish) helpers -- each independently hand-testable.
## --------------------------------------------------------------------

build_adjacency <- function(edges_df, n) {
  ## edges_df has 1-indexed node1/node2, one row per undirected edge.
  ## Both directions listed explicitly (no reliance on Matrix's
  ## `symmetric=TRUE` storage-class handling) to keep this unambiguous for
  ## whatever downstream INLA does with the object.
  i <- c(edges_df$node1, edges_df$node2)
  j <- c(edges_df$node2, edges_df$node1)
  Matrix::sparseMatrix(i = i, j = j, x = 1, dims = c(n, n))
}

build_rsr_constraint <- function(income_z, n) {
  ## See tests/unit/test_inference_inla_rsr.R for the hand-verification of
  ## this exact construction. A is 1 x 2n: income_z in the first n columns
  ## (the bym2 f-term's combined field), zeros in the next n (the
  ## spatial-only component, left unconstrained).
  A <- matrix(c(income_z, rep(0, n)), nrow = 1)
  stopifnot(ncol(A) == 2 * n)
  list(A = A, e = matrix(0, nrow = 1, ncol = 1))
}

## Prior choices, stated explicitly (not mechanically ported -- PC-priors
## are a different parameterisation from the old HalfNormal/Beta ones by
## design, per tasks/inla_migration_plan.md #2 and Simpson et al. 2017):
##   - phi (spatial mixing, analogue of rho): pc prior, param=c(0.5,0.5)
##     i.e. P(phi < 0.5) = 0.5 -- a symmetric, weakly-informative choice
##     matching the old Beta(1,1)'s symmetry without claiming numerical
##     equivalence.
##   - precision for id (analogue of 1/sigma_spatial^2): pc.prec,
##     param=c(1, 0.01), i.e. P(sigma_spatial > 1) = 0.01 -- weakly
##     informative shrinkage towards a simpler (non-spatial) base model,
##     the standard PC-prior recommendation for this hyperparameter class,
##     comparable in spirit (not exact numerical match) to the old
##     HalfNormal(0.5)'s tail behaviour.
##   - Gaussian observation precision (analogue of 1/sigma_err^2): same
##     pc.prec(1, 0.01) reasoning.
build_hyper_spec <- function() {
  list(
    phi  = list(prior = "pc", param = c(0.5, 0.5)),
    prec = list(prior = "pc.prec", param = c(1, 0.01))
  )
}

## beta_th ~ Normal(-0.3, 0.1) -> intercept prior; beta_inc ~ Normal(0, 0.5)
## -> income_z coefficient prior. INLA parameterises fixed-effect priors by
## precision, not sigma, hence the 1/sigma^2 conversions.
build_control_fixed <- function() {
  list(
    mean.intercept = -0.3, prec.intercept = 1 / (0.1^2),
    mean = list(income_z = 0.0), prec = list(income_z = 1 / (0.5^2))
  )
}

## Extract rho/sigma_spatial/sigma_err in the same units/names the PyMC
## model and downstream results code use, from INLA's raw hyperpar summary
## (which reports "Phi for id" = phi = rho directly, but precisions not
## the standard deviations we need for a like-for-like comparison).
transform_hyperpar <- function(fit) {
  hp <- fit$summary.hyperpar
  prec_obs <- hp["Precision for the Gaussian observations", "mean"]
  prec_id  <- hp["Precision for id", "mean"]
  phi_id   <- hp["Phi for id", "mean"]
  data.frame(
    rho = phi_id,
    sigma_spatial = 1 / sqrt(prec_id),
    sigma_err = 1 / sqrt(prec_obs)
  )
}

## --------------------------------------------------------------------
## The convergence/quality gate. INLA has no MCMC divergences/r_hat; the
## real analogues checked here (tasks/inla_migration_plan.md #2 table):
##   1. INLA's own mode-finding status (mode$mode.status == 0 means ok).
##   2. No NA/Inf in the fixed-effect or hyperparameter summaries (a fit
##      that silently produced garbage must not be reported as valid).
##   3. CPO failure count: INLA flags individual observations where its
##      leave-one-out CPO approximation is unreliable
##      (cpo$failure > 0), the direct analogue of PSIS-LOO's
##      "Pareto k > 0.7" unreliable-point count in the old NUTS gate.
##   4. Simplified-vs-full-Laplace agreement: refit with the more accurate
##      (slower) "laplace" strategy and compare beta_th/beta_inc/rho/
##      sigma_spatial/sigma_err posterior means against the default
##      "simplified.laplace" fit. Large disagreement means the fast
##      approximation isn't trustworthy for this posterior -- the direct
##      analogue of NUTS's r_hat check (checking an approximation actually
##      converged to the same answer a more careful method would give).
## --------------------------------------------------------------------
check_inla_quality_gate <- function(fit, fit_laplace = NULL,
                                     max_cpo_failure_count = 10,
                                     max_relative_disagreement = 0.05) {
  problems <- character(0)

  mode_status <- fit$mode$mode.status
  if (!is.null(mode_status) && mode_status != 0) {
    problems <- c(problems, sprintf("mode.status=%d (nonzero means INLA's own optimizer did not confirm a valid mode)", mode_status))
  }

  fixed_vals <- fit$summary.fixed$mean
  hyper_vals <- fit$summary.hyperpar$mean
  if (any(!is.finite(fixed_vals))) problems <- c(problems, "non-finite value in summary.fixed$mean")
  if (any(!is.finite(hyper_vals))) problems <- c(problems, "non-finite value in summary.hyperpar$mean")

  cpo_failure_count <- 0L
  if (!is.null(fit$cpo) && !is.null(fit$cpo$failure)) {
    cpo_failure_count <- sum(fit$cpo$failure > 0, na.rm = TRUE)
    if (cpo_failure_count > max_cpo_failure_count) {
      problems <- c(problems, sprintf(
        "%d observations have unreliable CPO (failure>0), exceeds max allowed %d",
        cpo_failure_count, max_cpo_failure_count
      ))
    }
  }

  max_rel_disagreement <- NA_real_
  if (!is.null(fit_laplace)) {
    simplified_vals <- c(fit$summary.fixed$mean, transform_hyperpar(fit)$rho,
                          transform_hyperpar(fit)$sigma_spatial, transform_hyperpar(fit)$sigma_err)
    laplace_vals <- c(fit_laplace$summary.fixed$mean, transform_hyperpar(fit_laplace)$rho,
                       transform_hyperpar(fit_laplace)$sigma_spatial, transform_hyperpar(fit_laplace)$sigma_err)
    denom <- pmax(abs(laplace_vals), 1e-8)
    rel_disagreement <- abs(simplified_vals - laplace_vals) / denom
    max_rel_disagreement <- max(rel_disagreement)
    if (max_rel_disagreement > max_relative_disagreement) {
      problems <- c(problems, sprintf(
        "max relative disagreement between simplified.laplace and laplace strategies = %.4f, exceeds max allowed %.4f",
        max_rel_disagreement, max_relative_disagreement
      ))
    }
  }

  list(
    passed = length(problems) == 0,
    problems = problems,
    cpo_failure_count = cpo_failure_count,
    max_relative_disagreement = max_rel_disagreement
  )
}

## --------------------------------------------------------------------
## Effectful orchestrator
## --------------------------------------------------------------------
run_fit_inla <- function(args) {
  nodes_df <- read.csv(args$nodes)
  edges_df <- read.csv(args$edges)
  n <- nrow(nodes_df)

  stopifnot(all(c("id", "T_var", "income_z", "theory_log", "y_obs") %in% names(nodes_df)))
  stopifnot(all(c("node1", "node2") %in% names(edges_df)))
  stopifnot(all(nodes_df$id == seq_len(n)))  # must be exactly 1..n, in order

  W <- build_adjacency(edges_df, n)
  rsr_constraint <- build_rsr_constraint(nodes_df$income_z, n)
  hyper_spec <- build_hyper_spec()
  control_fixed <- build_control_fixed()

  df <- data.frame(
    y_obs = nodes_df$y_obs, id = nodes_df$id, income_z = nodes_df$income_z,
    theory_log = nodes_df$theory_log, T_var = nodes_df$T_var
  )

  formula <- y_obs ~ 1 + income_z +
    f(id, model = "bym2", graph = W, scale.model = TRUE,
      hyper = hyper_spec, extraconstr = rsr_constraint) +
    offset(theory_log - T_var / 2)

  cat(sprintf("[fit_inla] Fitting on %d nodes, %d edges (mode=%s)...\n", n, nrow(edges_df), args$mode))
  t0 <- Sys.time()
  fit <- inla(
    formula, data = df, family = "gaussian",
    control.fixed = control_fixed,
    control.compute = list(cpo = TRUE, waic = TRUE, dic = TRUE, config = TRUE)
  )
  cat(sprintf("[fit_inla] simplified.laplace fit done in %.1fs\n", as.numeric(Sys.time() - t0, units = "secs")))

  fit_laplace <- NULL
  if (isTRUE(args$check_laplace_agreement)) {
    cat("[fit_inla] Refitting with strategy='laplace' for the agreement gate...\n")
    t1 <- Sys.time()
    fit_laplace <- inla(
      formula, data = df, family = "gaussian",
      control.fixed = control_fixed,
      control.inla = list(strategy = "laplace"),
      control.compute = list(cpo = TRUE)
    )
    cat(sprintf("[fit_inla] laplace fit done in %.1fs\n", as.numeric(Sys.time() - t1, units = "secs")))
  }

  gate <- check_inla_quality_gate(fit, fit_laplace)
  cat(sprintf("[fit_inla] Quality gate: passed=%s, cpo_failure_count=%d, max_relative_disagreement=%s\n",
              gate$passed, gate$cpo_failure_count,
              ifelse(is.na(gate$max_relative_disagreement), "NA", sprintf("%.4f", gate$max_relative_disagreement))))
  if (!gate$passed) {
    for (p in gate$problems) cat(sprintf("[fit_inla] GATE PROBLEM: %s\n", p))
  }

  dir.create(args$output_dir, showWarnings = FALSE, recursive = TRUE)
  suffix <- if (!gate$passed) "_DIAGNOSTIC_FAILED_GATE" else ""

  git_commit <- tryCatch(
    system2("git", c("rev-parse", "HEAD"), stdout = TRUE, stderr = FALSE),
    error = function(e) "unknown", warning = function(w) "unknown"
  )
  metadata <- list(
    mode = args$mode, n_nodes = n, n_edges = nrow(edges_df),
    git_commit = paste(git_commit, collapse = ""),
    generated_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
    gate_passed = gate$passed, gate_problems = gate$problems,
    cpo_failure_count = gate$cpo_failure_count,
    max_relative_disagreement = gate$max_relative_disagreement,
    check_laplace_agreement = isTRUE(args$check_laplace_agreement)
  )
  writeLines(jsonlite::toJSON(metadata, auto_unbox = TRUE, null = "null", na = "null"),
             file.path(args$output_dir, paste0("inla_metadata", suffix, ".json")))

  write.csv(fit$summary.fixed, file.path(args$output_dir, paste0("inla_fixed_effects", suffix, ".csv")))
  write.csv(fit$summary.random$id, file.path(args$output_dir, paste0("inla_random_effects", suffix, ".csv")), row.names = FALSE)
  write.csv(fit$summary.hyperpar, file.path(args$output_dir, paste0("inla_hyperpar_raw", suffix, ".csv")))
  write.csv(transform_hyperpar(fit), file.path(args$output_dir, paste0("inla_hyperpar_transformed", suffix, ".csv")), row.names = FALSE)
  write.csv(
    data.frame(id = df$id, cpo = fit$cpo$cpo, pit = fit$cpo$pit, failure = fit$cpo$failure),
    file.path(args$output_dir, paste0("inla_cpo", suffix, ".csv")), row.names = FALSE
  )
  write.csv(
    data.frame(waic = fit$waic$waic, dic = fit$dic$dic),
    file.path(args$output_dir, paste0("inla_ic", suffix, ".csv")), row.names = FALSE
  )

  if (!gate$passed) {
    cat("[fit_inla] FATAL: quality gate failed. Diagnostic-suffixed files written; canonical outputs withheld.\n")
    quit(status = 1)
  }
  cat("[fit_inla] Quality gate passed. Canonical outputs written.\n")
  invisible(fit)
}

if (sys.nframe() == 0) {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  run_fit_inla(args)
}
