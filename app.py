"""
Smart Meal Planner & Grocery Optimizer
=======================================
A Streamlit app for weekly meal planning, pantry tracking,
automatic grocery list generation, and budget monitoring.
"""

import os
import sys
from datetime import date

import streamlit as st

# ── Path setup (ensures imports work regardless of run directory) ───────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.recipe import Recipe
from models.pantry_item import PantryItem
from models.meal_plan import MealPlan
from utils.storage import (
    load_recipes, save_recipes,
    load_pantry, save_pantry,
    load_meal_plan, save_meal_plan,
    load_budget, save_budget,
)
from utils.grocery import generate_grocery_list
from utils.suggestions import suggest_recipes_by_pantry, suggest_recipes_for_expiring
from utils.pdf_export import generate_meal_plan_pdf

# ── Page config — must be the very first Streamlit call ────────────────────────
st.set_page_config(
    page_title="Smart Meal Planner",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Outfit:wght@300;400;500;600&display=swap');

:root {
    --bg:       #F8F9FB;
    --card:     #FFFFFF;
    --sidebar:  #0F172A;
    --primary:  #166534;
    --accent:   #15803D;
    --muted:    #64748B;
    --border:   #E2E8F0;
    --text:     #0F172A;
    --radius:   8px;
    --shadow:   0 1px 6px rgba(0,0,0,0.06);
}

/* ── Base ── */
.stApp { background: var(--bg) !important; }

body, p, li, span, label, div, input, select, textarea {
    font-family: 'Outfit', sans-serif !important;
    color: var(--text);
}

h1, h2, h3, h4 {
    font-family: 'Cormorant Garamond', serif !important;
    color: var(--text) !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
}
h1 { font-size: 2.4rem !important; }
h2 { font-size: 1.7rem !important; }
h3 { font-size: 1.3rem !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--sidebar) !important;
    border-right: 1px solid #1E293B !important;
}
section[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
    font-family: 'Outfit', sans-serif !important;
}
section[data-testid="stSidebar"] strong,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #F1F5F9 !important;
    font-family: 'Cormorant Garamond', serif !important;
}
section[data-testid="stSidebar"] .stRadio > label { display: none; }
section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    font-size: 14px !important;
    font-weight: 400 !important;
    letter-spacing: 0.01em !important;
    color: #94A3B8 !important;
    padding: 2px 0 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #1E293B !important;
    margin: 16px 0 !important;
}
section[data-testid="stSidebar"] .stCaption {
    color: #475569 !important;
    font-size: 12px !important;
}

/* ── Metrics ── */
div[data-testid="metric-container"] {
    background: var(--card) !important;
    border-radius: var(--radius) !important;
    padding: 20px 24px !important;
    box-shadow: var(--shadow) !important;
    border: 1px solid var(--border) !important;
}
div[data-testid="metric-container"] label {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 2rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: var(--radius) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    letter-spacing: 0.02em !important;
    border: 1px solid var(--border) !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"] {
    background: #1F2937 !important;
    border-color: #1F2937 !important;
    color: #FFFFFF !important;
}
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {
    color: #FFFFFF !important;
}
/* Also catch form submit buttons which use a different kind */
.stFormSubmitButton > button {
    background: #1F2937 !important;
    border-color: #1F2937 !important;
    color: #FFFFFF !important;
}
.stFormSubmitButton > button p,
.stFormSubmitButton > button span {
    color: #FFFFFF !important;
}
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: var(--text) !important;
}
.stButton > button:hover { opacity: 0.82 !important; }

/* ── Sidebar nav icons ── */
section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    font-size: 14px !important;
    font-weight: 400 !important;
    letter-spacing: 0.03em !important;
    color: #94A3B8 !important;
    padding: 3px 0 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* ── Alerts ── */
.alert-warning {
    background: #FEFCE8;
    border: 1px solid #FDE047;
    border-left: 3px solid #CA8A04;
    border-radius: var(--radius);
    padding: 12px 16px;
    margin-bottom: 12px;
    font-size: 14px;
}
.alert-danger {
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-left: 3px solid #DC2626;
    border-radius: var(--radius);
    padding: 12px 16px;
    margin-bottom: 12px;
    font-size: 14px;
}

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin: 2px 2px 2px 0;
}
.badge-green  { background: #DCFCE7; color: #166534; }
.badge-orange { background: #FEF3C7; color: #92400E; }
.badge-blue   { background: #EFF6FF; color: #1D4ED8; }
.badge-red    { background: #FEF2F2; color: #991B1B; }

/* ── Forms & inputs ── */
.stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ── Hide sidebar collapse button completely ── */
[data-testid="baseButton-headerNoPadding"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"] button {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
    position: absolute !important;
}
</style>
"""

_JS = """
<script>
(function() {
    var SELECTORS = [
        '[data-testid="baseButton-headerNoPadding"]',
        '[data-testid="collapsedControl"]',
        '[data-testid="stSidebarCollapseButton"]',
        '[data-testid="stSidebarCollapsedControl"]'
    ];

    function removeButtons() {
        SELECTORS.forEach(function(sel) {
            document.querySelectorAll(sel).forEach(function(el) {
                el.remove();
            });
            try {
                window.parent.document.querySelectorAll(sel).forEach(function(el) {
                    el.remove();
                });
            } catch(e) {}
        });
    }

    // Run immediately and keep running after every Streamlit re-render
    removeButtons();
    setInterval(removeButtons, 200);
})();
</script>
"""


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def parse_ingredients(text: str) -> tuple:
    """
    Parse a multi-line ingredient string into a list of dicts.
    Expected format (one ingredient per line):  name | quantity | unit
    Returns (ingredients, failed_lines) where failed_lines is a list of
    (line_number, original_text) tuples for lines that could not be parsed.
    """
    ingredients = []
    failed_lines = []
    for i, line in enumerate(text.strip().splitlines(), start=1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3 or not parts[0]:
            failed_lines.append((i, line.strip()))
            continue
        try:
            qty = float(parts[1])
        except ValueError:
            failed_lines.append((i, line.strip()))
            continue
        ingredients.append({"name": parts[0], "quantity": qty, "unit": parts[2]})
    return ingredients, failed_lines


def format_ingredients(ingredients: list) -> str:
    """Format an ingredient list back to the editable multi-line string."""
    return "\n".join(
        f"{ing['name']} | {ing['quantity']} | {ing['unit']}"
        for ing in ingredients
    )


def get_recipe_icon(recipe) -> str:
    """Return a fitting food emoji based on recipe name and category."""
    name = recipe.name.lower()
    cat  = recipe.category.lower()

    # Name-based (more specific)
    if any(w in name for w in ["spaghetti", "pasta", "carbonara", "tagliatelle", "linguine"]):
        return "🍝"
    if "pizza" in name:
        return "🍕"
    if any(w in name for w in ["salad", "caprese"]):
        return "🥗"
    if any(w in name for w in ["soup", "lentil", "dal", "broth"]):
        return "🍲"
    if any(w in name for w in ["taco", "burrito", "quesadilla"]):
        return "🌮"
    if any(w in name for w in ["pancake", "waffle"]):
        return "🥞"
    if any(w in name for w in ["toast", "sandwich"]):
        return "🥪"
    if any(w in name for w in ["omelette", "omel", "egg", "shakshuka"]):
        return "🍳"
    if any(w in name for w in ["curry", "tikka", "masala"]):
        return "🍛"
    if any(w in name for w in ["stir fry", "stir-fry", "wok"]):
        return "🥘"
    if any(w in name for w in ["risotto"]):
        return "🍚"
    if any(w in name for w in ["oat", "overnight", "porridge"]):
        return "🥣"
    if any(w in name for w in ["salmon", "tuna", "fish", "teriyaki"]):
        return "🐟"
    if any(w in name for w in ["burger", "beef"]):
        return "🍔"
    if any(w in name for w in ["pad thai", "noodle", "ramen"]):
        return "🍜"
    if any(w in name for w in ["avocado"]):
        return "🥑"
    if any(w in name for w in ["chicken"]):
        return "🍗"
    if any(w in name for w in ["mushroom"]):
        return "🍄"
    if any(w in name for w in ["banana", "fruit", "smoothie"]):
        return "🍌"

    # Category fallback
    if cat == "italian":       return "🍝"
    if cat == "asian":         return "🍜"
    if cat == "mexican":       return "🌮"
    if cat == "mediterranean": return "🥗"
    if cat == "american":      return "🥞"
    if cat == "indian":        return "🍛"
    if cat == "french":        return "🥐"

    return "🍽️"


def get_expired_items(pantry: dict) -> list:
    return [item for item in pantry.values() if item.is_expired()]


def get_expiring_items(pantry: dict) -> list:
    return [item for item in pantry.values() if item.is_expiring_soon() and not item.is_expired()]


def pct(ratio: float) -> str:
    return f"{int(ratio * 100)}%"


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════

def init_state() -> None:
    """Load all persistent data into session_state on first run."""
    if "recipes" not in st.session_state:
        st.session_state.recipes = load_recipes()
    if "pantry" not in st.session_state:
        st.session_state.pantry = load_pantry()
    if "meal_plan" not in st.session_state:
        st.session_state.meal_plan = load_meal_plan()
    if "budget" not in st.session_state:
        st.session_state.budget = load_budget()
    # UI state
    if "editing_recipe_id" not in st.session_state:
        st.session_state.editing_recipe_id = None
    if "show_add_recipe" not in st.session_state:
        st.session_state.show_add_recipe = False
    if "editing_pantry_id" not in st.session_state:
        st.session_state.editing_pantry_id = None
    if "show_add_pantry" not in st.session_state:
        st.session_state.show_add_pantry = False


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def show_dashboard() -> None:
    st.title("Dashboard")
    st.markdown("Welcome to your **Smart Meal Planner**. Here's a snapshot of your week.")

    recipes  = st.session_state.recipes
    pantry   = st.session_state.pantry
    meal_plan = st.session_state.meal_plan
    budget   = st.session_state.budget

    # Planned cost — multiply each recipe's cost by how many times it's planned
    planned_cost = sum(
        recipes[rid].estimated_cost * count
        for rid, count in meal_plan.get_recipe_id_counts().items()
        if rid in recipes
    )

    # ── Key metrics ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recipes", len(recipes))
    c2.metric("Pantry Items", len(pantry))
    c3.metric("Meals Planned", meal_plan.get_total_meals())
    budget_delta = f"€{budget - planned_cost:.2f} remaining"
    c4.metric("Planned Cost", f"€{planned_cost:.2f}", budget_delta)

    st.markdown("---")

    # ── Weekly overview grid ──────────────────────────────────────────────────
    col_title, col_btn = st.columns([5, 1])
    col_title.subheader("This Week at a Glance")

    pdf_bytes = generate_meal_plan_pdf(meal_plan, recipes)
    col_btn.download_button(
        label="⬇ PDF",
        data=pdf_bytes,
        file_name="meal_plan.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    cols = st.columns(7)
    for i, day in enumerate(MealPlan.DAYS):
        with cols[i]:
            st.markdown(f"**{day[:3]}**")
            for meal in MealPlan.MEAL_TYPES:
                rid = meal_plan.plan[day][meal]
                if rid and rid in recipes:
                    name = recipes[rid].name
                    short = name if len(name) <= 14 else name[:13] + "…"
                    st.caption(f"_{meal[0]}_: {short}")
                else:
                    st.caption(f"_{meal[0]}_: —")

    st.markdown("---")

    # ── Expiry alerts ─────────────────────────────────────────────────────────
    expired  = get_expired_items(pantry)
    expiring = get_expiring_items(pantry)

    if expired:
        names = ", ".join(f"<b>{i.name}</b>" for i in expired)
        st.markdown(f'<div class="alert-danger">🚫 <b>Expired — remove from pantry:</b> {names}</div>',
                    unsafe_allow_html=True)

    if expiring:
        parts = []
        for i in expiring:
            d = i.days_until_expiry()
            label = "today" if d == 0 else (f"in {d} day" + ("s" if d != 1 else ""))
            parts.append(f"<b>{i.name}</b> ({label})")
        st.markdown(f'<div class="alert-warning">⏰ <b>Expiring soon:</b> {", ".join(parts)}</div>',
                    unsafe_allow_html=True)

    if not expired and not expiring:
        st.success("✅ All pantry items are fresh — nothing expiring soon!")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RECIPES
# ══════════════════════════════════════════════════════════════════════════════

def _parse_scraped_ingredient(text: str):
    """Parse one scraped ingredient line into (name, quantity, unit) or None."""
    import re

    FRACTIONS = {
        "½": 0.5, "⅓": 1/3, "⅔": 2/3, "¼": 0.25, "¾": 0.75,
        "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875,
        "⅙": 1/6, "⅚": 5/6, "⅕": 0.2, "⅖": 0.4, "⅗": 0.6, "⅘": 0.8,
    }
    UNIT_MAP = {
        "kg": "kg", "kilogram": "kg", "kilograms": "kg",
        "g": "g", "gram": "g", "grams": "g",
        "ml": "ml", "milliliter": "ml", "milliliters": "ml", "millilitre": "ml",
        "l": "L", "liter": "L", "liters": "L", "litre": "L", "litres": "L",
        "tbsp": "tbsp", "tablespoon": "tbsp", "tablespoons": "tbsp", "tbs": "tbsp",
        "tsp": "tsp", "teaspoon": "tsp", "teaspoons": "tsp",
        "cup": "cup", "cups": "cup",
        "oz": "oz", "ounce": "oz", "ounces": "oz",
        "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb",
        "pcs": "pcs", "piece": "pcs", "pieces": "pcs",
        "pinch": "pinch", "pinches": "pinch",
        "clove": "pcs", "cloves": "pcs",
        "slice": "pcs", "slices": "pcs",
        "can": "pcs", "cans": "pcs",
        "bunch": "pcs", "bunches": "pcs",
        "stalk": "pcs", "stalks": "pcs",
        "sprig": "pcs", "sprigs": "pcs",
        "pot": "pcs",
    }

    text = text.lstrip("#").strip()
    text = re.sub(r"\([^)]*\)", "", text).strip()
    text = re.sub(r"\s+", " ", text).strip().rstrip("),.")

    for frac, val in FRACTIONS.items():
        text = text.replace(frac, str(val))

    text = re.sub(r"(\d+(?:\.\d+)?)\s+to\s+\d+(?:\.\d+)?", r"\1", text)

    # Format 1: "100g flour" — qty glued to unit
    m_glued = re.match(r"^(\d+(?:\.\d+)?)\s*([a-zA-Z]+)\s+(.+)$", text)
    if m_glued:
        try:
            qty = float(m_glued.group(1))
        except ValueError:
            qty = 1.0
        unit_word = m_glued.group(2).lower()
        name = m_glued.group(3).strip().rstrip("),").strip()
        if unit_word in UNIT_MAP:
            return name.title(), round(qty, 2), UNIT_MAP[unit_word]

    # Format 2: "2 tablespoons olive oil"
    m = re.match(
        r"^(\d+(?:\.\d+)?(?:\s+\d+(?:\.\d+)?)?)\s+([a-zA-Z]+)(?:\s+(.+))?$",
        text.strip()
    )
    if m:
        try:
            qty = sum(float(p) for p in m.group(1).split())
        except ValueError:
            qty = 1.0
        word = m.group(2).lower()
        rest = (m.group(3) or "").strip().rstrip("),").strip()
        if word in UNIT_MAP:
            name = rest if rest else word
            unit = UNIT_MAP[word]
        else:
            name = (word + (" " + rest if rest else "")).strip()
            unit = "pcs"
        name = re.sub(r"\s+", " ", name).strip()
        if name:
            return name.title(), round(qty, 2), unit

    return None


def _scrape_recipe_from_url(url: str) -> dict:
    """Scrape a recipe from a URL using recipe-scrapers."""
    from recipe_scrapers import scrape_me
    try:
        scraper = scrape_me(url, wild_mode=True)
    except TypeError:
        scraper = scrape_me(url)

    try:
        title = scraper.title() or ""
    except Exception:
        title = ""

    try:
        prep = scraper.total_time() or scraper.prep_time() or 20
    except Exception:
        prep = 20

    try:
        instructions = scraper.instructions() or ""
    except Exception:
        instructions = ""

    raw_ingredients, parsed_lines, failed_lines = [], [], []
    try:
        for ing in scraper.ingredients():
            raw_ingredients.append(ing)
            result = _parse_scraped_ingredient(ing)
            if result:
                n, q, u = result
                parsed_lines.append(f"{n} | {q} | {u}")
            else:
                failed_lines.append(f"# {ing}")
    except Exception:
        pass

    detected_category = "Other"
    try:
        cuisine = (scraper.cuisine() or "").lower()
    except Exception:
        cuisine = ""
    name_lower = title.lower()
    if any(w in cuisine or w in name_lower for w in ["italian", "pasta", "pizza", "risotto"]):
        detected_category = "Italian"
    elif any(w in cuisine or w in name_lower for w in ["asian", "chinese", "japanese", "thai", "korean", "stir", "wok"]):
        detected_category = "Asian"
    elif any(w in cuisine or w in name_lower for w in ["mexican", "taco", "burrito", "enchilada", "quesadilla"]):
        detected_category = "Mexican"
    elif any(w in cuisine or w in name_lower for w in ["mediterranean", "greek", "turkish", "lebanese"]):
        detected_category = "Mediterranean"
    elif any(w in cuisine or w in name_lower for w in ["american", "burger", "bbq", "pancake", "waffle"]):
        detected_category = "American"
    elif any(w in cuisine or w in name_lower for w in ["indian", "curry", "masala", "tikka", "butter chicken", "dal", "biryani"]):
        detected_category = "Indian"
    elif any(w in cuisine or w in name_lower for w in ["french", "crepe", "quiche", "ratatouille"]):
        detected_category = "French"

    all_text = (title + " " + " ".join(raw_ingredients) + " " + instructions).lower()
    detected_dietary = []
    animal = ["meat", "chicken", "beef", "pork", "lamb", "fish", "salmon", "tuna",
              "shrimp", "prawn", "egg", "milk", "cream", "butter", "cheese",
              "yogurt", "honey", "pancetta", "bacon", "ham", "gelatin"]
    meat_fish = ["meat", "chicken", "beef", "pork", "lamb", "fish", "salmon", "tuna",
                 "shrimp", "prawn", "pancetta", "bacon", "ham", "anchovy", "gelatin"]
    if not any(w in all_text for w in animal):
        detected_dietary += ["Vegan", "Vegetarian"]
    elif not any(w in all_text for w in meat_fish):
        detected_dietary.append("Vegetarian")
    if any(w in all_text for w in ["chicken", "beef", "fish", "salmon", "tuna", "shrimp",
                                    "lentil", "chickpea", "tofu", "egg", "steak", "lamb"]):
        detected_dietary.append("High-Protein")
    if int(prep) <= 30 if prep else False:
        detected_dietary.append("Quick")
    if not any(w in all_text for w in ["flour", "pasta", "bread", "wheat", "barley",
                                        "tortilla", "crouton", "noodle", "couscous"]):
        detected_dietary.append("Gluten-Free")

    return {
        "name": title,
        "prep_time": int(prep) if prep else 20,
        "instructions": instructions,
        "raw_ingredients": raw_ingredients,
        "parsed_lines": parsed_lines,
        "failed_lines": failed_lines,
        "category": detected_category,
        "dietary_types": detected_dietary,
    }


def _recipe_form(recipe: Recipe = None) -> None:
    """Render the add / edit form for a Recipe."""
    is_edit = recipe is not None
    st.subheader("Edit Recipe" if is_edit else "New Recipe")

    # ── URL Scraper (only shown when adding a new recipe) ─────────────────────
    if not is_edit:
        if "show_url_importer" not in st.session_state:
            st.session_state.show_url_importer = False

        if st.button("↓  Import from URL", use_container_width=False):
            st.session_state.show_url_importer = not st.session_state.show_url_importer
            st.rerun()

        if st.session_state.show_url_importer:
            with st.container(border=True):
                url_col, btn_col = st.columns([5, 1])
                url_input = url_col.text_input(
                    "Paste a recipe URL to auto-fill the fields below",
                    placeholder="https://www.bbcgoodfood.com/recipes/...",
                )
                import_clicked = btn_col.button("Import", use_container_width=True, type="primary")

                if import_clicked and url_input.strip():
                    with st.spinner("Fetching recipe…"):
                        try:
                            scraped_data = _scrape_recipe_from_url(url_input.strip())
                            st.session_state["scraped_recipe"] = scraped_data
                            st.session_state["import_msg"] = ("success", f"✅ Imported: **{scraped_data['name']}** — fields are pre-filled below.")
                            st.session_state.show_url_importer = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Could not import recipe. The site may not be supported. ({e})")

        # Show persisted import message (survives rerun)
        if "import_msg" in st.session_state:
            msg_type, msg_text = st.session_state.pop("import_msg")
            if msg_type == "success":
                st.success(msg_text)
                st.info("📋 Please review all pre-filled fields before saving — automatic parsing may not be 100% accurate.")

        st.markdown("")

    # Pull scraped values if available
    scraped = st.session_state.get("scraped_recipe", {}) if not is_edit else {}

    # Build ingredient text: parsed lines first, then unparseable as comments
    scraped_ing_text = ""
    has_failed = False
    if scraped.get("parsed_lines") or scraped.get("failed_lines"):
        all_lines = scraped.get("parsed_lines", []) + scraped.get("failed_lines", [])
        scraped_ing_text = "\n".join(all_lines)
        has_failed = bool(scraped.get("failed_lines"))

    with st.form("recipe_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        name = col1.text_input(
            "Recipe Name *",
            value=recipe.name if is_edit else scraped.get("name", ""),
            placeholder="e.g. Chicken Stir Fry",
        )
        if is_edit and recipe.category in Recipe.CATEGORY_OPTIONS:
            cat_idx = Recipe.CATEGORY_OPTIONS.index(recipe.category)
        elif scraped.get("category") in Recipe.CATEGORY_OPTIONS:
            cat_idx = Recipe.CATEGORY_OPTIONS.index(scraped["category"])
        else:
            cat_idx = 0
        category = col2.selectbox("Category", Recipe.CATEGORY_OPTIONS, index=cat_idx)

        col3, col4 = st.columns(2)
        prep_time = col3.number_input(
            "Prep Time (minutes)", min_value=1, max_value=360,
            value=recipe.prep_time if is_edit else scraped.get("prep_time", 20),
        )
        estimated_cost = col4.number_input(
            "Estimated Cost (€)", min_value=0.0, max_value=500.0, step=0.5,
            value=recipe.estimated_cost if is_edit else 0.0,
        )
        if not is_edit and not recipe:
            col4.caption("Enter estimated cost manually.")

        dietary_types = st.multiselect(
            "Dietary Types",
            Recipe.DIETARY_OPTIONS,
            default=recipe.dietary_types if is_edit else scraped.get("dietary_types", []),
        )

        st.markdown(
            "**Ingredients** &nbsp;—&nbsp; one per line, format: `name | quantity | unit`"
        )
        if is_edit:
            default_ing = format_ingredients(recipe.ingredients)
        elif scraped_ing_text:
            default_ing = scraped_ing_text
        else:
            default_ing = "pasta | 200 | g\neggs | 2 | pcs"

        ingredient_text = st.text_area(
            "Ingredients",
            value=default_ing,
            height=160,
            label_visibility="collapsed",
            placeholder="pasta | 200 | g\neggs | 2 | pcs\nolive oil | 2 | tbsp",
        )

        if scraped_ing_text and not is_edit:
            if has_failed:
                st.caption("⚠️ Some ingredients (marked with #) could not be parsed automatically — please reformat them to `name | quantity | unit` before saving. Please review all fields carefully before saving.")

        instructions = st.text_area(
            "Instructions",
            value=recipe.instructions if is_edit else scraped.get("instructions", ""),
            height=100,
            placeholder="Describe the preparation steps…",
        )

        btn1, btn2 = st.columns(2)
        submitted = btn1.form_submit_button("Save", use_container_width=True, type="primary")
        cancelled = btn2.form_submit_button("Cancel", use_container_width=True)

    # Handle outside the form context so rerun works cleanly
    if cancelled:
        st.session_state.editing_recipe_id = None
        st.session_state.show_add_recipe   = False
        st.session_state.pop("scraped_recipe", None)
        st.rerun()

    if submitted:
        if not name.strip():
            st.error("Recipe name is required.")
            return
        ingredients, failed_lines = parse_ingredients(ingredient_text)
        if not ingredients:
            st.error("Please add at least one ingredient using the format:  name | quantity | unit")
            return
        if failed_lines:
            for line_num, line_text in failed_lines:
                st.warning(
                    f"Line {line_num} could not be parsed and was skipped: "
                    f'`{line_text}` — please use the format `name | quantity | unit`'
                )
            return
        if float(estimated_cost) == 0.0:
            st.warning(
                "⚠️ Estimated cost is €0.00. This will affect your budget tracking. "
                "If this is intentional, click **Save** again to confirm."
            )
            if "cost_zero_confirmed" not in st.session_state:
                st.session_state["cost_zero_confirmed"] = True
                return
        st.session_state.pop("cost_zero_confirmed", None)

        if is_edit:
            recipe.name           = name.strip()
            recipe.category       = category
            recipe.prep_time      = int(prep_time)
            recipe.estimated_cost = float(estimated_cost)
            recipe.dietary_types  = dietary_types
            recipe.ingredients    = ingredients
            recipe.instructions   = instructions.strip()
            st.session_state.recipes[recipe.id] = recipe
        else:
            new_recipe = Recipe(
                name=name.strip(),
                ingredients=ingredients,
                prep_time=int(prep_time),
                category=category,
                dietary_types=dietary_types,
                estimated_cost=float(estimated_cost),
                instructions=instructions.strip(),
            )
            st.session_state.recipes[new_recipe.id] = new_recipe

        save_recipes(st.session_state.recipes)
        st.session_state.editing_recipe_id = None
        st.session_state.show_add_recipe   = False
        st.session_state.pop("scraped_recipe", None)
        st.success("✅ Recipe saved!")
        st.rerun()


def show_recipes() -> None:
    st.title("Recipes")

    recipes = st.session_state.recipes

    # Show form if adding or editing
    if st.session_state.show_add_recipe:
        _recipe_form()
        return
    if st.session_state.editing_recipe_id:
        recipe = recipes.get(st.session_state.editing_recipe_id)
        if recipe:
            _recipe_form(recipe)
            return
        # Recipe not found — reset state
        st.session_state.editing_recipe_id = None

    # ── Filter bar ────────────────────────────────────────────────────────────
    col_s, col_c, col_d, col_add = st.columns([3, 2, 2, 1])
    search     = col_s.text_input("Search", placeholder="Search by name…", label_visibility="collapsed")
    cat_filter = col_c.selectbox("Category", ["All"] + Recipe.CATEGORY_OPTIONS, label_visibility="collapsed")
    diet_filter = col_d.multiselect("Dietary", Recipe.DIETARY_OPTIONS, label_visibility="collapsed",
                                    placeholder="Filter by diet…")

    if col_add.button("Add Recipe", use_container_width=True, type="primary"):
        st.session_state.show_add_recipe = True
        st.rerun()

    st.markdown("---")

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = list(recipes.values())

    if search:
        filtered = [r for r in filtered if search.lower() in r.name.lower()]
    if cat_filter != "All":
        filtered = [r for r in filtered if r.category == cat_filter]
    if diet_filter:
        filtered = [r for r in filtered if r.matches_dietary_filter(diet_filter)]

    if not filtered:
        st.info("No recipes found. Adjust your filters or add a new recipe!")
        return

    st.caption(f"Showing **{len(filtered)}** recipe(s)")

    # ── Recipe cards — 3 per row ──────────────────────────────────────────────
    for row_start in range(0, len(filtered), 3):
        cols = st.columns(3)
        for j, recipe in enumerate(filtered[row_start: row_start + 3]):
            with cols[j]:
                with st.container(border=True):
                    icon = get_recipe_icon(recipe)
                    st.subheader(f"{icon}  {recipe.name}")
                    st.markdown(
                        f"🏷️ **{recipe.category}** &nbsp;·&nbsp; "
                        f"⏱️ **{recipe.prep_time} min** &nbsp;·&nbsp; "
                        f"<span style='white-space:nowrap'>💰 **€{recipe.estimated_cost:.2f}**</span>",
                        unsafe_allow_html=True,
                    )

                    if recipe.dietary_types:
                        badges = "".join(
                            f'<span class="badge badge-green">{dt}</span>'
                            for dt in recipe.dietary_types
                        )
                        st.markdown(badges, unsafe_allow_html=True)
                        st.markdown("")  # spacing

                    if recipe.ingredients:
                        ing_html = "".join(
                            f"<li>{ing['name']} — {ing['quantity']} {ing['unit']}</li>"
                            for ing in recipe.ingredients
                        )
                        st.markdown(f"""
<details>
<summary style="cursor:pointer;font-weight:600;color:#374151;font-size:14px;padding:6px 0;font-family:'Outfit',sans-serif;">
  Ingredients ({len(recipe.ingredients)})
</summary>
<ul style="margin:8px 0 4px 16px;padding:0;color:#374151;font-size:14px;font-family:'Outfit',sans-serif;line-height:1.8;">
{ing_html}
</ul>
</details>""", unsafe_allow_html=True)

                    if recipe.instructions:
                        st.markdown(f"""
<details>
<summary style="cursor:pointer;font-weight:600;color:#374151;font-size:14px;padding:6px 0;font-family:'Outfit',sans-serif;">
  Instructions
</summary>
<p style="margin:8px 0 4px 0;color:#374151;font-size:14px;line-height:1.7;font-family:'Outfit',sans-serif;">
{recipe.instructions}
</p>
</details>
<div style="margin-top:20px;"></div>""", unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)

                    b1, b2 = st.columns(2)
                    if b1.button("Edit", key=f"edit_r_{recipe.id}", use_container_width=True):
                        st.session_state.editing_recipe_id = recipe.id
                        st.rerun()

                    if b2.button("Delete", key=f"del_r_{recipe.id}", use_container_width=True):
                        # Also remove from meal plan and clear any selectbox state
                        st.session_state.meal_plan.clear_recipe_id(recipe.id)
                        for day in MealPlan.DAYS:
                            for meal in MealPlan.MEAL_TYPES:
                                key = f"mp_{day}_{meal}"
                                if st.session_state.get(key) == recipe.name:
                                    del st.session_state[key]
                        save_meal_plan(st.session_state.meal_plan)
                        del st.session_state.recipes[recipe.id]
                        save_recipes(st.session_state.recipes)
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PANTRY
# ══════════════════════════════════════════════════════════════════════════════

def _pantry_form(item: PantryItem = None) -> None:
    """Render the add / edit form for a PantryItem."""
    is_edit = item is not None
    st.subheader("Edit Item" if is_edit else "New Pantry Item")

    with st.form("pantry_form", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)

        name = col1.text_input(
            "Ingredient Name *",
            value=item.name if is_edit else "",
            placeholder="e.g. Olive Oil",
        )
        quantity = col2.number_input(
            "Quantity", min_value=0.0, step=0.5,
            value=float(item.quantity) if is_edit else 1.0,
        )
        unit_idx = PantryItem.UNIT_OPTIONS.index(item.unit) \
            if is_edit and item.unit in PantryItem.UNIT_OPTIONS else 0
        unit = col3.selectbox("Unit", PantryItem.UNIT_OPTIONS, index=unit_idx)

        # Expiry date (optional via checkbox)
        has_expiry_default = is_edit and bool(item.expiration_date)
        has_expiry = st.checkbox("Track expiration date", value=has_expiry_default)

        exp_default = (
            date.fromisoformat(item.expiration_date)
            if (is_edit and item.expiration_date)
            else date.today()
        )
        exp_date = st.date_input("Expiration Date", value=exp_default,
                                  help="Only used if 'Track expiration date' is checked.")

        btn1, btn2 = st.columns(2)
        submitted = btn1.form_submit_button("Save", use_container_width=True, type="primary")
        cancelled = btn2.form_submit_button("Cancel", use_container_width=True)

    if cancelled:
        st.session_state.editing_pantry_id = None
        st.session_state.show_add_pantry   = False
        st.rerun()

    if submitted:
        if not name.strip():
            st.error("Ingredient name is required.")
            return

        exp_str = exp_date.isoformat() if has_expiry else None

        if is_edit:
            item.name            = name.strip()
            item.quantity        = float(quantity)
            item.unit            = unit
            item.expiration_date = exp_str
            st.session_state.pantry[item.id] = item
        else:
            new_item = PantryItem(
                name=name.strip(),
                quantity=float(quantity),
                unit=unit,
                expiration_date=exp_str,
            )
            st.session_state.pantry[new_item.id] = new_item

        save_pantry(st.session_state.pantry)
        st.session_state.editing_pantry_id = None
        st.session_state.show_add_pantry   = False
        st.success("✅ Pantry updated!")
        st.rerun()


def show_pantry() -> None:
    st.title("Pantry")

    pantry = st.session_state.pantry

    if st.session_state.show_add_pantry:
        _pantry_form()
        return
    if st.session_state.editing_pantry_id:
        item = pantry.get(st.session_state.editing_pantry_id)
        if item:
            _pantry_form(item)
            return
        st.session_state.editing_pantry_id = None

    # ── Header row ────────────────────────────────────────────────────────────
    col_h, col_add = st.columns([5, 1])
    col_h.markdown("Track ingredients you have at home, including quantities and expiry dates.")
    if col_add.button("Add Item", use_container_width=True, type="primary"):
        st.session_state.show_add_pantry = True
        st.rerun()

    if not pantry:
        st.info("Your pantry is empty. Add your first ingredient!")
        return

    # ── Summary row ───────────────────────────────────────────────────────────
    expired  = get_expired_items(pantry)
    expiring = get_expiring_items(pantry)
    fresh    = [i for i in pantry.values() if not i.is_expired() and not i.is_expiring_soon()]

    s1, s2, s3 = st.columns(3)
    s1.metric("Fresh",         len(fresh))
    s2.metric("Expiring Soon", len(expiring))
    s3.metric("Expired",       len(expired))

    st.markdown("---")

    # ── Table header ─────────────────────────────────────────────────────────
    hdr = st.columns([3, 1, 1, 2, 2])
    hdr[0].markdown("**Ingredient**")
    hdr[1].markdown("**Qty**")
    hdr[2].markdown("**Unit**")
    hdr[3].markdown("**Expires**")
    hdr[4].markdown("**Actions**")
    st.divider()

    # Sort: expired first → expiring → fresh
    sorted_items = (
        sorted(expired,  key=lambda x: x.name) +
        sorted(expiring, key=lambda x: x.days_until_expiry()) +
        sorted(fresh,    key=lambda x: x.name)
    )

    for item in sorted_items:
        row = st.columns([3, 1, 1, 2, 2])

        if item.is_expired():
            icon  = "🔴"
            days_ago = abs(item.days_until_expiry())
            label = f"Expired {days_ago} day{'s' if days_ago != 1 else ''} ago" if days_ago > 0 else "Expired today"
        elif item.is_expiring_soon():
            icon  = "🟡"
            d     = item.days_until_expiry()
            label = "Today!" if d == 0 else f"In {d} day{'s' if d != 1 else ''}"
        else:
            icon  = "🟢"
            label = item.expiration_date if item.expiration_date else "No date"

        row[0].write(f"{icon} {item.name}")
        row[1].write(f"{item.quantity:g}")
        row[2].write(item.unit)
        row[3].write(label)

        btn_cols = row[4].columns(2)
        if btn_cols[0].button("Edit", key=f"edit_p_{item.id}", use_container_width=True):
            st.session_state.editing_pantry_id = item.id
            st.rerun()
        if btn_cols[1].button("Delete", key=f"del_p_{item.id}", use_container_width=True):
            del st.session_state.pantry[item.id]
            save_pantry(st.session_state.pantry)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MEAL PLANNER
# ══════════════════════════════════════════════════════════════════════════════

def show_meal_planner() -> None:
    st.title("Meal Planner")
    st.caption("Assign recipes to any slot. Changes are saved automatically.")

    recipes   = st.session_state.recipes
    meal_plan = st.session_state.meal_plan

    if not recipes:
        st.warning("No recipes available yet. Head to **🍽️ Recipes** and add some first!")
        return

    # Build option list (name -> id mapping)
    none_label = "— none —"
    sorted_recipes = sorted(recipes.values(), key=lambda r: r.name)
    option_map: dict = {none_label: None}
    option_map.update({r.name: r.id for r in sorted_recipes})
    option_names = list(option_map.keys())

    changed = False

    for meal_type in MealPlan.MEAL_TYPES:
        st.subheader(meal_type)
        cols = st.columns(7)

        for i, day in enumerate(MealPlan.DAYS):
            with cols[i]:
                st.caption(f"**{day[:3]}**")

                current_rid = meal_plan.plan[day][meal_type]
                widget_key  = f"mp_{day}_{meal_type}"

                # Determine current index for the selectbox
                if current_rid and current_rid in recipes:
                    current_name = recipes[current_rid].name
                    current_idx  = option_names.index(current_name) \
                        if current_name in option_names else 0
                else:
                    current_idx = 0

                selected_name = st.selectbox(
                    label=f"{day}_{meal_type}",
                    options=option_names,
                    index=current_idx,
                    key=widget_key,
                    label_visibility="collapsed",
                )

                selected_rid = option_map[selected_name]

                # Persist change if user selected a different recipe
                if selected_rid != current_rid:
                    if selected_rid:
                        meal_plan.assign_recipe(day, meal_type, selected_rid)
                    else:
                        meal_plan.remove_recipe(day, meal_type)
                    changed = True

        st.markdown("---")

    if changed:
        save_meal_plan(meal_plan)

    # ── Summary ───────────────────────────────────────────────────────────────
    total_meals = meal_plan.get_total_meals()
    total_cost  = sum(
        recipes[rid].estimated_cost * count
        for rid, count in meal_plan.get_recipe_id_counts().items()
        if rid in recipes
    )

    if total_meals > 0:
        st.info(
            f"**{total_meals} meal{'s' if total_meals != 1 else ''} planned** this week · "
            f"Estimated cost: **€{total_cost:.2f}**"
        )
    else:
        st.info("No meals planned yet. Use the dropdowns above to assign recipes to your week!")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: GROCERY LIST
# ══════════════════════════════════════════════════════════════════════════════

def show_grocery_list() -> None:
    st.title("Grocery List")
    st.caption("Auto-generated from your meal plan. Pantry items are automatically deducted.")

    meal_plan = st.session_state.meal_plan
    recipes   = st.session_state.recipes
    pantry    = st.session_state.pantry

    if meal_plan.get_total_meals() == 0:
        st.warning("No meals planned yet. Go to **🗓️ Meal Planner** to assign recipes first!")
        return

    grocery_list = generate_grocery_list(meal_plan, recipes, pantry)

    if not grocery_list:
        st.success("🎉 Your pantry already covers everything for this week's meals. Nothing to buy!")
        return

    # ── Summary ───────────────────────────────────────────────────────────────
    missing  = [g for g in grocery_list if g["status"] == "missing"]
    partial  = [g for g in grocery_list if g["status"] == "partial"]
    mismatch = [g for g in grocery_list if g["status"] == "unit_mismatch"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Missing",      len(missing),  help="Not in pantry at all")
    c2.metric("Need More",    len(partial),  help="In pantry but not enough")
    c3.metric("Check Units",  len(mismatch), help="In pantry but units differ — verify manually")

    st.markdown("---")

    # ── List items ────────────────────────────────────────────────────────────
    for item in grocery_list:
        status = item["status"]
        if status == "missing":
            icon  = "○"
            note  = ""
        elif status == "partial":
            icon  = "◑"
            note  = " _(need more)_"
        else:
            icon  = "!"
            note  = f" _(pantry: {item['note']})_" if item["note"] else ""

        col_icon, col_name, col_qty = st.columns([1, 5, 2])
        col_icon.write(icon)
        col_name.write(f"**{item['name']}**{note}")
        col_qty.write(f"{item['quantity']:g} {item['unit']}")

    st.markdown("---")

    # ── Copyable text export ──────────────────────────────────────────────────
    export_text = "SHOPPING LIST\n" + "=" * 30 + "\n"
    for item in grocery_list:
        export_text += f"☐  {item['name']:20s} {item['quantity']:>6g} {item['unit']}\n"

    st.text_area("📋 Copy your shopping list", value=export_text, height=220)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SUGGESTIONS
# ══════════════════════════════════════════════════════════════════════════════

def show_suggestions() -> None:
    st.title("Suggestions")

    recipes = st.session_state.recipes
    pantry  = st.session_state.pantry

    if not pantry:
        st.warning("Your pantry is empty. Add ingredients in **🫙 Pantry** to get personalised suggestions!")
        return

    tab1, tab2 = st.tabs(["Based on Your Pantry", "Use Expiring Ingredients"])

    # ── Tab 1: Pantry-based suggestions ──────────────────────────────────────
    with tab1:
        st.caption("Recipes you can mostly or fully make with what's already at home.")

        threshold = st.slider(
            "Minimum ingredient match (%)", 10, 100, 50, step=10,
            help="Lower = more suggestions; higher = only well-matched recipes",
        ) / 100

        suggestions = suggest_recipes_by_pantry(pantry, recipes, min_match_ratio=threshold)

        if not suggestions:
            st.info(
                "No recipes match your current pantry at this threshold. "
                "Try lowering the slider or adding more pantry items."
            )
        else:
            st.success(f"Found **{len(suggestions)}** matching recipe(s)!")
            for s in suggestions:
                recipe = s["recipe"]
                with st.container(border=True):
                    head1, head2 = st.columns([4, 1])
                    head1.markdown(f"### {recipe.name}")
                    head2.metric("Match", pct(s["match_ratio"]))

                    info1, info2, info3 = st.columns(3)
                    info1.caption(f"⏱️ {recipe.prep_time} min")
                    info2.caption(f"💰 €{recipe.estimated_cost:.2f}")
                    info3.caption(f"🏷️ {recipe.category}")

                    if s["matched"]:
                        st.markdown("✅ **Have:** " + ", ".join(sorted(s["matched"])))
                    if s["missing"]:
                        st.markdown("🛒 **Still need:** " + ", ".join(sorted(s["missing"])))

    # ── Tab 2: Expiry-based suggestions ──────────────────────────────────────
    with tab2:
        st.caption("Recipes that help you use up ingredients before they go bad.")

        expiring_items = get_expiring_items(pantry)

        if not expiring_items:
            st.success("✅ Nothing expiring soon — come back when you have ingredients to use up!")
        else:
            names_html = ", ".join(f"<b>{i.name}</b>" for i in expiring_items)
            st.markdown(
                f'<div class="alert-warning">⏰ Expiring soon: {names_html}</div>',
                unsafe_allow_html=True,
            )

            expiry_suggestions = suggest_recipes_for_expiring(pantry, recipes)

            if not expiry_suggestions:
                st.info("No recipes in your collection use these expiring ingredients. Consider adding more recipes!")
            else:
                for s in expiry_suggestions:
                    recipe = s["recipe"]
                    with st.container(border=True):
                        head1, head2 = st.columns([4, 1])
                        head1.markdown(f"### {recipe.name}")
                        n = len(s["uses_expiring"])
                        head2.info(f"Uses {n} expiring item{'s' if n != 1 else ''}")

                        st.caption(f"⏱️ {recipe.prep_time} min · 💰 €{recipe.estimated_cost:.2f} · 🏷️ {recipe.category}")
                        st.markdown("⏰ **Uses expiring:** " + ", ".join(sorted(s["uses_expiring"])))
                        if s["missing"]:
                            st.markdown("🛒 **Still need:** " + ", ".join(sorted(s["missing"])))


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: BUDGET
# ══════════════════════════════════════════════════════════════════════════════

def show_budget() -> None:
    st.title("Budget")
    st.caption("Set your weekly food budget and track how your meal plan compares.")

    recipes   = st.session_state.recipes
    meal_plan = st.session_state.meal_plan

    # ── Budget input ──────────────────────────────────────────────────────────
    col_input, col_save = st.columns([3, 1])
    new_budget = col_input.number_input(
        "Weekly Food Budget (€)",
        min_value=0.0, max_value=10_000.0, step=5.0,
        value=st.session_state.budget,
    )
    if col_save.button("Save", use_container_width=True):
        st.session_state.budget = new_budget
        save_budget(new_budget)
        st.success("Budget saved!")

    budget = st.session_state.budget
    st.markdown("---")

    # ── Cost summary ──────────────────────────────────────────────────────────
    recipe_counts   = meal_plan.get_recipe_id_counts()
    planned_recipes = [(rid, recipes[rid], count) for rid, count in recipe_counts.items() if rid in recipes]

    if not planned_recipes:
        st.info("No meals planned yet. Go to **🗓️ Meal Planner** to assign recipes!")
        return

    total_cost = sum(r.estimated_cost * count for _, r, count in planned_recipes)
    remaining  = budget - total_cost

    c1, c2, c3 = st.columns(3)
    c1.metric("Planned Cost", f"€{total_cost:.2f}")
    c2.metric("Weekly Budget", f"€{budget:.2f}")
    c3.metric(
        "💵 Remaining",
        f"€{abs(remaining):.2f}",
        delta=f"{'over' if remaining < 0 else 'under'} budget",
        delta_color="inverse" if remaining < 0 else "normal",
    )

    # ── Progress bar ──────────────────────────────────────────────────────────
    if budget > 0:
        ratio  = min(total_cost / budget, 1.0)
        status = "🔴 Over Budget" if remaining < 0 else ("🟡 Close to Limit" if ratio > 0.8 else "🟢 On Track")
        st.markdown(f"**Budget Usage — {status}**")
        st.progress(ratio)
        st.caption(f"€{total_cost:.2f} of €{budget:.2f} used ({pct(ratio)})")

    st.markdown("---")

    # ── Breakdown table ───────────────────────────────────────────────────────
    st.subheader("Cost Breakdown by Meal")

    rows = []
    for day in MealPlan.DAYS:
        for meal_type in MealPlan.MEAL_TYPES:
            rid = meal_plan.plan[day][meal_type]
            if rid and rid in recipes:
                r = recipes[rid]
                rows.append({
                    "Day":       day,
                    "Meal":      meal_type,
                    "Recipe":    r.name,
                    "Category":  r.category,
                    "Cost (€)":  f"€{r.estimated_cost:.2f}",
                })

    if rows:
        import pandas as pd
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Verdict ───────────────────────────────────────────────────────────────
    if remaining < 0:
        st.error(
            f"⚠️ You are **€{abs(remaining):.2f} over budget**. "
            "Consider removing a meal or choosing a cheaper recipe."
        )
    elif remaining < budget * 0.1:
        st.warning(f"📊 Almost at your limit — only **€{remaining:.2f}** remaining.")
    else:
        st.success(f"✅ Great job! You have **€{remaining:.2f}** left in your weekly budget.")


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION & MAIN
# ══════════════════════════════════════════════════════════════════════════════

PAGES = {
    "🏠  Dashboard":     show_dashboard,
    "🍽️  Recipes":       show_recipes,
    "🫙  Pantry":        show_pantry,
    "🗓️  Meal Planner":  show_meal_planner,
    "🛒  Grocery List":  show_grocery_list,
    "💡  Suggestions":   show_suggestions,
    "💳  Budget":        show_budget,
}


def main() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(_JS, unsafe_allow_html=True)
    init_state()

    with st.sidebar:
        st.markdown("## Smart Meal Planner")
        st.markdown("---")

        page = st.radio(
            "Navigate",
            list(PAGES.keys()),
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Quick stats
        recipes  = st.session_state.recipes
        pantry   = st.session_state.pantry
        expiring = get_expiring_items(pantry)
        expired  = get_expired_items(pantry)

        st.caption(f"{len(recipes)} recipe{'s' if len(recipes) != 1 else ''}")
        st.caption(f"{len(pantry)} pantry item{'s' if len(pantry) != 1 else ''}")

        if expired:
            st.caption(f"{len(expired)} expired item{'s' if len(expired) != 1 else ''}")
        if expiring:
            st.caption(f"{len(expiring)} expiring soon")

    PAGES[page]()


if __name__ == "__main__":
    main()
