from models.meal_plan import MealPlan
from models.recipe import Recipe
from models.pantry_item import PantryItem

# ── Unit conversion table ──────────────────────────────────────────────────────
# Maps (from_unit, to_unit) -> conversion factor
# quantity_in_to_unit = quantity_in_from_unit * factor
_CONVERSIONS = {
    ("kg", "g"):   1000.0,
    ("g",  "kg"):  0.001,
    ("l",  "ml"):  1000.0,
    ("ml", "l"):   0.001,
    ("L",  "ml"):  1000.0,
    ("ml", "L"):   0.001,
    ("l",  "L"):   1.0,
    ("L",  "l"):   1.0,
}


def _normalise_unit(unit: str) -> str:
    """Lowercase and strip unit for comparison."""
    return unit.strip().lower()


def _convert(quantity: float, from_unit: str, to_unit: str):
    """
    Try to convert quantity from from_unit to to_unit.
    Returns (converted_quantity, to_unit) if conversion is possible,
    otherwise returns None.
    """
    factor = _CONVERSIONS.get((from_unit, to_unit))
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
            unit = ing.get("unit", "")
            key  = (name, unit)
            needed[key] = needed.get(key, 0) + qty

    # ── Step 2: Build a pantry lookup, aggregating by (name, unit) ───────────
    # Handles duplicate pantry entries (e.g. two "spaghetti" entries = summed)
    pantry_lookup: dict = {}   # (name, unit) -> total quantity
    for item in pantry.values():
        if item.is_expired():
            continue
        key = (item.name.lower().strip(), item.unit)
        pantry_lookup[key] = pantry_lookup.get(key, 0) + item.quantity

    # ── Step 3: Determine what is missing or insufficient ────────────────────
    grocery_list = []

    for (name, needed_unit), needed_qty in needed.items():
        pantry_qty = pantry_lookup.get((name, needed_unit), None)

        if pantry_qty is not None:
            # ── Exact unit match ──────────────────────────────────────────────
            missing_qty = needed_qty - pantry_qty
            if missing_qty > 0:
                grocery_list.append({
                    "name": name.title(),
                    "quantity": round(missing_qty, 2),
                    "unit": needed_unit,
                    "status": "partial",
                    "note": None,
                })
        else:
            # ── Look for same ingredient with a different unit ─────────────────
            converted = False
            for (pname, punit), pqty in pantry_lookup.items():
                if pname != name:
                    continue
                # Try converting pantry quantity to the needed unit
                pqty_converted = _convert(pqty, punit, needed_unit)
                if pqty_converted is not None:
                    # Conversion successful — compare in the same unit
                    missing_qty = needed_qty - pqty_converted
                    if missing_qty > 0:
                        grocery_list.append({
                            "name": name.title(),
                            "quantity": round(missing_qty, 2),
                            "unit": needed_unit,
                            "status": "partial",
                            "note": f"Pantry has {pqty} {punit} (≈ {round(pqty_converted, 2)} {needed_unit})",
                        })
                    # else: pantry has enough after conversion
                    converted = True
                    break

            if not converted:
                # Check if ingredient exists in pantry with incompatible unit
                other_unit_entry = next(
                    ((n, u) for (n, u) in pantry_lookup if n == name),
                    None
                )
                if other_unit_entry:
                    other_qty = pantry_lookup[other_unit_entry]
                    grocery_list.append({
                        "name": name.title(),
                        "quantity": round(needed_qty, 2),
                        "unit": needed_unit,
                        "status": "unit_mismatch",
                        "note": f"Pantry has {other_qty} {other_unit_entry[1]} — cannot auto-convert",
                    })
                else:
                    grocery_list.append({
                        "name": name.title(),
                        "quantity": round(needed_qty, 2),
                        "unit": needed_unit,
                        "status": "missing",
                        "note": None,
                    })

    grocery_list.sort(key=lambda x: x["name"])
    return grocery_list
