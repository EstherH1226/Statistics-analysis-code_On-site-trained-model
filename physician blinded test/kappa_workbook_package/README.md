# Inter-observer agreement and S2 Table

From this directory:

```sh
python kappa_analysis.py --input "01-S1_Table.xlsx" --output kappa_analysis_results.json
python update_s2_table.py --results kappa_analysis_results.json --template "01-S2_Table.xlsx" --output "S2_Table_corrected.xlsx"
python -m unittest test_unanimous_acceptance.py
```

`update_s2_table.py` preserves the supplied manuscript table layout and changes
only its 34 unanimous acceptance values and S3-to-S2 title number. It does not
replace the existing overall summary or restyle the table.

Definitions:
- Overall acceptance: acceptable individual ratings / 90 per sub-question.
- Unanimous acceptance: patients accepted by all three observers / 30.
- Complete agreement: all three accept OR all three reject / 30.
- Observed agreement: mean of the three observer-pair observed agreements.

The analysis JSON and `agreement_by_question.csv` retain these separate fields.
The original Figure 3 unanimous acceptance calculation was correct. The
repository figure script now reads the same JSON field used by the table;
its original rendering functions and layout are retained. Run it with
`python draw_kappa_figure.py` after generating the default JSON in this folder.
No patient workbook is needed by the figure script.

`make_kappa_workbook.py` remains available for the existing analysis workbook
layout. Its question-level column now reports unanimous acceptance. This
analysis workbook is distinct from the manuscript S2 template.

The summary has 510 patient-question combinations (1530 individual ratings)
per model. Bootstrap confidence intervals retain patient-cluster resampling,
5000 draws, seed 20260505. Between-model acceptance testing is handled by the
separate GEE package and is not part of this correction.
