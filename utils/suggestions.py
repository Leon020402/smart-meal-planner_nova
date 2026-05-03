from models.pantry_item import PantryItem
from models.recipe import Recipe


def suggest_recipes_by_pantry(
    pantry: dict,
    recipes: dict,
    min_match_ratio: float = 0.5,
) -> list:
    """
    Suggest recipes based on the ingredients currently available in the pantry.

    Only non-expired pantry items are considered.
    Returns a list of suggestion dicts sorted by match ratio (descending):
        {
            "recipe":       Recipe,
            "match_ratio":  float,     # 0.0 – 1.0
            "matched":      set,       # ingredient names in both pantry and recipe
            "missing":      set,       # ingredient names not in pantry
        }
    """
    # Build a set of available (non-expired) ingredient names
    available = {
        item.name.lower().strip()
        for item in pantry.values()
        if not item.is_expired()
    }

    suggestions = []
    for recipe_id, recipe in recipes.items():
        required = set(recipe.get_ingredient_names())
        if not required:
            continue
        matched = required & available
        ratio = len(matched) / len(required)
        if ratio >= min_match_ratio:
            suggestions.append({
                "recipe": recipe,
                "match_ratio": ratio,
                "matched": matched,
                "missing": required - available,
            })

    suggestions.sort(key=lambda x: x["match_ratio"], reverse=True)
    return suggestions


def suggest_recipes_for_expiring(pantry: dict, recipes: dict) -> list:
    """
    Return recipes that use one or more ingredients expiring soon.

    Returns a list of suggestion dicts sorted by the number of expiring
    ingredients used (descending):
        {
            "recipe":        Recipe,
            "uses_expiring": set,   # expiring ingredient names used by recipe
            "missing":       set,   # required ingredients not available in pantry
        }
    """
    expiring = {
        item.name.lower().strip()
        for item in pantry.values()
        if item.is_expiring_soon() and not item.is_expired()
    }

    if not expiring:
        return []

    # All non-expired pantry items (for missing-ingredient calculation)
    available = {
        item.name.lower().strip()
        for item in pantry.values()
        if not item.is_expired()
    }

    suggestions = []
    for recipe_id, recipe in recipes.items():
        required = set(recipe.get_ingredient_names())
        overlap = required & expiring
        if overlap:
            suggestions.append({
                "recipe": recipe,
                "uses_expiring": overlap,
                "missing": required - available,
            })

    suggestions.sort(key=lambda x: len(x["uses_expiring"]), reverse=True)
    return suggestions
