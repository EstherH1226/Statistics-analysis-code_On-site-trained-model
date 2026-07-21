import json
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
INPUT_XLSX = BASE / "Raw data_McNemar’s test.xlsx"
RESULT_JSON = BASE / "kappa_analysis_results.json"
OUTPUT_PNG = BASE / "kappa_agreement_acceptance_figure.png"
OUTPUT_PDF = BASE / "kappa_agreement_acceptance_figure.pdf"
OUTPUT_MODEL_SUMMARY_PNG = BASE / "kappa_model_summary.png"
OUTPUT_MODEL_SUMMARY_PDF = BASE / "kappa_model_summary.pdf"
OUTPUT_MODEL_SUMMARY_TIFF = BASE / "kappa_model_summary.tiff"
OUTPUT_PANEL_A_PNG = BASE / "kappa_panel_A_fleiss_kappa.png"
OUTPUT_PANEL_A_PDF = BASE / "kappa_panel_A_fleiss_kappa.pdf"
OUTPUT_PANEL_A_TIFF = BASE / "kappa_panel_A_fleiss_kappa.tiff"
OUTPUT_PANEL_B_PNG = BASE / "kappa_panel_B_observed_agreement.png"
OUTPUT_PANEL_B_PDF = BASE / "kappa_panel_B_observed_agreement.pdf"
OUTPUT_PANEL_B_TIFF = BASE / "kappa_panel_B_observed_agreement.tiff"
OUTPUT_PANEL_C_PNG = BASE / "kappa_panel_C_all_3_accepted.png"
OUTPUT_PANEL_C_PDF = BASE / "kappa_panel_C_all_3_accepted.pdf"
OUTPUT_PANEL_C_TIFF = BASE / "kappa_panel_C_all_3_accepted.tiff"

RATERS = ["RO", "MP", "DR"]
QUESTIONS = [
    "Q3-1", "Q3-2", "Q3-3", "Q3-4", "Q3-5",
    "Q4-1", "Q4-2", "Q4-3", "Q4-4",
    "Q5-1", "Q5-2", "Q5-3", "Q5-4",
    "Q6-1", "Q6-2", "Q6-3", "Q6-4",
]
DISPLAY_QUESTIONS = QUESTIONS
PATIENT_ID_COL = 6
MODEL_COL = 7
BLOCK_STARTS = {"RO": 8, "MP": 25, "DR": 42}
MODELS = ["Pre-built model", "On-site trained model"]


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\malgunbd.ttf" if bold else r"C:\Windows\Fonts\malgun.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


F_TITLE = font(44, True)
F_SUBTITLE = font(23)
F_PANEL = font(28, True)
F_HEADER = font(22, True)
F_LABEL = font(20)
F_SMALL = font(17)
F_CELL = font(18, True)
F_NOTE = font(19)


def lerp(a, b, t):
    return int(a + (b - a) * t)


def blend(c1, c2, t):
    return tuple(lerp(c1[i], c2[i], t) for i in range(3))


def kappa_color(v):
    v = max(-0.2, min(1.0, float(v)))
    stops = [
        (-0.2, (183, 28, 28)),
        (0.0, (244, 196, 191)),
        (0.2, (248, 213, 126)),
        (0.4, (190, 220, 140)),
        (0.6, (89, 169, 112)),
        (1.0, (27, 94, 32)),
    ]
    for (x0, c0), (x1, c1) in zip(stops, stops[1:]):
        if v <= x1:
            return blend(c0, c1, (v - x0) / (x1 - x0))
    return stops[-1][1]


def rate_color(v):
    v = max(0.0, min(1.0, float(v)))
    stops = [
        (0.0, (247, 251, 255)),
        (0.5, (116, 169, 207)),
        (1.0, (8, 81, 156)),
    ]
    for (x0, c0), (x1, c1) in zip(stops, stops[1:]):
        if v <= x1:
            return blend(c0, c1, (v - x0) / (x1 - x0))
    return stops[-1][1]


def kappa_category(v):
    v = float(v)
    if v < 0:
        return "Poor"
    if v <= 0.20:
        return "Slight"
    if v <= 0.40:
        return "Fair"
    if v <= 0.60:
        return "Moderate"
    if v <= 0.80:
        return "Substantial"
    return "Almost perfect"


CATEGORY_COLORS = {
    "Poor": (196, 75, 75),
    "Slight": (238, 184, 164),
    "Fair": (239, 210, 127),
    "Moderate": (151, 198, 124),
    "Substantial": (74, 151, 93),
    "Almost perfect": (26, 111, 46),
}


def text_center(draw, box, text, fill, fnt):
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0, 0), text, font=fnt)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - h) / 2 - 1), text, fill=fill, font=fnt)


def draw_round_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def wrapped_text(draw, xy, text, fnt, fill, max_width, line_gap=5):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, fill=fill, font=fnt)
        y += fnt.size + line_gap
    return y


def build_long():
    raw = pd.read_excel(INPUT_XLSX, sheet_name=0, header=None)
    data_rows = raw[
        (raw.iloc[:, MODEL_COL] == "Pre-built model")
        | (raw.iloc[:, MODEL_COL] == "On-site trained model")
    ]
    records = []
    for _, row in data_rows.iterrows():
        for q_idx, question in enumerate(QUESTIONS):
            rec = {
                "Patient ID": str(row.iloc[PATIENT_ID_COL]),
                "Model": str(row.iloc[MODEL_COL]),
                "Question": question,
            }
            for rater, start in BLOCK_STARTS.items():
                rec[rater] = int(float(row.iloc[start + q_idx]) > 0)
            records.append(rec)
    return pd.DataFrame(records)


def draw_heatmap(draw, x, y, title, data, color_fn, value_fmt, legend_labels):
    cell_w = 165
    cell_h = 38
    left_w = 76
    header_h = 42
    title_h = 38
    total_w = left_w + 2 * cell_w
    total_h = title_h + header_h + len(QUESTIONS) * cell_h + 54

    draw_round_rect(draw, (x, y, x + total_w, y + total_h), 8, (255, 255, 255), (214, 222, 230), 1)
    draw.text((x + 12, y + 8), title, fill=(31, 78, 121), font=F_PANEL)
    hy = y + title_h
    text_center(draw, (x + left_w, hy, x + left_w + cell_w, hy + header_h), "Pre-built", (28, 48, 68), F_HEADER)
    text_center(draw, (x + left_w + cell_w, hy, x + left_w + 2 * cell_w, hy + header_h), "On-site", (28, 48, 68), F_HEADER)
    draw.line((x + 10, hy + header_h, x + total_w - 10, hy + header_h), fill=(210, 218, 226), width=1)

    for i, q in enumerate(QUESTIONS):
        q_label = DISPLAY_QUESTIONS[i]
        cy = hy + header_h + i * cell_h
        draw.text((x + 14, cy + 9), q_label, fill=(50, 62, 72), font=F_LABEL)
        for j, model in enumerate(MODELS):
            val = data[model][q]
            cx = x + left_w + j * cell_w
            fill = color_fn(val)
            draw.rectangle((cx, cy, cx + cell_w, cy + cell_h), fill=fill, outline=(255, 255, 255), width=2)
            brightness = 0.299 * fill[0] + 0.587 * fill[1] + 0.114 * fill[2]
            txt_fill = (255, 255, 255) if brightness < 125 else (25, 35, 45)
            text_center(draw, (cx, cy, cx + cell_w, cy + cell_h), value_fmt(val), txt_fill, F_CELL)

    # Compact legend.
    ly = y + total_h - 38
    lx = x + 14
    draw.text((lx, ly + 4), legend_labels[0], fill=(68, 78, 88), font=F_SMALL)
    grad_x = lx + 78
    grad_w = 190
    for k in range(grad_w):
        t = k / (grad_w - 1)
        sample = -0.2 + t * 1.2 if color_fn is kappa_color else t
        draw.line((grad_x + k, ly, grad_x + k, ly + 18), fill=color_fn(sample))
    draw.rectangle((grad_x, ly, grad_x + grad_w, ly + 18), outline=(180, 190, 200), width=1)
    draw.text((grad_x + grad_w + 8, ly + 4), legend_labels[1], fill=(68, 78, 88), font=F_SMALL)


def draw_category_heatmap(draw, x, y, title, data):
    cell_w = 165
    cell_h = 38
    left_w = 76
    header_h = 42
    title_h = 38
    total_w = left_w + 2 * cell_w
    total_h = title_h + header_h + len(QUESTIONS) * cell_h + 134

    draw_round_rect(draw, (x, y, x + total_w, y + total_h), 8, (255, 255, 255), (214, 222, 230), 1)
    draw.text((x + 12, y + 8), title, fill=(31, 78, 121), font=F_PANEL)
    hy = y + title_h
    text_center(draw, (x + left_w, hy, x + left_w + cell_w, hy + header_h), "Pre-built", (28, 48, 68), F_HEADER)
    text_center(draw, (x + left_w + cell_w, hy, x + left_w + 2 * cell_w, hy + header_h), "On-site", (28, 48, 68), F_HEADER)
    draw.line((x + 10, hy + header_h, x + total_w - 10, hy + header_h), fill=(210, 218, 226), width=1)

    for i, q in enumerate(QUESTIONS):
        q_label = DISPLAY_QUESTIONS[i]
        cy = hy + header_h + i * cell_h
        draw.text((x + 14, cy + 9), q_label, fill=(50, 62, 72), font=F_LABEL)
        for j, model in enumerate(MODELS):
            val = data[model][q]
            cat = kappa_category(val)
            fill = CATEGORY_COLORS[cat]
            cx = x + left_w + j * cell_w
            draw.rectangle((cx, cy, cx + cell_w, cy + cell_h), fill=fill, outline=(255, 255, 255), width=2)
            brightness = 0.299 * fill[0] + 0.587 * fill[1] + 0.114 * fill[2]
            txt_fill = (255, 255, 255) if brightness < 125 else (25, 35, 45)
            text_center(draw, (cx, cy, cx + cell_w, cy + cell_h), cat, txt_fill, F_SMALL)

    legend_y = y + total_h - 92
    legend_x = x + 14
    legend_items = ["Poor", "Slight", "Fair", "Moderate", "Substantial", "Almost perfect"]
    for idx, item in enumerate(legend_items):
        lx = legend_x + (idx % 2) * 198
        ly = legend_y + (idx // 2) * 28
        draw.rectangle((lx, ly, lx + 20, ly + 20), fill=CATEGORY_COLORS[item], outline=(180, 190, 200))
        draw.text((lx + 28, ly + 1), item, fill=(68, 78, 88), font=F_SMALL)


def save_category_panel(output_png, output_pdf, output_tiff, data):
    img = Image.new("RGBA", (720, 1060), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((55, 34), "B. Kappa category", fill=(20, 44, 66), font=F_TITLE)
    wrapped_text(
        draw,
        (55, 89),
        "Landis-Koch descriptive categories for chance-corrected agreement.",
        F_SUBTITLE,
        (78, 90, 102),
        610,
    )
    draw_category_heatmap(draw, 120, 155, "Kappa category", data)
    img.save(output_png, dpi=(300, 300))
    img.convert("RGB").save(output_pdf, "PDF", resolution=300)
    img.save(output_tiff, "TIFF", dpi=(300, 300), compression="tiff_lzw")


def draw_model_summary(draw, x0, y0, x1, y1, result):
    draw_round_rect(draw, (x0, y0, x1, y1), 10, (255, 255, 255), (214, 222, 230), 1)
    draw.text((x0 + 22, y0 + 18), "Model-level summary", fill=(31, 78, 121), font=F_PANEL)

    bar_origin_x = x0 + 390
    max_bar_w = 380
    rows_y = [y0 + 82, y0 + 144]
    for idx, model in enumerate(MODELS):
        m = result["models"][model]
        fleiss = m["fleiss"]["kappa"]
        obs = m["fleiss"]["mean_agreement"]
        all_acc = m["all_accept_rate"]
        row_y = rows_y[idx]
        label = "Pre-built" if idx == 0 else "On-site trained"
        draw.text((x0 + 28, row_y + 7), label, fill=(35, 45, 55), font=F_HEADER)
        bw = int(max(0, fleiss) * max_bar_w)
        draw.rectangle((bar_origin_x, row_y, bar_origin_x + max_bar_w, row_y + 24), fill=(230, 236, 242))
        draw.rectangle((bar_origin_x, row_y, bar_origin_x + bw, row_y + 24), fill=kappa_color(fleiss))
        kappa_text_x = bar_origin_x + max_bar_w + 18
        draw.text((kappa_text_x, row_y - 2), f"Fleiss kappa {fleiss:.3f}", fill=(35, 45, 55), font=F_LABEL)
        tag_x = x0 + 1065
        tag_w = 230
        draw_round_rect(draw, (tag_x, row_y - 4, tag_x + tag_w, row_y + 32), 18, (232, 243, 253), None)
        text_center(draw, (tag_x, row_y - 4, tag_x + tag_w, row_y + 32), f"Observed {obs:.3f}", (20, 75, 120), F_LABEL)
        tag2_x = x0 + 1330
        tag2_w = 245
        draw_round_rect(draw, (tag2_x, row_y - 4, tag2_x + tag2_w, row_y + 32), 18, (232, 245, 237), None)
        text_center(draw, (tag2_x, row_y - 4, tag2_x + tag2_w, row_y + 32), f"All accepted {all_acc:.3f}", (38, 97, 57), F_LABEL)

    note = (
        "Key read: Pre-built has higher chance-corrected agreement, while On-site trained shows stronger consensus "
        "toward acceptance."
    )
    wrapped_text(draw, (x0 + 28, y0 + 198), note, F_NOTE, (70, 80, 90), 980)


def save_panel_a(result):
    img = Image.new("RGBA", (1800, 420), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((70, 42), "Model-level inter-rater agreement summary", fill=(20, 44, 66), font=F_TITLE)
    draw_model_summary(draw, 70, 125, 1730, 365, result)
    img.save(OUTPUT_MODEL_SUMMARY_PNG, dpi=(300, 300))
    img.convert("RGB").save(OUTPUT_MODEL_SUMMARY_PDF, "PDF", resolution=300)
    img.save(OUTPUT_MODEL_SUMMARY_TIFF, "TIFF", dpi=(300, 300), compression="tiff_lzw")


def save_heatmap_panel(output_png, output_pdf, output_tiff, title, subtitle, data, color_fn, value_fmt, legend_labels):
    img = Image.new("RGBA", (720, 980), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((55, 34), title, fill=(20, 44, 66), font=F_TITLE)
    wrapped_text(draw, (55, 89), subtitle, F_SUBTITLE, (78, 90, 102), 610)
    draw_heatmap(draw, 120, 155, title.replace("Question-level ", ""), data, color_fn, value_fmt, legend_labels)
    img.save(output_png, dpi=(300, 300))
    img.convert("RGB").save(output_pdf, "PDF", resolution=300)
    img.save(output_tiff, "TIFF", dpi=(300, 300), compression="tiff_lzw")


def response_patterns(long_df):
    patterns = {m: {} for m in MODELS}
    for model in MODELS:
        for q in QUESTIONS:
            sub = long_df[(long_df["Model"] == model) & (long_df["Question"] == q)]
            vals = sub[RATERS]
            all_accept = float(((vals == 1).all(axis=1)).mean())
            all_unaccept = float(((vals == 0).all(axis=1)).mean())
            disagree = float(1.0 - all_accept - all_unaccept)
            patterns[model][q] = {
                "3 accept": all_accept,
                "3 unaccept": all_unaccept,
                "2:1 disagreement": disagree,
            }
    return patterns


def save_response_pattern_panel(output_png, output_pdf, output_tiff, patterns):
    img = Image.new("RGBA", (980, 1300), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((55, 34), "C. Observer response pattern", fill=(20, 44, 66), font=F_TITLE)
    wrapped_text(
        draw,
        (55, 89),
        "Distribution of unanimous acceptance, unanimous unacceptance, and 2:1 observer disagreement.",
        F_SUBTITLE,
        (78, 90, 102),
        850,
    )

    x, y = 55, 155
    w, h = 870, 1080
    draw_round_rect(draw, (x, y, x + w, y + h), 8, (255, 255, 255), (214, 222, 230), 1)
    draw.text((x + 16, y + 12), "Response pattern by question", fill=(31, 78, 121), font=F_PANEL)

    colors = {
        "3 accept": (42, 126, 88),
        "3 unaccept": (96, 117, 138),
        "2:1 disagreement": (224, 151, 64),
    }
    bar_x = x + 180
    bar_w = 610
    row_h = 50
    top = y + 70
    sub_h = 18
    for i, q in enumerate(QUESTIONS):
        q_label = DISPLAY_QUESTIONS[i]
        row_y = top + i * row_h
        draw.text((x + 22, row_y + 14), q_label, fill=(50, 62, 72), font=F_LABEL)
        for model_idx, model in enumerate(MODELS):
            by = row_y + 5 + model_idx * 22
            label = "Pre" if model_idx == 0 else "On"
            draw.text((bar_x - 42, by - 2), label, fill=(70, 82, 94), font=F_SMALL)
            cursor = bar_x
            for key in ["3 accept", "3 unaccept", "2:1 disagreement"]:
                seg_w = int(round(patterns[model][q][key] * bar_w))
                if seg_w > 0:
                    draw.rectangle((cursor, by, cursor + seg_w, by + sub_h), fill=colors[key])
                cursor += seg_w
            draw.rectangle((bar_x, by, bar_x + bar_w, by + sub_h), outline=(220, 226, 232), width=1)

    axis_y = top + len(QUESTIONS) * row_h + 6
    for pct in [0, 0.25, 0.5, 0.75, 1.0]:
        tx = bar_x + int(pct * bar_w)
        draw.line((tx, axis_y, tx, axis_y + 7), fill=(120, 132, 144), width=1)
        label = f"{int(pct * 100)}%"
        text_center(draw, (tx - 30, axis_y + 9, tx + 30, axis_y + 31), label, (70, 82, 94), F_SMALL)

    legend_y = y + h - 52
    legend_x = x + 22
    for item in ["3 accept", "3 unaccept", "2:1 disagreement"]:
        draw.rectangle((legend_x, legend_y, legend_x + 22, legend_y + 22), fill=colors[item])
        draw.text((legend_x + 30, legend_y + 1), item, fill=(55, 66, 76), font=F_SMALL)
        legend_x += 220

    img.save(output_png, dpi=(300, 300))
    img.convert("RGB").save(output_pdf, "PDF", resolution=300)
    img.save(output_tiff, "TIFF", dpi=(300, 300), compression="tiff_lzw")


def main():
    result = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
    long_df = build_long()

    q_metrics = pd.DataFrame(result["question_metrics"])
    kappas = {m: {} for m in MODELS}
    observed = {m: {} for m in MODELS}
    accept_all = {m: {} for m in MODELS}
    for _, row in q_metrics.iterrows():
        kappas[row["Model"]][row["Question"]] = row["Fleiss kappa"]
        observed[row["Model"]][row["Question"]] = row["Observed agreement"]
    for model in MODELS:
        for q in QUESTIONS:
            sub = long_df[(long_df["Model"] == model) & (long_df["Question"] == q)]
            vals = sub[RATERS]
            accept_all[model][q] = float(((vals == 1).all(axis=1)).mean())

    W, H = 1800, 1450
    img = Image.new("RGB", (W, H), (246, 248, 250))
    draw = ImageDraw.Draw(img)

    draw.text((70, 44), "Inter-rater agreement and acceptance pattern", fill=(20, 44, 66), font=F_TITLE)
    draw.text(
        (70, 101),
        "Each question summarizes 30 patients. Kappa is chance-corrected; observed agreement and all-acceptance show consensus direction.",
        fill=(78, 90, 102),
        font=F_SUBTITLE,
    )

    # Panel A: model-level summary.
    draw_model_summary(draw, 70, 170, 1730, 410, result)

    draw_heatmap(draw, 70, 470, "B. Fleiss' kappa", kappas, kappa_color, lambda v: f"{v:.2f}", ("low", "high"))
    draw_heatmap(draw, 650, 470, "C. Observed agreement", observed, rate_color, lambda v: f"{v:.2f}", ("0", "1"))
    draw_heatmap(draw, 1230, 470, "D. All 3 accepted", accept_all, rate_color, lambda v: f"{v:.2f}", ("0", "1"))

    # Bottom interpretation strip.
    bx0, by0, bx1, by1 = 70, 1300, 1730, 1400
    draw_round_rect(draw, (bx0, by0, bx1, by1), 10, (255, 255, 255), (214, 222, 230), 1)
    draw.text((bx0 + 22, by0 + 18), "Interpretation", fill=(31, 78, 121), font=F_PANEL)
    text = (
        "High observed agreement plus high all-acceptance is meaningful consensus that observers found the structure acceptable. "
        "Low kappa in those cells should be read as a prevalence effect, not simply poor observer reliability."
    )
    wrapped_text(draw, (bx0 + 240, by0 + 23), text, F_NOTE, (55, 66, 76), 1350)

    img.save(OUTPUT_PNG, dpi=(300, 300))
    img.save(OUTPUT_PDF, "PDF", resolution=300)
    save_panel_a(result)
    save_heatmap_panel(
        OUTPUT_PANEL_A_PNG,
        OUTPUT_PANEL_A_PDF,
        OUTPUT_PANEL_A_TIFF,
        "A. Fleiss' kappa",
        "Chance-corrected agreement among RO, MP, and DR.",
        kappas,
        kappa_color,
        lambda v: f"{v:.2f}",
        ("low", "high"),
    )
    save_heatmap_panel(
        OUTPUT_PANEL_B_PNG,
        OUTPUT_PANEL_B_PDF,
        OUTPUT_PANEL_B_TIFF,
        "B. Observed agreement",
        "Crude agreement among the three observers, without chance correction.",
        observed,
        rate_color,
        lambda v: f"{v:.2f}",
        ("0", "1"),
    )
    save_heatmap_panel(
        OUTPUT_PANEL_C_PNG,
        OUTPUT_PANEL_C_PDF,
        OUTPUT_PANEL_C_TIFF,
        "C. All 3 accepted",
        "Proportion of patients for whom all three observers rated the structure as acceptable.",
        accept_all,
        rate_color,
        lambda v: f"{v:.2f}",
        ("0", "1"),
    )
    print(OUTPUT_PNG)
    print(OUTPUT_PDF)
    print(OUTPUT_MODEL_SUMMARY_PNG)
    print(OUTPUT_MODEL_SUMMARY_PDF)
    print(OUTPUT_MODEL_SUMMARY_TIFF)
    print(OUTPUT_PANEL_A_PNG)
    print(OUTPUT_PANEL_A_PDF)
    print(OUTPUT_PANEL_A_TIFF)
    print(OUTPUT_PANEL_B_PNG)
    print(OUTPUT_PANEL_B_PDF)
    print(OUTPUT_PANEL_B_TIFF)
    print(OUTPUT_PANEL_C_PNG)
    print(OUTPUT_PANEL_C_PDF)
    print(OUTPUT_PANEL_C_TIFF)


if __name__ == "__main__":
    main()
