import json
import os

from models.recipe import Recipe
from models.pantry_item import PantryItem
from models.meal_plan import MealPlan

# Resolve the data directory relative to this file's location
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_BASE_DIR, "data")

_RECIPES_FILE = os.path.join(DATA_DIR, "recipes.json")
_SAMPLE_FILE = os.path.join(DATA_DIR, "sample_recipes.json")
_PANTRY_FILE = os.path.join(DATA_DIR, "pantry.json")
_MEAL_PLAN_FILE = os.path.join(DATA_DIR, "meal_plan.json")
_BUDGET_FILE = os.path.join(DATA_DIR, "budget.json")


# ── Low-level helpers ──────────────────────────────────────────────────────────

def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_json(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(filepath: str, data: dict) -> None:
    _ensure_data_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Recipes ────────────────────────────────────────────────────────────────────

def load_recipes() -> dict:
    """
    Load recipes from JSON.
    On first run (no recipes.json), fall back to the bundled sample recipes.
    Returns a dict of {recipe_id: Recipe}.
    """
    if not os.path.exists(_RECIPES_FILE):
        raw = _load_json(_SAMPLE_FILE)
    else:
        raw = _load_json(_RECIPES_FILE)
    return {rid: Recipe.from_dict(r) for rid, r in raw.items()}


def save_recipes(recipes: dict) -> None:
    _save_json(_RECIPES_FILE, {rid: r.to_dict() for rid, r in recipes.items()})


# ── Pantry ─────────────────────────────────────────────────────────────────────

def load_pantry() -> dict:
    """Returns a dict of {item_id: PantryItem}."""
    raw = _load_json(_PANTRY_FILE)
    return {pid: PantryItem.from_dict(p) for pid, p in raw.items()}


def save_pantry(pantry: dict) -> None:
    _save_json(_PANTRY_FILE, {pid: p.to_dict() for pid, p in pantry.items()})


# ── Meal Plan ──────────────────────────────────────────────────────────────────

def load_meal_plan() -> MealPlan:
    raw = _load_json(_MEAL_PLAN_FILE)
    if not raw:
        return MealPlan()
    return MealPlan.from_dict(raw)


def save_meal_plan(meal_plan: MealPlan) -> None:
    _save_json(_MEAL_PLAN_FILE, meal_plan.to_dict())


# ── Budget ─────────────────────────────────────────────────────────────────────

def load_budget() -> float:
    raw = _load_json(_BUDGET_FILE)
    return float(raw.get("weekly_budget", 100.0))


def save_budget(budget: float) -> None:
    _save_json(_BUDGET_FILE, {"weekly_budget": budget})
