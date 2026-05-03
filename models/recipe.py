import uuid


class Recipe:
    """Represents a recipe with ingredients, preparation info, and metadata."""

    DIETARY_OPTIONS = ["Vegetarian", "Vegan", "High-Protein", "Low-Cost", "Quick", "Gluten-Free"]
    CATEGORY_OPTIONS = ["Italian", "Asian", "Mexican", "Mediterranean", "American", "Indian", "French", "Other"]

    def __init__(
        self,
        name: str,
        ingredients: list,
        prep_time: int,
        category: str,
        dietary_types: list,
        estimated_cost: float,
        instructions: str,
        recipe_id: str = None,
    ):
        self.id = recipe_id if recipe_id else str(uuid.uuid4())
        self.name = name
        self.ingredients = ingredients       # list of dicts: {name, quantity, unit}
        self.prep_time = int(prep_time)      # minutes
        self.category = category
        self.dietary_types = dietary_types   # list of strings
        self.estimated_cost = float(estimated_cost)
        self.instructions = instructions

    # ── Serialisation ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "ingredients": self.ingredients,
            "prep_time": self.prep_time,
            "category": self.category,
            "dietary_types": self.dietary_types,
            "estimated_cost": self.estimated_cost,
            "instructions": self.instructions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Recipe":
        return cls(
            name=data["name"],
            ingredients=data.get("ingredients", []),
            prep_time=data.get("prep_time", 20),
            category=data.get("category", "Other"),
            dietary_types=data.get("dietary_types", []),
            estimated_cost=data.get("estimated_cost", 0.0),
            instructions=data.get("instructions", ""),
            recipe_id=data.get("id"),
        )

    # ── Helpers ────────────────────────────────────────────────────────────────

    def get_ingredient_names(self) -> list:
        """Return a lowercase list of ingredient names."""
        return [ing["name"].lower().strip() for ing in self.ingredients]

    def matches_dietary_filter(self, filters: list) -> bool:
        """Return True if the recipe satisfies all selected dietary filters."""
        if not filters:
            return True
        recipe_lower = [dt.lower() for dt in self.dietary_types]
        return all(f.lower() in recipe_lower for f in filters)

    def is_quick(self) -> bool:
        return self.prep_time <= 30

    def __repr__(self) -> str:
        return f"Recipe(name={self.name!r}, category={self.category!r})"
