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

## Revised physician-blinded test analysis

For the revised Table 3, use linear GEE with patient clustering:

```sh
python "physician blinded test/gee_analysis_package/gee_acceptance_analysis.py" --input "01-S1_Table.xlsx" --output-dir gee_results
```

This replaces the historical patient-level McNemar analysis. Each sub-question
retains 90 paired patient-observer assessments from 30 patients, with three
observers rating both models. No observer responses are collapsed into a
patient-level acceptance classification. See the GEE package README for
Mancl–DeRouen covariance, t(26) inference and Holm adjustment over 17 comparisons.
The Wilcoxon analysis of geometric metrics above is unchanged.

For inter-observer agreement and S2 Table:

```sh
python "physician blinded test/kappa_workbook_package/kappa_analysis.py" --input "01-S1_Table.xlsx" --output agreement_results.json
python "physician blinded test/kappa_workbook_package/update_s2_table.py" --results agreement_results.json --template "01-S2_Table.xlsx" --output "S2_Table_corrected.xlsx"
```

Unanimous acceptance is the proportion of 30 patients accepted by all three
observers, not the proportion of 90 individual ratings accepted. Both fields
are retained separately in the analysis output. The template updater preserves
the supplied supplementary table's formatting. Figure 3's original unanimous
acceptance values were already correct; its visual design is unchanged.
Patient raw data are supplied separately with the manuscript, not uploaded by
these scripts. `validation/` contains aggregate verification results only.
