from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ✅ BUNU EKLE

from .schemas import SearchRequest, SearchResponse, RecipeResult
from .normalize import tokenize_query
from .recipe_store import RecipeStore
from .ingredient_mapper import IngredientMapper

app = FastAPI(title="Food Match API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

store: RecipeStore | None = None
mapper: IngredientMapper | None = None


@app.on_event("startup")
def startup():
    global store, mapper

    recipes_path = os.getenv("RECIPES_PATH", "data/recipes.json")
    store = RecipeStore.from_json_file(recipes_path)

    vocab = store.unique_ingredients()
    # Embedding ile dinamik TR->EN: ING_USE_EMBEDDINGS=0 yaparsan kapatır1
    use_embeddings = os.getenv("ING_USE_EMBEDDINGS", "1") != "0"
    mapper = IngredientMapper(vocab=vocab, use_embeddings=use_embeddings)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    assert store is not None and mapper is not None

    tokens = tokenize_query(req.query_raw)
    debug_items, mapped_list = mapper.map_many(tokens, min_score=req.min_score)

    required = set(mapped_list)

    # 1) strict araması
    results = store.search(required=required, limit=req.limit, mode=req.mode, min_matches=req.min_matches)

    note = None

    # 2) strict 0 ise otomatik relaxed fallback (menemen beklentisi için kritik)
    if req.mode == "strict" and len(results) == 0 and len(required) >= 2:
        fallback_min_matches = req.min_matches if req.min_matches is not None else max(1, len(required) - 1)
        results = store.search(required=required, limit=req.limit, mode="relaxed", min_matches=fallback_min_matches)
        note = f"Strict sonuç 0 olduğu için relaxed fallback çalıştı (min_matches={fallback_min_matches}). " \
               f"Dataset'te tüm malzemeleri aynı anda içeren tarif olmayabilir."

    return SearchResponse(
        query_raw=req.query_raw,
        query_tokens=tokens,
        query_mapped=mapped_list,
        mapped_debug=[{"from": x.from_token, "to": x.to, "score": x.score} for x in debug_items],
        mode=req.mode if note is None else "relaxed",
        count=len(results),
        results=[
            RecipeResult(
                name=r.name,
                category=r.category,
                matched=matched,
                missing=missing,
                ingredients=r.ingredients_raw,
            )
            for (r, matched, missing) in results
        ],
        note=note,
    )
