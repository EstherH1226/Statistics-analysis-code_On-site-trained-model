# Table 3: acceptance rates and between-model comparisons

From the repository root:

```sh
python "physician blinded test/gee_analysis_package/gee_acceptance_analysis.py" --input "01-S1_Table.xlsx" --output-dir gee_results
python "physician blinded test/gee_analysis_package/verify_manuscript_results.py" --input "01-S1_Table.xlsx"
```

The input is the S1 raw-data workbook: patient identifier in column G, model
in H, and 17 sub-questions for RO (I:Y), MP (Z:AP) and DR (AQ:BG).
Sub-questions are Q3-1 through Q3-5, followed by four each for Q4, Q5 and Q6.
Acceptable entries may be 0.2 (Q3), 0.25 (Q4–Q6), or 1; unacceptable is 0.
These entries indicate acceptance; they are not used as analytic weights.
The original workbook is read-only and is never overwritten. Missing values,
unexpected encodings, duplicated patient/model records, or incomplete pairing
cause an error instead of silent exclusion or aggregation.

Each sub-question has 90 paired patient-observer assessments (180 individual
binary observations) nested in 30 patients. Overall acceptance rates use 90
individual assessments per model. Rates for RO, MP and DR use 30 each and are
descriptive only; no separate observer hypothesis tests are performed.

## Model and inference

The model is a linear GEE with an identity link, Gaussian working variance,
working independence, and four coefficients: intercept, model, MP and DR
(RO is reference). The on-site model coefficient estimates the difference
in acceptance rates (on-site minus pre-built).

For this specification the estimating equation has the closed-form least
squares solution. Covariance is calculated using the Mancl–DeRouen correction:
for each patient, residuals are premultiplied by `(I - H_ii)^(-1)` before
constructing the cluster sandwich. The working scale cancels. No additional
CR1 multiplier is applied. Tests and 95% confidence intervals use t(26), where
26 = 30 patient clusters minus four coefficients. Holm adjustment includes
all 17 sub-questions. Confidence intervals are not multiplicity-adjusted.

This is not an independent-observation ordinary least squares test. All six
ratings per patient contribute to the same cluster. No any-observer-positive
or any-sub-question-positive endpoint is used.

Diagnostics include design rank/condition, the largest condition number of
the MD adjustment matrix, corrected and uncorrected sandwich SE, and fitted
value range. The identity-link model may have fitted values outside [0,1];
these are not reported as predicted probabilities. Estimation is closed-form,
so there is no iterative convergence or logistic-separation issue. Inference
with 30 clusters remains approximate despite the small-sample correction.

## Outputs

- `GEE_subquestion_results.csv`: counts, rates, rate differences, confidence
  intervals, unadjusted and Holm-adjusted p-values, and diagnostics.
- `Acceptance_by_observer.csv`: descriptive acceptance rates for RO, MP, DR.
- `analysis_metadata.json`: the analysis specification.

The verification script compares all 17 results against the rounded Table 3
values supplied for the revised manuscript. Aggregate reference outputs are
in `validation/`; raw patient ratings are not included in this commit.

Reference for the covariance correction: Mancl LA, DeRouen TA. A covariance
estimator for GEE with improved small-sample properties. Biometrics.
2001;57:126–134. doi:10.1111/j.0006-341X.2001.00126.x.
