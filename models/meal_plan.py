class MealPlan:
    """Represents a weekly meal plan mapping (day, meal_type) to recipe IDs."""

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    MEAL_TYPES = ["Breakfast", "Lunch", "Dinner"]

    def __init__(self):
        # plan[day][meal_type] = recipe_id (str) or None
        self.plan = {
            day: {meal: None for meal in self.MEAL_TYPES}
            for day in self.DAYS
        }

    # ── Mutations ──────────────────────────────────────────────────────────────

    def assign_recipe(self, day: str, meal_type: str, recipe_id: str) -> None:
        """Assign a recipe to a specific slot."""
        if day in self.plan and meal_type in self.plan[day]:
            self.plan[day][meal_type] = recipe_id

    def remove_recipe(self, day: str, meal_type: str) -> None:
        """Clear a specific slot."""
        if day in self.plan and meal_type in self.plan[day]:
            self.plan[day][meal_type] = None

    def clear_recipe_id(self, recipe_id: str) -> None:
        """Remove all occurrences of a recipe ID from the plan."""
        for day in self.DAYS:
            for meal in self.MEAL_TYPES:
                if self.plan[day][meal] == recipe_id:
                    self.plan[day][meal] = None

    # ── Queries ────────────────────────────────────────────────────────────────

    def get_all_recipe_ids(self) -> list:
        """Return a deduplicated list of all planned recipe IDs."""
        seen = []
        for day in self.DAYS:
            for meal in self.MEAL_TYPES:
                rid = self.plan[day][meal]
                if rid and rid not in seen:
                    seen.append(rid)
        return seen

    def get_recipe_id_counts(self) -> dict:
        """Return a dict of {recipe_id: count} for all planned meals."""
        counts = {}
        for day in self.DAYS:
            for meal in self.MEAL_TYPES:
                rid = self.plan[day][meal]
                if rid:
                    counts[rid] = counts.get(rid, 0) + 1
        return counts

    def get_total_meals(self) -> int:
        """Return the total number of assigned meals."""
        return sum(
            1
            for day in self.DAYS
            for meal in self.MEAL_TYPES
            if self.plan[day][meal] is not None
        )

    # ── Serialisation ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {"plan": self.plan}

    @classmethod
    def from_dict(cls, data: dict) -> "MealPlan":
        mp = cls()
        loaded = data.get("plan", {})
        for day in cls.DAYS:
            if day in loaded:
                for meal in cls.MEAL_TYPES:
                    mp.plan[day][meal] = loaded[day].get(meal)
        return mp

    def __repr__(self) -> str:
        return f"MealPlan(meals_planned={self.get_total_meals()})"
