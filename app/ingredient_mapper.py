from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from rapidfuzz import fuzz, process

from .normalize import TR_HINTS, normalize_ingredient_text


@dataclass
class MapItem:
    from_token: str
    to: str
    score: float


class IngredientMapper:
    """
    1) Önce küçük TR_HINTS ile hızlı yakala (soğan->onion gibi)
    2) Sonra sentence-transformers varsa multilingual embedding ile en yakını bul
    3) En son fallback: rapidfuzz (EN token yazıldıysa işe yarar)
    """

    def __init__(self, vocab: List[str], use_embeddings: bool = True):
        self.vocab = sorted(set([normalize_ingredient_text(v) for v in vocab]))
        self.use_embeddings = use_embeddings

        self._model = None
        self._vocab_emb = None

        if self.use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                # Küçük ve multilingual bir model (TR dahil)
                self._model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
                self._vocab_emb = self._encode(self.vocab)
            except Exception:
                # embeddings yoksa fuzzy'ye düşer
                self._model = None
                self._vocab_emb = None
                self.use_embeddings = False

    def _encode(self, texts: List[str]) -> np.ndarray:
        emb = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(emb, dtype=np.float32)

    def _best_by_embeddings(self, token: str) -> Tuple[str, float]:
        q = normalize_ingredient_text(token)
        q_emb = self._encode([q])[0]  # (d,)
        sims = np.dot(self._vocab_emb, q_emb)  # cosine (normalize edildi)
        idx = int(np.argmax(sims))
        score = float(sims[idx])
        return self.vocab[idx], score

    def _best_by_fuzzy(self, token: str) -> Tuple[str, float]:
        q = normalize_ingredient_text(token)
        hit = process.extractOne(q, self.vocab, scorer=fuzz.WRatio)
        if not hit:
            return q, 0.0
        choice, score, _ = hit
        return choice, float(score) / 100.0

    def map_one(self, token: str) -> Tuple[str, float]:
        t = token.strip().lower()
        if not t:
            return "", 0.0

        # TR hızlı ipucu
        if t in TR_HINTS:
            return normalize_ingredient_text(TR_HINTS[t]), 1.0

        if self.use_embeddings and self._model is not None and self._vocab_emb is not None:
            return self._best_by_embeddings(t)

        return self._best_by_fuzzy(t)

    def map_many(self, tokens: List[str], min_score: float = 0.55) -> Tuple[List[MapItem], List[str]]:
        debug: List[MapItem] = []
        mapped: List[str] = []

        for tok in tokens:
            to, score = self.map_one(tok)
            if not to:
                continue
            debug.append(MapItem(from_token=tok, to=to, score=score))
            if score >= min_score:
                mapped.append(to)

        # uniq (sıra koruyarak)
        seen = set()
        out = []
        for m in mapped:
            if m not in seen:
                seen.add(m)
                out.append(m)

        return debug, out
