from models.meal_plan import MealPlan
from models.recipe import Recipe
from models.pantry_item import PantryItem


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
    needed: dict = {}   # name -> {"quantity": float, "unit": str}

    for recipe_id in meal_plan.get_all_recipe_ids():
        recipe = recipes.get(recipe_id)
        if recipe is None:
            continue  # recipe was deleted after planning — skip gracefully
        for ing in recipe.ingredients:
            name = ing["name"].lower().strip()
            qty = float(ing.get("quantity", 0))
            unit = ing.get("unit", "")
            if name in needed and needed[name]["unit"] == unit:
                needed[name]["quantity"] += qty
            else:
                # First occurrence or different unit — store as new entry
                needed[name] = {"quantity": qty, "unit": unit}

    # ── Step 2: Build a pantry lookup, excluding expired items ────────────────
    pantry_lookup: dict = {
        item.name.lower().strip(): item
        for item in pantry.values()
        if not item.is_expired()
    }

    # ── Step 3: Determine what is missing or insufficient ────────────────────
    grocery_list = []

    for name, details in needed.items():
        needed_qty = details["quantity"]
        needed_unit = details["unit"]

        if name in pantry_lookup:
            pantry_item = pantry_lookup[name]
            if pantry_item.unit == needed_unit:
                # Same unit — check if we have enough
                missing_qty = needed_qty - pantry_item.quantity
                if missing_qty > 0:
                    grocery_list.append({
                        "name": name.title(),
                        "quantity": round(missing_qty, 2),
                        "unit": needed_unit,
                        "status": "partial",
                        "note": None,
                    })
                # else: pantry has enough — no action needed
            else:
                # Units differ — flag for the user and add the full required amount
                grocery_list.append({
                    "name": name.title(),
                    "quantity": round(needed_qty, 2),
                    "unit": needed_unit,
                    "status": "unit_mismatch",
                    "note": f"Pantry has {pantry_item.quantity} {pantry_item.unit}",
                })
        else:
            # Not in pantry at all
            grocery_list.append({
                "name": name.title(),
                "quantity": round(needed_qty, 2),
                "unit": needed_unit,
                "status": "missing",
                "note": None,
            })

    grocery_list.sort(key=lambda x: x["name"])
    return grocery_list
