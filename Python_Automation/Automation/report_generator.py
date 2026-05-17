"""
report_generator.py
====================
Takes scraped data and produces:
  - notes.csv
  - flashcards.csv
  - quizzes.csv
  - study_hub_report.pdf  (tables + bar chart)
"""

import csv
import json
import os
from pathlib import Path
from datetime import datetime

# ── PDF & Chart imports ───────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, Image, HRFlowable)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

OUTPUT_DIR = Path("study_hub_output")


# ── CSV Exporters ─────────────────────────────────────────────────────────────

def save_csv(records: list, filename: str):
    if not records:
        print(f"  ⚠️  No data for {filename}")
        return
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    print(f"  💾 {len(records):>4} rows  →  {filename}")


def save_json(data: dict, filename: str):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  💾 JSON      →  {filename}")


def export_csvs(data: dict):
    all_notes, all_flashcards, all_quizzes = [], [], []
    for subject_data in data.values():
        all_notes.extend(subject_data.get("notes", []))
        all_flashcards.extend(subject_data.get("flashcards", []))
        all_quizzes.extend(subject_data.get("quiz", []))
    save_csv(all_notes,      "notes.csv")
    save_csv(all_flashcards, "flashcards.csv")
    save_csv(all_quizzes,    "quizzes.csv")
    save_json(data,          "full_export.json")
    return all_notes, all_flashcards, all_quizzes


# ── Chart Generator ───────────────────────────────────────────────────────────

def make_chart(data: dict, chart_path: Path):
    if not HAS_MATPLOTLIB:
        return None

    subjects = list(data.keys())
    notes_counts      = [len(data[s].get("notes", []))      for s in subjects]
    flashcard_counts  = [len(data[s].get("flashcards", [])) for s in subjects]
    quiz_counts       = [len(data[s].get("quiz", []))       for s in subjects]

    # Shorten long subject names for the chart
    short_names = [s[:12] + "…" if len(s) > 12 else s for s in subjects]

    x = range(len(subjects))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#f9f9f9")
    ax.set_facecolor("#f9f9f9")

    bars1 = ax.bar([i - width for i in x], notes_counts,     width, label="Notes",      color="#4A90D9", zorder=3)
    bars2 = ax.bar([i         for i in x], flashcard_counts, width, label="Flashcards", color="#50C878", zorder=3)
    bars3 = ax.bar([i + width for i in x], quiz_counts,      width, label="Quiz Qs",    color="#E8873A", zorder=3)

    ax.set_xlabel("Subject", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("CS Study Hub — Content Overview by Subject", fontsize=13, fontweight="bold", pad=15)
    ax.set_xticks(list(x))
    ax.set_xticklabels(short_names, rotation=20, ha="right", fontsize=9)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
    ax.spines[["top","right"]].set_visible(False)

    # Value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2, h + 0.3, str(int(h)),
                        ha="center", va="bottom", fontsize=8, color="#333")

    plt.tight_layout()
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()
    return chart_path


# ── PDF Generator ─────────────────────────────────────────────────────────────

def make_pdf(data: dict, all_notes: list, all_flashcards: list, all_quizzes: list):
    if not HAS_REPORTLAB:
        print("  ⚠️  reportlab not installed — skipping PDF.")
        return

    pdf_path   = OUTPUT_DIR / "study_hub_report.pdf"
    chart_path = OUTPUT_DIR / "chart.png"

    # Generate chart first
    chart_file = make_chart(data, chart_path) if HAS_MATPLOTLIB else None

    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    BLUE   = colors.HexColor("#2C5F9E")
    LGRAY  = colors.HexColor("#F2F4F8")
    DGRAY  = colors.HexColor("#444444")

    title_style = ParagraphStyle("title", parent=styles["Title"],
                                  fontSize=22, textColor=BLUE,
                                  spaceAfter=4, alignment=TA_CENTER)
    sub_style   = ParagraphStyle("sub", parent=styles["Normal"],
                                  fontSize=11, textColor=DGRAY,
                                  alignment=TA_CENTER, spaceAfter=2)
    h2_style    = ParagraphStyle("h2", parent=styles["Heading2"],
                                  fontSize=14, textColor=BLUE, spaceBefore=14, spaceAfter=6)
    h3_style    = ParagraphStyle("h3", parent=styles["Heading3"],
                                  fontSize=11, textColor=DGRAY, spaceBefore=8, spaceAfter=4)
    body_style  = ParagraphStyle("body", parent=styles["Normal"],
                                  fontSize=9, leading=13, textColor=DGRAY)
    small_style = ParagraphStyle("small", parent=styles["Normal"],
                                  fontSize=8, textColor=colors.grey)

    story = []
    now = datetime.now().strftime("%B %d, %Y  %I:%M %p")

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("📚 CS Study Hub", title_style))
    story.append(Paragraph("Automated Content Report", sub_style))
    story.append(Paragraph(f"Generated: {now}", small_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    story.append(Spacer(1, 0.8*cm))

    # ── Summary stats ─────────────────────────────────────────────────────────
    story.append(Paragraph("Summary", h2_style))

    total_notes = len(all_notes)
    total_fc    = len(all_flashcards)
    total_quiz  = len(all_quizzes)
    total_subj  = len(data)

    summary_data = [
        ["Metric", "Count"],
        ["Total Subjects",   str(total_subj)],
        ["Total Note Entries", str(total_notes)],
        ["Total Flashcard Pairs", str(total_fc)],
        ["Total Quiz Questions", str(total_quiz)],
        ["Total Content Items", str(total_notes + total_fc + total_quiz)],
    ]
    summary_table = Table(summary_data, colWidths=[10*cm, 5*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  BLUE),
        ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 10),
        ("BACKGROUND",  (0,1), (-1,-1), LGRAY),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LGRAY]),
        ("ALIGN",       (1,0), (1,-1),  "CENTER"),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",  (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.8*cm))

    # ── Chart ─────────────────────────────────────────────────────────────────
    if chart_file and chart_file.exists():
        story.append(Paragraph("Content Distribution by Subject", h2_style))
        story.append(Image(str(chart_file), width=16*cm, height=8*cm))
        story.append(Spacer(1, 0.8*cm))

    # ── Per-subject breakdown ─────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
    story.append(Paragraph("Per-Subject Breakdown", h2_style))

    table_data = [["Subject", "Notes", "Flashcards", "Quiz Qs", "Total"]]
    for name, subj_data in data.items():
        n  = len(subj_data.get("notes", []))
        fc = len(subj_data.get("flashcards", []))
        qz = len(subj_data.get("quiz", []))
        table_data.append([name, str(n), str(fc), str(qz), str(n+fc+qz)])

    breakdown_table = Table(table_data, colWidths=[6*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    breakdown_table.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0),  BLUE),
        ("TEXTCOLOR",      (0,0), (-1,0),  colors.white),
        ("FONTNAME",       (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LGRAY]),
        ("ALIGN",          (1,0), (-1,-1), "CENTER"),
        ("GRID",           (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
        ("TOPPADDING",     (0,0), (-1,-1), 6),
        ("LEFTPADDING",    (0,0), (0,-1),  10),
    ]))
    story.append(breakdown_table)
    story.append(Spacer(1, 1*cm))

    # ── Notes sample ─────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
    story.append(Paragraph("Sample Notes (first 10 entries)", h2_style))
    for rec in all_notes[:10]:
        story.append(Paragraph(f"<b>[{rec['subject']}]</b> {rec['topic']}", h3_style))
        story.append(Paragraph(rec["content"], body_style))
        story.append(Spacer(1, 0.2*cm))

    # ── Flashcard sample ──────────────────────────────────────────────────────
    if all_flashcards:
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
        story.append(Paragraph("Sample Flashcards (first 10 pairs)", h2_style))
        fc_table_data = [["#", "Subject", "Question", "Answer"]]
        for rec in all_flashcards[:10]:
            fc_table_data.append([
                Paragraph(str(rec["card_number"]), body_style),
                Paragraph(rec["subject"], body_style),
                Paragraph(rec["question"][:60] + ("…" if len(rec["question"]) > 60 else ""), body_style),
                Paragraph(rec["answer"][:60]   + ("…" if len(rec["answer"])   > 60 else ""), body_style),
            ])
        fc_table = Table(fc_table_data, colWidths=[1*cm, 3*cm, 6*cm, 6*cm])
        fc_table.setStyle(TableStyle([
            ("BACKGROUND",     (0,0), (-1,0),  BLUE),
            ("TEXTCOLOR",      (0,0), (-1,0),  colors.white),
            ("FONTNAME",       (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",       (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LGRAY]),
            ("ALIGN",          (0,0), (1,-1),  "CENTER"),
            ("GRID",           (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
            ("TOPPADDING",     (0,0), (-1,-1), 5),
            ("LEFTPADDING",    (0,0), (-1,-1), 6),
            ("WORDWRAP",       (0,0), (-1,-1), True),
        ]))
        story.append(fc_table)

    # ── Quiz sample ───────────────────────────────────────────────────────────
    if all_quizzes:
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
        story.append(Paragraph("Sample Quiz Questions (first 10)", h2_style))
        for rec in all_quizzes[:10]:
            story.append(Paragraph(
                f"<b>Q{rec['question_number']} [{rec['subject']}]:</b> {rec['question'][:120]}",
                body_style))
            if rec.get("correct_answer"):
                story.append(Paragraph(f"  ✅ Answer: {rec['correct_answer']}", small_style))
            story.append(Spacer(1, 0.25*cm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"CS Study Hub Automation Project  ·  Report generated on {now}",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"  📄 PDF       →  study_hub_report.pdf")

    # Clean up chart temp file
    if chart_file and chart_file.exists():
        chart_file.unlink()


# ── Main entry ────────────────────────────────────────────────────────────────

def generate(data: dict):
    """Generate all output files from scraped data dict."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("\n💾 Saving CSV files...")
    all_notes, all_flashcards, all_quizzes = export_csvs(data)
    print("\n📄 Generating PDF report...")
    make_pdf(data, all_notes, all_flashcards, all_quizzes)
    return all_notes, all_flashcards, all_quizzes
