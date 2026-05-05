from models.meal_plan import MealPlan
from models.recipe import Recipe
from models.pantry_item import PantryItem

# ── Unit conversion table ──────────────────────────────────────────────────────
# All units are normalised to lowercase before lookup — no duplicates needed.
# Maps (from_unit, to_unit) -> conversion factor
_CONVERSIONS = {
    ("kg", "g"):  1000.0,
    ("g",  "kg"): 0.001,
    ("l",  "ml"): 1000.0,
    ("ml", "l"):  0.001,
}


def _normalise_unit(unit: str) -> str:
    """Normalise unit to lowercase and strip whitespace for consistent comparison."""
    return unit.strip().lower()


def _convert(quantity: float, from_unit: str, to_unit: str):
    """
    Try to convert quantity from from_unit to to_unit.
    Both units are normalised before lookup.
    Returns converted quantity if conversion is possible, otherwise None.
    """
    factor = _CONVERSIONS.get((_normalise_unit(from_unit), _normalise_unit(to_unit)))
    if factor is not None:
        return quantity * factor
    return None


def generate_grocery_list(
    meal_plan: MealPlan,
    recipes: dict,
    pantry: dict,
) -> list:
    """
    Compare the ingredients required by planned meals against pantry contents.

    Returns a sorted list of dicts, each describing an item that needs to be
    purchased:
        {
            "name":     str,          # title-cased ingredient name
            "quantity": float,        # amount needed
            "unit":     str,
            "status":   str,          # "missing" | "partial" | "unit_mismatch"
            "note":     str | None,   # extra info for unit_mismatch
        }
    """
    # ── Step 1: Aggregate all ingredient quantities from planned recipes ───────
    needed: dict = {}   # (name, unit) -> quantity

    recipe_counts = meal_plan.get_recipe_id_counts()

    for recipe_id, count in recipe_counts.items():
        recipe = recipes.get(recipe_id)
        if recipe is None:
            continue
        for ing in recipe.ingredients:
            name = ing["name"].lower().strip()
            qty  = float(ing.get("quantity", 0)) * count
            unit = _normalise_unit(ing.get("unit", ""))
            key  = (name, unit)
            needed[key] = needed.get(key, 0) + qty

    # ── Step 2: Build a pantry lookup, aggregating by (name, unit) ───────────
    # Handles duplicate pantry entries (e.g. two "spaghetti" entries = summed)
    pantry_lookup: dict = {}   # (name, unit) -> total quantity
    for item in pantry.values():
        if item.is_expired():
            continue
        key = (item.name.lower().strip(), _normalise_unit(item.unit))
        pantry_lookup[key] = pantry_lookup.get(key, 0) + item.quantity

    # ── Step 3: Determine what is missing or insufficient ────────────────────
    grocery_list = []

    for (name, needed_unit), needed_qty in needed.items():

        # Sum ALL pantry quantities for this ingredient in the needed unit
        # (includes exact matches + all convertible units)
        total_available = 0.0
        has_any_pantry  = False
        incompatible_entries = []  # (qty, unit) where conversion is impossible

        for (pname, punit), pqty in pantry_lookup.items():
            if pname != name:
                continue
            has_any_pantry = True
            if punit == needed_unit:
                # Exact match — add directly
                total_available += pqty
            else:
                converted = _convert(pqty, punit, needed_unit)
                if converted is not None:
                    # Convertible — add in needed unit
                    total_available += converted
                else:
                    # Incompatible unit — record for mismatch warning
                    incompatible_entries.append((pqty, punit))

        if not has_any_pantry:
            # Not in pantry at all
            grocery_list.append({
                "name": name.title(),
                "quantity": round(needed_qty, 2),
                "unit": needed_unit,
                "status": "missing",
                "note": None,
            })
        else:
            missing_qty = needed_qty - total_available
            if missing_qty > 0:
                if incompatible_entries and total_available == 0.0:
                    # Only incompatible units available — flag as mismatch
                    note_parts = ", ".join(f"{q} {u}" for q, u in incompatible_entries)
                    grocery_list.append({
                        "name": name.title(),
                        "quantity": round(needed_qty, 2),
                        "unit": needed_unit,
                        "status": "unit_mismatch",
                        "note": f"Pantry has {note_parts} — cannot auto-convert",
                    })
                else:
                    grocery_list.append({
                        "name": name.title(),
                        "quantity": round(missing_qty, 2),
                        "unit": needed_unit,
                        "status": "partial",
                        "note": None,
                    })
            # else: enough in pantry — nothing to add

    grocery_list.sort(key=lambda x: x["name"])
    return grocery_list
