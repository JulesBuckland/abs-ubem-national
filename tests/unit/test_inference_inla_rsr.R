## Hand-verification that INLA's extraconstr mechanism correctly implements
## Restricted Spatial Regression (RSR) for the BYM2 spatial term, before
## trusting it in src/inference/inla/fit_inla.R on real project data.
##
## Background: the PyMC model (src/inference/model_unified.py,
## build_unified_model()) projects the combined BYM2 effect `omega` to be
## exactly orthogonal to `income_z` on every posterior draw
## (omega_star = omega - Z(Z'Z)^-1 Z'omega), which is the standard RSR
## construction (Reich et al. 2006; Hodges & Reich 2010; Hughes & Haran
## 2013 -- all already cited in the manuscript) with the defining property
## sum(income_z_i * omega_i) == 0 exactly (Hanks et al. 2015 state this as
## the constraint X'U(s)=0; confirmed against Lamouroux et al. 2025,
## arXiv:2410.01530, which independently implements RSR via the same
## orthogonality criterion). INLA has no MCMC draws to project post-hoc, so
## the constraint must instead be built into the latent GMRF itself.
##
## Mechanism verified here: f(id, model="bym2", ..., extraconstr=list(A=A,
## e=e)) imposes the exact linear constraint Ax=e on the f-term's latent
## field (INLA's own docs, INLA/html/f.html: "This argument defines extra
## linear constraints ... Ax = e"). Per INLA/documentation/latent/bym2.pdf,
## the bym2 f-term's latent vector x has length 2n: the first n entries are
## the COMBINED field b_i (the direct analogue of PyMC's `omega`), the next
## n are the spatial-only u_i (analogue of PyMC's `phi`) -- confirmed
## empirically by inspecting summary.random$id on a known 3-node case (rows
## 1:n exactly match y-intercept, not rows (n+1):2n). So the RSR constraint
## is A = [income_z^T | 0^T] (1 x 2n), e = 0, applied to the combined field
## only.
##
## Expected result, stated before running: an UNCONSTRAINED fit on data
## with a genuine income_z-correlated spatial confound should show a
## clearly nonzero sum(income_z * E[b]) (there is nothing else in this
## model -- no income_z fixed effect -- for that correlation to go). The
## CONSTRAINED fit (extraconstr as above) should drive that same quantity
## to INLA solver-precision zero (observed: ~1e-8 to ~1e-5 across repeated
## runs, vs. ~18 unconstrained -- a reduction of 6-10 orders of magnitude,
## cor(income_z, b) collapsing from ~0.83 to <1e-4). A run that doesn't show
## this contrast means the mechanism is not doing what the docs claim and
## must not be used on real data.
##
## Run: Rscript tests/unit/test_inference_inla_rsr.R
## Exits non-zero (via stop()) if the verification fails.

library(INLA)
set.seed(20260725)

nx <- 4; ny <- 4
n <- nx * ny
coords <- expand.grid(x = 1:nx, y = 1:ny)
adj <- matrix(0, n, n)
for (i in seq_len(n)) {
  for (j in seq_len(n)) {
    if (i < j) {
      dx <- abs(coords$x[i] - coords$x[j])
      dy <- abs(coords$y[i] - coords$y[j])
      if ((dx == 1 && dy == 0) || (dx == 0 && dy == 1)) {
        adj[i, j] <- 1
        adj[j, i] <- 1
      }
    }
  }
}
g <- inla.read.graph(adj)

income_z_raw <- coords$x - mean(coords$x)
income_z <- as.numeric(income_z_raw / sd(income_z_raw))

## Genuine spatially-smooth field (repeated neighbour-averaging of iid
## noise) mixed with an income_z-aligned component -- the classic
## Reich/Hodges-Reich confounding scenario: a smooth true effect that's
## collinear with a smooth covariate. No income_z fixed effect is included
## in the model below, so a real confound has nowhere to go but into `b`
## unless the constraint removes it.
smooth_noise <- rnorm(n)
nbrs <- lapply(seq_len(n), function(i) which(adj[i, ] == 1))
for (iter in 1:20) {
  smooth_noise <- sapply(seq_len(n), function(i) mean(c(smooth_noise[i], smooth_noise[nbrs[[i]]])))
}
smooth_noise <- as.numeric((smooth_noise - mean(smooth_noise)) / sd(smooth_noise))

true_field <- 1.2 * income_z + 0.8 * smooth_noise
y <- 3.0 + true_field + rnorm(n, sd = 0.05)

cat("cor(income_z, true_field) [confound genuinely present]:", cor(income_z, true_field), "\n\n")

df <- data.frame(y = y, id = 1:n)
hyper_spec <- list(
  phi  = list(prior = "pc", param = c(0.5, 0.5)),
  prec = list(prior = "pc.prec", param = c(1, 0.01))
)

cat("=== Fit 1: no extraconstr (positive control) ===\n")
formula_uc <- y ~ 1 + f(id, model = "bym2", graph = g, scale.model = TRUE, hyper = hyper_spec)
fit_unconstrained <- inla(formula_uc, data = df, family = "gaussian")
b_unconstrained <- fit_unconstrained$summary.random$id$mean[1:n]
zprime_b_unconstrained <- sum(income_z * b_unconstrained)
cat("sum(income_z * E[b]) UNCONSTRAINED:", zprime_b_unconstrained, "\n")
cat("cor(income_z, b) UNCONSTRAINED:", cor(income_z, b_unconstrained), "\n\n")

cat("=== Fit 2: extraconstr = [income_z^T | 0^T], e=0 (the RSR mechanism) ===\n")
A_mat <- matrix(c(income_z, rep(0, n)), nrow = 1)  # 1 x 2n
stopifnot(ncol(A_mat) == 2 * n)
e_vec <- matrix(0, nrow = 1, ncol = 1)
formula_c <- y ~ 1 + f(id, model = "bym2", graph = g, scale.model = TRUE, hyper = hyper_spec,
                        extraconstr = list(A = A_mat, e = e_vec))
fit_constrained <- inla(formula_c, data = df, family = "gaussian")
b_constrained <- fit_constrained$summary.random$id$mean[1:n]
zprime_b_constrained <- sum(income_z * b_constrained)
cat("sum(income_z * E[b]) CONSTRAINED:", zprime_b_constrained, "\n")
cat("cor(income_z, b) CONSTRAINED:", cor(income_z, b_constrained), "\n\n")

cat("=== VERDICT ===\n")
cat(sprintf("|Z'b| unconstrained = %.6f, |Z'b| constrained = %.3e\n",
            abs(zprime_b_unconstrained), abs(zprime_b_constrained)))
tol <- 1e-4  # generous vs. observed ~1e-8..1e-5 solver-precision residuals; still >99.99% removal required
pass <- abs(zprime_b_constrained) < tol && abs(zprime_b_unconstrained) > 0.1
cat(sprintf("PASS: %s\n", pass))
if (!pass) stop("RSR-in-INLA verification FAILED -- do not use extraconstr on real data until this passes.")
cat("RSR-in-INLA mechanism verified: extraconstr drives the covariate/spatial-effect\n")
cat("inner product to numerical zero from a genuine, substantial confound.\n")
