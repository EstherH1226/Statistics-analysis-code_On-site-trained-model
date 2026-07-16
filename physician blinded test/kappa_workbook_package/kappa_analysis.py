import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
INPUT = BASE_DIR / "Raw data_McNemar’s test.xlsx"
OUTPUT_JSON = INPUT.with_name("kappa_analysis_results.json")

RATERS = ["RO", "MP", "DR"]
QUESTIONS = [
    "Q3-1", "Q3-2", "Q3-3", "Q3-4", "Q3-5",
    "Q4-1", "Q4-2", "Q4-3", "Q4-4",
    "Q5-1", "Q5-2", "Q5-3", "Q5-4",
    "Q6-1", "Q6-2", "Q6-3", "Q6-4",
]
PATIENT_ID_COL = 6
MODEL_COL = 7
BLOCK_STARTS = {"RO": 8, "MP": 25, "DR": 42}


def cohen_kappa(a, b):
    a = np.asarray(a, dtype=int)
    b = np.asarray(b, dtype=int)
    mask = np.isin(a, [0, 1]) & np.isin(b, [0, 1])
    a = a[mask]
    b = b[mask]
    n = len(a)
    if n == 0:
        return {"n": 0, "po": None, "pe": None, "kappa": None, "n00": 0, "n01": 0, "n10": 0, "n11": 0}
    n00 = int(np.sum((a == 0) & (b == 0)))
    n01 = int(np.sum((a == 0) & (b == 1)))
    n10 = int(np.sum((a == 1) & (b == 0)))
    n11 = int(np.sum((a == 1) & (b == 1)))
    po = (n00 + n11) / n
    p_a0, p_a1 = np.mean(a == 0), np.mean(a == 1)
    p_b0, p_b1 = np.mean(b == 0), np.mean(b == 1)
    pe = p_a0 * p_b0 + p_a1 * p_b1
    kappa = 1.0 if abs(1 - pe) < 1e-12 and abs(po - 1) < 1e-12 else (po - pe) / (1 - pe)
    return {
        "n": int(n),
        "po": float(po),
        "pe": float(pe),
        "kappa": float(kappa),
        "n00": n00,
        "n01": n01,
        "n10": n10,
        "n11": n11,
    }


def fleiss_kappa(rows):
    vals = np.asarray(rows, dtype=int)
    vals = vals[np.all(np.isin(vals, [0, 1]), axis=1)]
    n_items, n_raters = vals.shape
    if n_items == 0:
        return {"n_items": 0, "kappa": None, "mean_agreement": None, "chance_agreement": None}
    counts0 = np.sum(vals == 0, axis=1)
    counts1 = np.sum(vals == 1, axis=1)
    p_i = (counts0 * (counts0 - 1) + counts1 * (counts1 - 1)) / (n_raters * (n_raters - 1))
    mean_agreement = float(np.mean(p_i))
    p0 = float(np.sum(counts0) / (n_items * n_raters))
    p1 = 1.0 - p0
    chance = p0 * p0 + p1 * p1
    kappa = 1.0 if abs(1 - chance) < 1e-12 and abs(mean_agreement - 1) < 1e-12 else (mean_agreement - chance) / (1 - chance)
    return {
        "n_items": int(n_items),
        "kappa": float(kappa),
        "mean_agreement": mean_agreement,
        "chance_agreement": float(chance),
        "p_acceptance_all_ratings": p1,
    }


def ci(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return [None, None]
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]


def build_long():
    raw = pd.read_excel(INPUT, sheet_name=0, header=None)
    data_rows = raw[
        (raw.iloc[:, MODEL_COL] == "Pre-built model")
        | (raw.iloc[:, MODEL_COL] == "On-site trained model")
    ]
    records = []
    for _, row in data_rows.iterrows():
        for q_idx, question in enumerate(QUESTIONS):
            rec = {
                "Patient ID": str(row.iloc[PATIENT_ID_COL]),
                "Patient #": str(row.iloc[PATIENT_ID_COL]),
                "Model": str(row.iloc[MODEL_COL]),
                "Question": question,
            }
            for rater, start in BLOCK_STARTS.items():
                value = row.iloc[start + q_idx]
                rec[rater] = int(float(value) > 0) if not pd.isna(value) else None
            records.append(rec)
    return pd.DataFrame(records)


def model_metrics(df):
    out = {}
    for model, sub in df.groupby("Model", sort=False):
        items = sub[RATERS].to_numpy()
        pairwise = {}
        for a, b in [("RO", "MP"), ("RO", "DR"), ("MP", "DR")]:
            pairwise[f"{a}-{b}"] = cohen_kappa(sub[a], sub[b])
        out[model] = {
            "n_patients": int(sub["Patient ID"].nunique()),
            "n_items": int(len(sub)),
            "fleiss": fleiss_kappa(items),
            "pairwise": pairwise,
            "rater_acceptance_rate": {r: float(sub[r].mean()) for r in RATERS},
            "complete_agreement_rate": float(np.mean(np.all(items == items[:, [0]], axis=1))),
            "all_accept_rate": float(np.mean(np.all(items == 1, axis=1))),
            "all_unaccept_rate": float(np.mean(np.all(items == 0, axis=1))),
            "two_vs_one_disagreement_rate": float(np.mean(~np.all(items == items[:, [0]], axis=1))),
        }
    return out


def question_metrics(df):
    rows = []
    for model, by_model in df.groupby("Model", sort=False):
        for q, sub in by_model.groupby("Question", sort=False):
            fk = fleiss_kappa(sub[RATERS].to_numpy())
            entry = {
                "Model": model,
                "Question": q,
                "n_items": int(len(sub)),
                "Fleiss kappa": fk["kappa"],
                "Observed agreement": fk["mean_agreement"],
                "Acceptance all ratings": fk["p_acceptance_all_ratings"],
            }
            for a, b in [("RO", "MP"), ("RO", "DR"), ("MP", "DR")]:
                entry[f"{a}-{b} kappa"] = cohen_kappa(sub[a], sub[b])["kappa"]
            rows.append(entry)
    return rows


def bootstrap(df, n_boot=5000, seed=20260505):
    rng = np.random.default_rng(seed)
    patients = sorted(df["Patient ID"].unique())
    stats = {model: {"fleiss": [], "pair_mean": [], "RO-MP": [], "RO-DR": [], "MP-DR": []} for model in df["Model"].unique()}
    diffs = {"fleiss": [], "pair_mean": [], "RO-MP": [], "RO-DR": [], "MP-DR": []}
    for _ in range(n_boot):
        sampled = rng.choice(patients, size=len(patients), replace=True)
        boot = pd.concat([df[df["Patient ID"] == pid] for pid in sampled], ignore_index=True)
        metrics = model_metrics(boot)
        for model, m in metrics.items():
            stats[model]["fleiss"].append(m["fleiss"]["kappa"])
            pair_vals = []
            for pair, pm in m["pairwise"].items():
                stats[model][pair].append(pm["kappa"])
                pair_vals.append(pm["kappa"])
            stats[model]["pair_mean"].append(float(np.mean(pair_vals)))
        if "Pre-built model" in metrics and "On-site trained model" in metrics:
            pre = metrics["Pre-built model"]
            on = metrics["On-site trained model"]
            diffs["fleiss"].append(on["fleiss"]["kappa"] - pre["fleiss"]["kappa"])
            diffs["pair_mean"].append(
                np.mean([v["kappa"] for v in on["pairwise"].values()])
                - np.mean([v["kappa"] for v in pre["pairwise"].values()])
            )
            for pair in ["RO-MP", "RO-DR", "MP-DR"]:
                diffs[pair].append(on["pairwise"][pair]["kappa"] - pre["pairwise"][pair]["kappa"])
    return {
        "ci": {model: {name: ci(vals) for name, vals in stat.items()} for model, stat in stats.items()},
        "diff_ci": {name: ci(vals) for name, vals in diffs.items()},
        "diff_prob_gt_0": {name: float(np.mean(np.asarray(vals) > 0)) for name, vals in diffs.items()},
        "n_boot": n_boot,
        "seed": seed,
    }


def main():
    long_df = build_long()
    metrics = model_metrics(long_df)
    boot = bootstrap(long_df)

    model_order = ["Pre-built model", "On-site trained model"]
    differences = {}
    for key in ["fleiss", "pair_mean", "RO-MP", "RO-DR", "MP-DR"]:
        if key == "fleiss":
            pre = metrics[model_order[0]]["fleiss"]["kappa"]
            on = metrics[model_order[1]]["fleiss"]["kappa"]
        elif key == "pair_mean":
            pre = np.mean([v["kappa"] for v in metrics[model_order[0]]["pairwise"].values()])
            on = np.mean([v["kappa"] for v in metrics[model_order[1]]["pairwise"].values()])
        else:
            pre = metrics[model_order[0]]["pairwise"][key]["kappa"]
            on = metrics[model_order[1]]["pairwise"][key]["kappa"]
        differences[key] = {
            "pre_built": float(pre),
            "on_site": float(on),
            "difference_on_site_minus_pre": float(on - pre),
            "bootstrap_ci": boot["diff_ci"][key],
            "bootstrap_prob_difference_gt_0": boot["diff_prob_gt_0"][key],
        }

    result = {
        "input": str(INPUT),
        "n_bootstrap": boot["n_boot"],
        "bootstrap_seed": boot["seed"],
        "models": metrics,
        "bootstrap_ci": boot["ci"],
        "differences": differences,
        "question_metrics": question_metrics(long_df),
        "long_data_preview": long_df.head(12).to_dict(orient="records"),
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUTPUT_JSON))


if __name__ == "__main__":
    main()
