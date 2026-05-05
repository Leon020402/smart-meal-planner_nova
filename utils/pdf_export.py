"""
PDF export utility — generates a restaurant-menu-style weekly meal plan.
"""
import io
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Colour palette (matches app theme) ────────────────────────────────────────
DARK   = colors.HexColor("#0F172A")
GREEN  = colors.HexColor("#166534")
LIGHT  = colors.HexColor("#F8F9FB")
MUTED  = colors.HexColor("#64748B")
BORDER = colors.HexColor("#94A3B8")
WHITE  = colors.white

# ── Styles ─────────────────────────────────────────────────────────────────────
def _styles():
    return {
        "title": ParagraphStyle(
            "title",
            fontName="Times-Bold",
            fontSize=24,
            textColor=DARK,
            alignment=TA_CENTER,
            spaceAfter=2,
            leading=28,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Times-Italic",
            fontSize=13,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "date_line": ParagraphStyle(
            "date_line",
            fontName="Helvetica",
            fontSize=9,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "day_header": ParagraphStyle(
            "day_header",
            fontName="Times-Bold",
            fontSize=14,
            textColor=GREEN,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "meal_label": ParagraphStyle(
            "meal_label",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "meal_name": ParagraphStyle(
            "meal_name",
            fontName="Times-Roman",
            fontSize=11,
            textColor=DARK,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "meal_detail": ParagraphStyle(
            "meal_detail",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "empty_meal": ParagraphStyle(
            "empty_meal",
            fontName="Helvetica-Oblique",
            fontSize=10,
            textColor=BORDER,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }


def generate_meal_plan_pdf(meal_plan, recipes: dict) -> bytes:
    """
    Generate a restaurant-menu-style PDF of the weekly meal plan.
    Returns the PDF as bytes for Streamlit download_button.
    """
    buffer = io.BytesIO()
    s = _styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=1.8*cm,
        bottomMargin=1.8*cm,
        title="Weekly Meal Plan",
        author="Smart Meal Planner",
    )

    story = []
    W = A4[0] - 4*cm  # usable width

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Weekly Meal Plan", s["title"]))
    story.append(Paragraph("Smart Meal Planner", s["subtitle"]))
    story.append(Paragraph(
        date.today().strftime("Generated on %B %d, %Y"), s["date_line"]
    ))
    story.append(Spacer(1, 0.35*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=DARK))
    story.append(Spacer(1, 0.3*cm))

    # ── Days ──────────────────────────────────────────────────────────────────
    from models.meal_plan import MealPlan

    for day_idx, day in enumerate(MealPlan.DAYS):
        # Day title row
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(day.upper(), s["day_header"]))
        story.append(Spacer(1, 0.12*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        story.append(Spacer(1, 0.15*cm))

        # Three meal columns
        meal_cells = []
        for meal_type in MealPlan.MEAL_TYPES:
            rid = meal_plan.plan[day][meal_type]
            recipe = recipes.get(rid) if rid else None

            cell_content = [
                Paragraph(meal_type.upper(), s["meal_label"]),
                Spacer(1, 3),
            ]
            if recipe:
                cell_content.append(Paragraph(recipe.name, s["meal_name"]))
            else:
                cell_content.append(Paragraph("—", s["empty_meal"]))

            meal_cells.append(cell_content)

        col_w = W / 3
        meal_table = Table(
            [meal_cells],
            colWidths=[col_w, col_w, col_w],
        )
        meal_table.setStyle(TableStyle([
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",(0, 0), (-1, -1), 8),
            ("TOPPADDING",  (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0),(-1, -1), 6),
            ("LINEAFTER",   (0, 0), (1, -1), 0.5, BORDER),
        ]))
        story.append(meal_table)
        story.append(Spacer(1, 0.2*cm))

        if day_idx < len(MealPlan.DAYS) - 1:
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=BORDER, dash=(2, 4)))
            story.append(Spacer(1, 0.1*cm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Smart Meal Planner — Plan smarter, eat better.", s["footer"]))

    doc.build(story)
    return buffer.getvalue()
