import math
from collections import Counter
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "Raw data_McNemar’s test.xlsx"

QUESTION_OUTPUT = BASE_DIR / "McNemar_patient_level_results.csv"
TOTAL_DETAIL_OUTPUT = BASE_DIR / "Patient_level_total_scores.csv"
SUBQUESTION_OUTPUT = BASE_DIR / "McNemar_subquestion_patient_level_results.csv"
SUBQUESTION_DETAIL_OUTPUT = BASE_DIR / "Patient_level_subquestion_scores.csv"

MODEL_COL = 7
PATIENT_ID_COL = 6
FIRST_SCORE_COL = 8
LAST_SCORE_COL = 58
HEADER_ROW = 2

QUESTION_MAP = {
    "Q3": "Q3",
    "Q4": "Q4",
    "Q5": "Q5",
    "Q6": "Q6",
}


def mcnemar_exact_p(pre_only, onsite_only):
    """Two-sided exact McNemar p-value using the binomial distribution."""
    n = pre_only + onsite_only
    if n == 0:
        return 1.0

    k = min(pre_only, onsite_only)
    lower_tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2 * lower_tail)


def average_ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0

    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1

        average_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = average_rank
        i = j + 1

    return ranks


def wilcoxon_signed_rank_exact_p(differences):
    """Two-sided exact Wilcoxon signed-rank p-value for paired differences."""
    nonzero = [float(d) for d in differences if abs(float(d)) > 1e-12]
    if not nonzero:
        return 1.0, 0.0, 0.0, 0

    ranks = average_ranks([abs(d) for d in nonzero])

    # Average ranks can be half-integers when ties occur. Scale by 2 so the
    # dynamic-programming exact distribution can use integer sums.
    scale = 2
    integer_ranks = [int(round(r * scale)) for r in ranks]
    w_plus = sum(r for r, d in zip(integer_ranks, nonzero) if d > 0)
    total_rank_sum = sum(integer_ranks)
    observed_deviation = abs(w_plus - total_rank_sum / 2)

    counts = Counter({0: 1})
    for rank in integer_ranks:
        next_counts = Counter()
        for rank_sum, count in counts.items():
            next_counts[rank_sum] += count
            next_counts[rank_sum + rank] += count
        counts = next_counts

    extreme_count = sum(
        count
        for rank_sum, count in counts.items()
        if abs(rank_sum - total_rank_sum / 2) >= observed_deviation - 1e-12
    )
    p_value = min(1.0, extreme_count / (2 ** len(integer_ranks)))

    return (
        p_value,
        w_plus / scale,
        min(w_plus, total_rank_sum - w_plus) / scale,
        len(nonzero),
    )


def sum_scores(row, columns):
    return float(pd.to_numeric(row.loc[columns], errors="coerce").fillna(0).sum())


def make_summary_row(pre, onsite, label, excel_label, columns):
    both_correct = 0
    pre_only = 0
    onsite_only = 0
    both_incorrect = 0
    pre_scores = []
    onsite_scores = []
    differences = []

    for patient_id in pre.index:
        pre_score = sum_scores(pre.loc[patient_id], columns)
        onsite_score = sum_scores(onsite.loc[patient_id], columns)

        pre_scores.append(pre_score)
        onsite_scores.append(onsite_score)
        differences.append(onsite_score - pre_score)

        pre_correct = pre_score > 0
        onsite_correct = onsite_score > 0

        if pre_correct and onsite_correct:
            both_correct += 1
        elif pre_correct and not onsite_correct:
            pre_only += 1
        elif not pre_correct and onsite_correct:
            onsite_only += 1
        else:
            both_incorrect += 1

    n = both_correct + pre_only + onsite_only + both_incorrect
    wilcoxon_p, w_plus, w_statistic, wilcoxon_n = wilcoxon_signed_rank_exact_p(
        differences
    )

    return {
        "actual_question": label,
        "excel_question": excel_label,
        "n_patients": n,
        "both_correct": both_correct,
        "pre_built_only_correct": pre_only,
        "on_site_only_correct": onsite_only,
        "both_incorrect": both_incorrect,
        "discordant_pairs": pre_only + onsite_only,
        "pre_built_correct_rate": (both_correct + pre_only) / n,
        "on_site_correct_rate": (both_correct + onsite_only) / n,
        "difference_on_site_minus_pre_built_binary": (onsite_only - pre_only) / n,
        "mcnemar_exact_p_value": mcnemar_exact_p(pre_only, onsite_only),
        "pre_built_mean_score": sum(pre_scores) / n,
        "on_site_mean_score": sum(onsite_scores) / n,
        "mean_score_difference_on_site_minus_pre_built": sum(differences) / n,
        "wilcoxon_signed_rank_p_value": wilcoxon_p,
        "wilcoxon_w_plus": w_plus,
        "wilcoxon_statistic_min_rank_sum": w_statistic,
        "wilcoxon_n_nonzero_differences": wilcoxon_n,
        "test_note": (
            "McNemar p-value uses patient-level binary score >0. "
            "Wilcoxon signed-rank p-value uses patient-level summed score "
            "differences, excluding zero differences."
        ),
    }


def load_data():
    df = pd.read_excel(INPUT_FILE, sheet_name=0, header=None)
    headers = df.iloc[HEADER_ROW].to_list()
    model_rows = df[df[MODEL_COL].isin(["Pre-built model", "On-site trained model"])]

    pre = model_rows[model_rows[MODEL_COL] == "Pre-built model"].set_index(
        PATIENT_ID_COL
    )
    onsite = model_rows[model_rows[MODEL_COL] == "On-site trained model"].set_index(
        PATIENT_ID_COL
    )

    if pre.index.to_list() != onsite.index.to_list():
        raise ValueError("Patient IDs are not paired in the same order.")

    return headers, pre, onsite


def question_columns(headers):
    return {
        question: [
            col
            for col, header in enumerate(headers)
            if isinstance(header, str)
            and header.startswith(question + "-")
            and FIRST_SCORE_COL <= col <= LAST_SCORE_COL
        ]
        for question in QUESTION_MAP
    }


def subquestion_columns(headers):
    grouped = {}
    for col, header in enumerate(headers):
        if (
            FIRST_SCORE_COL <= col <= LAST_SCORE_COL
            and isinstance(header, str)
            and header.startswith("Q")
            and "-" in header
        ):
            grouped.setdefault(header, []).append(col)

    return dict(
        sorted(
            grouped.items(),
            key=lambda item: (
                int(item[0].split("-")[0][1:]),
                int(item[0].split("-")[1]),
            ),
        )
    )


def write_question_results(pre, onsite, qcols):
    rows = []

    for excel_question, columns in qcols.items():
        rows.append(
            make_summary_row(
                pre,
                onsite,
                label=QUESTION_MAP[excel_question],
                excel_label=excel_question,
                columns=columns,
            )
        )

    all_columns = [col for columns in qcols.values() for col in columns]
    rows.append(
        make_summary_row(
            pre,
            onsite,
            label="Total score",
            excel_label="Q1-Q4 total",
            columns=all_columns,
        )
    )

    pd.DataFrame(rows).to_csv(QUESTION_OUTPUT, index=False, encoding="utf-8-sig")

    detail_rows = []
    for patient_id in pre.index:
        pre_score = sum_scores(pre.loc[patient_id], all_columns)
        onsite_score = sum_scores(onsite.loc[patient_id], all_columns)
        detail_rows.append(
            {
                "patient_id": patient_id,
                "pre_built_total_score": pre_score,
                "on_site_total_score": onsite_score,
                "difference_on_site_minus_pre_built": onsite_score - pre_score,
            }
        )

    pd.DataFrame(detail_rows).to_csv(
        TOTAL_DETAIL_OUTPUT, index=False, encoding="utf-8-sig"
    )


def write_subquestion_results(pre, onsite, subqcols):
    rows = []
    detail_rows = []

    for excel_subquestion, columns in subqcols.items():
        excel_question, subquestion_number = excel_subquestion.split("-")
        actual_question = QUESTION_MAP[excel_question]
        actual_subquestion = f"{actual_question}-{subquestion_number}"

        row = make_summary_row(
            pre,
            onsite,
            label=actual_question,
            excel_label=excel_question,
            columns=columns,
        )
        row["actual_subquestion"] = actual_subquestion
        row["excel_subquestion"] = excel_subquestion
        row["n_observers_collapsed_per_patient"] = len(columns)
        row["test_note"] = (
            "Patient-level subquestion analysis. RO/MP/DR scores for each "
            "subquestion were summed per patient; McNemar uses binary score >0 "
            "and Wilcoxon uses summed score differences."
        )
        rows.append(row)

        for patient_id in pre.index:
            pre_score = sum_scores(pre.loc[patient_id], columns)
            onsite_score = sum_scores(onsite.loc[patient_id], columns)
            detail_rows.append(
                {
                    "patient_id": patient_id,
                    "actual_subquestion": actual_subquestion,
                    "excel_subquestion": excel_subquestion,
                    "pre_built_score": pre_score,
                    "on_site_score": onsite_score,
                    "difference_on_site_minus_pre_built": onsite_score - pre_score,
                    "pre_built_correct": pre_score > 0,
                    "on_site_correct": onsite_score > 0,
                }
            )

    column_order = [
        "actual_question",
        "actual_subquestion",
        "excel_question",
        "excel_subquestion",
        "n_patients",
        "n_observers_collapsed_per_patient",
        "both_correct",
        "pre_built_only_correct",
        "on_site_only_correct",
        "both_incorrect",
        "discordant_pairs",
        "pre_built_correct_rate",
        "on_site_correct_rate",
        "difference_on_site_minus_pre_built_binary",
        "mcnemar_exact_p_value",
        "pre_built_mean_score",
        "on_site_mean_score",
        "mean_score_difference_on_site_minus_pre_built",
        "wilcoxon_signed_rank_p_value",
        "wilcoxon_w_plus",
        "wilcoxon_statistic_min_rank_sum",
        "wilcoxon_n_nonzero_differences",
        "test_note",
    ]
    pd.DataFrame(rows)[column_order].to_csv(
        SUBQUESTION_OUTPUT, index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(detail_rows).to_csv(
        SUBQUESTION_DETAIL_OUTPUT, index=False, encoding="utf-8-sig"
    )


def main():
    headers, pre, onsite = load_data()
    qcols = question_columns(headers)
    subqcols = subquestion_columns(headers)

    write_question_results(pre, onsite, qcols)
    write_subquestion_results(pre, onsite, subqcols)

    print(f"Saved: {QUESTION_OUTPUT}")
    print(f"Saved: {TOTAL_DETAIL_OUTPUT}")
    print(f"Saved: {SUBQUESTION_OUTPUT}")
    print(f"Saved: {SUBQUESTION_DETAIL_OUTPUT}")


if __name__ == "__main__":
    main()
