# Statistics Analysis Code for On-site Trained Model

This repository contains Python scripts used for statistical analysis comparing an on-site trained model with a pre-built model.

## Main Analysis

`onsite_vs_prebuilt_wilcoxon_analysis.py` compares paired results between the on-site trained model and the pre-built model using the Wilcoxon signed-rank test.

The script expects this folder structure:

```text
.
+-- on-site
|   +-- dice_score_f.csv
|   +-- HD95_score_f.csv
|   +-- MSD_score_f.csv
+-- pre-built
|   +-- dice_score_f.csv
|   +-- HD95_score_f.csv
|   +-- MSD_score_f.csv
+-- onsite_vs_prebuilt_wilcoxon_analysis.py
```

Each CSV file should contain an anonymized `patient_id` column and one or more common organ columns, such as:

```text
Heart, Lung_L, Lung_R, patient_id
```

Only organ columns that exist in both the `on-site` and `pre-built` files are analyzed. Paired comparisons are matched by `patient_id` when possible. If no `patient_id` values match and the two files have the same number of rows, the script falls back to row-order pairing.

The anonymized model-comparison CSV files in `on-site/` and `pre-built/` are included in this repository.

## Output

Running the script creates:

```text
onsite_vs_prebuilt_wilcoxon_results.xlsx
```

The Excel file includes:

- `Mean_SD_by_group`: mean, standard deviation, and sample size by model group
- `Wilcoxon_onsite_vs_pre`: paired Wilcoxon signed-rank test results
- `Merged_DSC`, `Merged_HD95`, `Merged_MSD`: patient-level merged data for verification

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Run:

```bash
python onsite_vs_prebuilt_wilcoxon_analysis.py
```

If the output Excel file is already open, close it before running the script again.

## Additional Scripts

Other included scripts support related statistical analyses and figure generation:

- `physician blinded test/kappa_workbook_package/kappa_analysis.py`
- `physician blinded test/kappa_workbook_package/make_kappa_workbook.py`
- `physician blinded test/mcnemar_analysis_package/mcnemar_patient_level_analysis.py`

These scripts are configured to use the raw Excel input file inside each package folder:

```text
physician blinded test/kappa_workbook_package/Raw data_McNemar's test.xlsx
physician blinded test/mcnemar_analysis_package/Raw data_McNemar's test.xlsx
```

The physician blinded test folder may also contain generated result files:

```text
McNemar_patient_level_results.csv
McNemar_subquestion_patient_level_results.csv
Patient_level_subquestion_scores.csv
Patient_level_total_scores.csv
kappa_analysis_results.json
kappa_analysis_results.xlsx
```

These physician blinded test result/data files are excluded from Git by default because they may contain patient-level identifiers.

The packaged folders can be run independently:

```powershell
cd "physician blinded test\kappa_workbook_package"
python kappa_analysis.py
python make_kappa_workbook.py

cd "..\mcnemar_analysis_package"
python mcnemar_patient_level_analysis.py
```
