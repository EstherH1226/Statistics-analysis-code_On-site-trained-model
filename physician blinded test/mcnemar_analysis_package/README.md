# McNemar Patient-Level Analysis Package

This folder contains the files needed to run the McNemar and Wilcoxon patient-level analyses for the physician blinded test.

## Files

- `Raw data_McNemar’s test.xlsx`: input data
- `mcnemar_patient_level_analysis.py`: analysis script

## Run

```powershell
python mcnemar_patient_level_analysis.py
```

## Outputs

- `McNemar_patient_level_results.csv`
- `McNemar_subquestion_patient_level_results.csv`
- `Patient_level_subquestion_scores.csv`
- `Patient_level_total_scores.csv`

The McNemar test uses patient-level binary correctness (`score > 0`). The Wilcoxon signed-rank test uses patient-level summed score differences.
