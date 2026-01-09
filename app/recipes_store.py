from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from .normalize import normalize_ingredient_text


@dataclass(frozen=True)
class Recipe:
    name: str
    category: str
    ingredients_raw: List[str]

    @property
    def ingredients_norm(self) -> List[str]:
        return [normalize_ingredient_text(x) for x in self.ingredients_raw]


class RecipeStore:
    def __init__(self, recipes: List[Recipe]):
        self._recipes = recipes

    @classmethod
    def from_json_file(cls, path: str | Path) -> "RecipeStore":
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))

        recipes: List[Recipe] = []
        for obj in data:
            name = obj.get("name", "").strip()
            category = obj.get("category", "").strip()
            ingredients = obj.get("ingredients", []) or []
            if not name or not isinstance(ingredients, list):
                continue
            recipes.append(Recipe(name=name, category=category, ingredients_raw=ingredients))
        return cls(recipes)

    def all(self) -> List[Recipe]:
        return self._recipes

    def unique_ingredients(self) -> List[str]:
        """
        Mapper için vocab: dataset'te geçen canonical ingredient seti
        """
        s: Set[str] = set()
        for r in self._recipes:
            for ing in r.ingredients_norm:
                s.add(ing)
        return sorted(s)

    def search(
        self,
        required: Set[str],
        limit: int,
        mode: str,
        min_matches: int | None,
    ) -> List[Tuple[Recipe, List[str], List[str]]]:
        """
        returns: (recipe, matched, missing)
        """
        results: List[Tuple[Recipe, List[str], List[str]]] = []

        if not required:
            return results

        req_list = list(required)

        for r in self._recipes:
            ing_set = set(r.ingredients_norm)
            matched = [x for x in req_list if x in ing_set]
            missing = [x for x in req_list if x not in ing_set]

            if mode == "strict":
                if not missing:
                    results.append((r, matched, missing))
            else:
                mm = min_matches if min_matches is not None else max(1, len(required) - 1)
                if len(matched) >= mm:
                    results.append((r, matched, missing))

        # Sırala: önce en çok eşleşen, sonra en az eksik
        results.sort(key=lambda t: (len(t[1]), -len(t[2])), reverse=True)
        return results[:limit]
