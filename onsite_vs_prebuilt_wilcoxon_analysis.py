from pathlib import Path

import pandas as pd
from scipy.stats import wilcoxon


BASE_DIR = Path(__file__).resolve().parent
ONSITE_DIR = BASE_DIR / "on-site"
PREBUILT_DIR = BASE_DIR / "pre-built"
OUTPUT_FILE = BASE_DIR / "onsite_vs_prebuilt_wilcoxon_results.xlsx"

FILES = {
    "DSC": "dice_score_f.csv",
    "HD95": "HD95_score_f.csv",
    "MSD": "MSD_score_f.csv",
}

def formatted_p_value(p_value):
    if pd.isna(p_value):
        return ""
    if p_value < 0.001:
        return "<0.001"
    return f"{p_value:.3f}"


def calculate_wilcoxon(onsite_values, prebuilt_values):
    diff = onsite_values - prebuilt_values

    if len(diff) == 0:
        return float("nan"), float("nan")
    if int((diff != 0).sum()) == 0:
        return 0.0, 1.0

    result = wilcoxon(
        onsite_values,
        prebuilt_values,
        zero_method="wilcox",
        alternative="two-sided",
        method="auto",
    )
    return float(result.statistic), float(result.pvalue)


def merge_paired_data(onsite, prebuilt):
    patient_id_merge = onsite.merge(
        prebuilt,
        on="patient_id",
        suffixes=("_onsite", "_prebuilt"),
        how="outer",
        indicator=True,
    )

    matched_count = int((patient_id_merge["_merge"] == "both").sum())
    if matched_count > 0:
        return patient_id_merge, "patient_id"

    if len(onsite) != len(prebuilt):
        return patient_id_merge, "patient_id_no_matches"

    onsite_by_row = onsite.copy()
    prebuilt_by_row = prebuilt.copy()
    onsite_by_row["_row_order"] = range(1, len(onsite_by_row) + 1)
    prebuilt_by_row["_row_order"] = range(1, len(prebuilt_by_row) + 1)

    row_order_merge = onsite_by_row.merge(
        prebuilt_by_row,
        on="_row_order",
        suffixes=("_onsite", "_prebuilt"),
        how="outer",
        indicator=True,
    )
    return row_order_merge, "row_order"


def main():
    summary_rows = []
    test_rows = []
    merged_sheets = {}

    for metric, filename in FILES.items():
        onsite = pd.read_csv(ONSITE_DIR / filename)
        prebuilt = pd.read_csv(PREBUILT_DIR / filename)

        onsite["patient_id"] = onsite["patient_id"].astype(str)
        prebuilt["patient_id"] = prebuilt["patient_id"].astype(str)
        organs = [
            column
            for column in onsite.columns
            if column != "patient_id" and column in prebuilt.columns
        ]

        for group_name, dataframe in [("On-site", onsite), ("Pre-built", prebuilt)]:
            for organ in organs:
                values = dataframe[organ]
                summary_rows.append(
                    {
                        "Metric": metric,
                        "Group": group_name,
                        "Organ": organ,
                        "N": int(values.count()),
                        "Mean": values.mean(),
                        "SD": values.std(ddof=1),
                        "Mean_SD": f"{values.mean():.3f} +/- {values.std(ddof=1):.3f}",
                    }
                )

        merged, pairing_method = merge_paired_data(onsite, prebuilt)
        merged_sheets[metric] = merged

        unmatched = merged[merged["_merge"] != "both"]
        if not unmatched.empty and pairing_method != "row_order":
            print(f"WARNING unmatched patients in {metric}:")
            print(unmatched[["patient_id", "_merge"]].to_string(index=False))
        if pairing_method == "row_order":
            print(f"WARNING {metric}: no matching patient_id values found. Paired analysis used row order.")

        for organ in organs:
            id_columns = (
                ["patient_id"]
                if pairing_method.startswith("patient_id")
                else ["patient_id_onsite", "patient_id_prebuilt", "_row_order"]
            )
            pair = merged.loc[
                merged["_merge"] == "both",
                id_columns + [f"{organ}_onsite", f"{organ}_prebuilt"],
            ].dropna()

            onsite_values = pair[f"{organ}_onsite"]
            prebuilt_values = pair[f"{organ}_prebuilt"]
            diff = onsite_values - prebuilt_values
            statistic, p_value = calculate_wilcoxon(onsite_values, prebuilt_values)

            test_rows.append(
                {
                    "Metric": metric,
                    "Organ": organ,
                    "Pairing_method": pairing_method,
                    "N_pair": int(len(pair)),
                    "Onsite_mean": onsite_values.mean(),
                    "Onsite_SD": onsite_values.std(ddof=1),
                    "Prebuilt_mean": prebuilt_values.mean(),
                    "Prebuilt_SD": prebuilt_values.std(ddof=1),
                    "Mean_diff_Onsite_minus_Prebuilt": diff.mean(),
                    "Median_diff_Onsite_minus_Prebuilt": diff.median(),
                    "W": statistic,
                    "p_value": p_value,
                    "p_formatted": formatted_p_value(p_value),
                    "Interpretation": (
                        "On-site higher"
                        if diff.mean() > 0
                        else "On-site lower"
                        if diff.mean() < 0
                        else "No mean difference"
                    ),
                }
            )

    summary = pd.DataFrame(summary_rows)
    tests = pd.DataFrame(test_rows)

    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
            summary.to_excel(writer, sheet_name="Mean_SD_by_group", index=False)
            tests.to_excel(writer, sheet_name="Wilcoxon_onsite_vs_pre", index=False)
            for metric, merged in merged_sheets.items():
                merged.to_excel(writer, sheet_name=f"Merged_{metric}", index=False)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot overwrite {OUTPUT_FILE}. Close the Excel file if it is open, then run this script again."
        ) from exc

    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
