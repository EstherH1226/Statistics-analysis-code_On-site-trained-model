# Kappa Workbook Package

This folder contains the files needed to generate the kappa analysis workbook.

## Files

- `Raw data_McNemar’s test.xlsx`: input data
- `kappa_analysis.py`: creates `kappa_analysis_results.json`
- `make_kappa_workbook.py`: creates `kappa_analysis_results.xlsx` from the JSON file
- `draw_kappa_figure.py`: creates kappa figure files from the JSON file and raw Excel file

## Run Order

```powershell
python kappa_analysis.py
python make_kappa_workbook.py
python draw_kappa_figure.py
```

## Outputs

- `kappa_analysis_results.json`
- `kappa_analysis_results.xlsx`
- `kappa_agreement_acceptance_figure.png`
- `kappa_agreement_acceptance_figure.pdf`
- `kappa_model_summary.png`
- `kappa_model_summary.pdf`
- `kappa_model_summary.tiff`
- `kappa_panel_A_fleiss_kappa.png`
- `kappa_panel_A_fleiss_kappa.pdf`
- `kappa_panel_A_fleiss_kappa.tiff`
- `kappa_panel_B_observed_agreement.png`
- `kappa_panel_B_observed_agreement.pdf`
- `kappa_panel_B_observed_agreement.tiff`
- `kappa_panel_C_all_3_accepted.png`
- `kappa_panel_C_all_3_accepted.pdf`
- `kappa_panel_C_all_3_accepted.tiff`

The workbook includes PABAK, calculated as `2 x observed agreement - 1`.
