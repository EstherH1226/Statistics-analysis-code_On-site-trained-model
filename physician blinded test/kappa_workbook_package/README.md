# Kappa Workbook Package

This folder contains the files needed to generate the kappa analysis workbook.

## Files

- `Raw data_McNemar’s test.xlsx`: input data
- `kappa_analysis.py`: creates `kappa_analysis_results.json`
- `make_kappa_workbook.py`: creates `kappa_analysis_results.xlsx` from the JSON file

## Run Order

```powershell
python kappa_analysis.py
python make_kappa_workbook.py
```

## Outputs

- `kappa_analysis_results.json`
- `kappa_analysis_results.xlsx`

The workbook includes PABAK, calculated as `2 x observed agreement - 1`.
