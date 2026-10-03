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

## Analyses used in the revised manuscript

| Manuscript component | Script |
| --- | --- |
| Geometric metrics: paired Wilcoxon comparisons | `onsite_vs_prebuilt_wilcoxon_analysis.py` |
| Table 3: acceptance rates and GEE comparisons | `physician blinded test/gee_analysis_package/gee_acceptance_analysis.py` |
| Inter-observer agreement and unanimous acceptance | `physician blinded test/kappa_workbook_package/kappa_analysis.py` |
| Agreement analysis workbook | `physician blinded test/kappa_workbook_package/make_kappa_workbook.py` |
| S2 Table in the original manuscript format | `physician blinded test/kappa_workbook_package/update_s2_table.py` |
| Agreement figure (Figure 3) | `physician blinded test/kappa_workbook_package/draw_kappa_figure.py` |

### Table 3

From the repository root, supply the individual ratings in S1 Table:

```sh
python "physician blinded test/gee_analysis_package/gee_acceptance_analysis.py" --input "01-S1_Table.xlsx" --output-dir gee_results
```

The analysis uses Gaussian identity-link GEE with patient clustering, observer
fixed effects, Mancl–DeRouen covariance, t(26) inference, and Holm adjustment
across 17 sub-questions. See the package README for the analysis specification.

### Agreement, S2 Table and Figure 3

Place the S1 raw-data workbook and S2 manuscript template in
`physician blinded test/kappa_workbook_package`, then run from that directory:

```sh
python kappa_analysis.py --input "01-S1_Table.xlsx"
python make_kappa_workbook.py
python update_s2_table.py --results kappa_analysis_results.json --template "01-S2_Table.xlsx" --output "S2_Table_corrected.xlsx"
python draw_kappa_figure.py
```

Run the analysis first so the workbook and figure use the newly computed JSON.
Unanimous acceptance is the proportion of 30 patients accepted by all three
observers, distinct from overall acceptance among 90 individual ratings.
The S2 updater preserves the supplied template formatting; the figure script
retains its existing rendering and layout.

Individual physician ratings and manuscript templates are supplied separately
with the manuscript. Generated outputs are not tracked. The anonymized geometric
metric CSV inputs remain included for reproducibility.
