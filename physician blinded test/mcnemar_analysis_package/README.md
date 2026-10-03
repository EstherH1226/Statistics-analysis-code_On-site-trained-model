# Replaced by the GEE acceptance analysis

The historical McNemar analysis aggregated observer responses within each
patient and used an any-observer-positive endpoint. It is not used in the
revised manuscript. Its source remains available in Git history.

The old filename now forwards to the current GEE implementation:

```sh
python mcnemar_patient_level_analysis.py --input "01-S1_Table.xlsx" --output-dir gee_results
```

See `../gee_analysis_package/README.md` for methods, outputs and validation.
