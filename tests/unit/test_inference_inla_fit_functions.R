## Hand-computed unit tests for the pure helper functions in
## src/inference/inla/fit_inla.R (adjacency construction, the RSR
## constraint matrix, hyperparameter transforms, and the quality gate
## decision logic). None of these tests call inla() itself -- that's
## covered by tests/unit/test_inference_inla_rsr.R (the RSR mechanism,
## against real INLA fits) and the pilot/national runs' own gate. Mocking
## the *fit* structure here (a plain list standing in for what inla()
## would return) is legitimate per this project's testing standard: it is
## a true external dependency (an expensive optimizer call), and the
## decision logic under test here is pure post-processing over its output.
##
## Run (from repo root): Rscript tests/unit/test_inference_inla_fit_functions.R
## (testthat::test_file() was tried first but changes the working directory
## in a way that breaks this file's relative source() path on this machine,
## and separately triggered an unrelated Rscript segfault on this session's
## R install -- plain `Rscript <file>` execution of testthat::test_that()
## blocks works reliably and is what every R script in this project uses.)

library(testthat)
library(Matrix)

source(file.path("src", "inference", "inla", "fit_inla.R"))

test_that("build_adjacency produces the exact symmetric sparse matrix for a 3-node chain", {
  # 3-node chain, 1-indexed: edges (1,2) and (2,3).
  edges_df <- data.frame(node1 = c(1, 2), node2 = c(2, 3))
  W <- build_adjacency(edges_df, n = 3)
  expected <- matrix(c(
    0, 1, 0,
    1, 0, 1,
    0, 1, 0
  ), nrow = 3, byrow = TRUE)
  expect_equal(as.matrix(W), expected, ignore_attr = TRUE)
})

test_that("build_rsr_constraint places income_z in the first n columns and zeros in the next n", {
  income_z <- c(-1.0, 0.0, 1.0)
  constraint <- build_rsr_constraint(income_z, n = 3)
  expect_equal(dim(constraint$A), c(1, 6))
  expect_equal(as.numeric(constraint$A[1, 1:3]), income_z)
  expect_equal(as.numeric(constraint$A[1, 4:6]), c(0, 0, 0))
  expect_equal(as.numeric(constraint$e), 0)
})

test_that("transform_hyperpar converts INLA's raw hyperpar names/units by hand-computable formulas", {
  # Hand-computed: prec_obs=4 -> sigma_err=1/sqrt(4)=0.5; prec_id=0.25 ->
  # sigma_spatial=1/sqrt(0.25)=2.0; phi passes through unchanged as rho.
  fake_hyperpar <- data.frame(
    mean = c(4, 0.25, 0.7),
    row.names = c("Precision for the Gaussian observations", "Precision for id", "Phi for id")
  )
  fit <- list(summary.hyperpar = fake_hyperpar)
  result <- transform_hyperpar(fit)
  expect_equal(result$sigma_err, 0.5)
  expect_equal(result$sigma_spatial, 2.0)
  expect_equal(result$rho, 0.7)
})

test_that("check_inla_quality_gate passes a clean fit with no laplace cross-check", {
  clean_fit <- list(
    mode = list(mode.status = 0),
    summary.fixed = data.frame(mean = c(-0.3, 0.05)),
    summary.hyperpar = data.frame(mean = c(4, 2, 0.6)),
    cpo = list(failure = rep(0, 10))
  )
  gate <- check_inla_quality_gate(clean_fit, fit_laplace = NULL)
  expect_true(gate$passed)
  expect_equal(gate$cpo_failure_count, 0)
})

test_that("check_inla_quality_gate fails on nonzero mode.status", {
  bad_fit <- list(
    mode = list(mode.status = 1),
    summary.fixed = data.frame(mean = c(-0.3, 0.05)),
    summary.hyperpar = data.frame(mean = c(4, 2, 0.6)),
    cpo = list(failure = rep(0, 10))
  )
  gate <- check_inla_quality_gate(bad_fit, fit_laplace = NULL)
  expect_false(gate$passed)
  expect_true(any(grepl("mode.status", gate$problems)))
})

test_that("check_inla_quality_gate fails when too many CPO failures exceed the threshold", {
  fit_many_failures <- list(
    mode = list(mode.status = 0),
    summary.fixed = data.frame(mean = c(-0.3, 0.05)),
    summary.hyperpar = data.frame(mean = c(4, 2, 0.6)),
    cpo = list(failure = c(rep(1, 11), rep(0, 5)))  # 11 failures, max allowed default 10
  )
  gate <- check_inla_quality_gate(fit_many_failures, fit_laplace = NULL)
  expect_false(gate$passed)
  expect_equal(gate$cpo_failure_count, 11)
})

test_that("check_inla_quality_gate fails when simplified vs full laplace disagree materially", {
  fit_simplified <- list(
    mode = list(mode.status = 0),
    summary.fixed = data.frame(mean = c(-0.3, 0.05)),
    summary.hyperpar = data.frame(
      mean = c(4, 2, 0.6),
      row.names = c("Precision for the Gaussian observations", "Precision for id", "Phi for id")
    ),
    cpo = list(failure = rep(0, 10))
  )
  # Deliberately very different hyperparameters -> should be flagged.
  fit_laplace_disagreeing <- list(
    summary.fixed = data.frame(mean = c(-0.3, 0.05)),
    summary.hyperpar = data.frame(
      mean = c(0.5, 0.1, 0.05),  # wildly different precision/phi values
      row.names = c("Precision for the Gaussian observations", "Precision for id", "Phi for id")
    )
  )
  gate <- check_inla_quality_gate(fit_simplified, fit_laplace = fit_laplace_disagreeing,
                                   max_relative_disagreement = 0.05)
  expect_false(gate$passed)
  expect_true(gate$max_relative_disagreement > 0.05)
})

test_that("check_inla_quality_gate passes when simplified vs full laplace closely agree", {
  fit_simplified <- list(
    mode = list(mode.status = 0),
    summary.fixed = data.frame(mean = c(-0.3, 0.05)),
    summary.hyperpar = data.frame(
      mean = c(4, 2, 0.6),
      row.names = c("Precision for the Gaussian observations", "Precision for id", "Phi for id")
    ),
    cpo = list(failure = rep(0, 10))
  )
  fit_laplace_agreeing <- list(
    summary.fixed = data.frame(mean = c(-0.301, 0.0498)),
    summary.hyperpar = data.frame(
      mean = c(4.01, 2.02, 0.601),  # within 1% of the simplified fit
      row.names = c("Precision for the Gaussian observations", "Precision for id", "Phi for id")
    )
  )
  gate <- check_inla_quality_gate(fit_simplified, fit_laplace = fit_laplace_agreeing,
                                   max_relative_disagreement = 0.05)
  expect_true(gate$passed)
})
