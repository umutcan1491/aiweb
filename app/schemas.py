from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


Mode = Literal["strict", "relaxed"]


class SearchRequest(BaseModel):
    query_raw: str = Field(..., examples=["soğan yumurta biber"])
    mode: Mode = "strict"

    # mapping kalitesi için
    min_score: float = 0.55

    # sonuç kontrolü
    limit: int = 10

    # relaxed mod için: en az kaç ingredient eşleşsin
    min_matches: Optional[int] = None


class MapDebugItem(BaseModel):
    from_token: str = Field(..., alias="from")
    to: str
    score: float


class RecipeResult(BaseModel):
    name: str
    category: str
    matched: List[str]
    missing: List[str]
    ingredients: List[str]


class SearchResponse(BaseModel):
    query_raw: str
    query_tokens: List[str]
    query_mapped: List[str]
    mapped_debug: List[MapDebugItem]
    mode: Mode
    count: int
    results: List[RecipeResult]
    note: Optional[str] = None
