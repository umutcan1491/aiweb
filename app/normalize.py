from __future__ import annotations

import re
from typing import List


_SPLIT_RE = re.compile(r"[,\n;]+")


def tokenize_query(q: str) -> List[str]:
    """
    'soğan yumurta, biber; domates' -> ['soğan', 'yumurta', 'biber', 'domates']
    """
    q = q.strip().lower()
    if not q:
        return []
    # önce , ; \n ile böl
    parts = []
    for chunk in _SPLIT_RE.split(q):
        chunk = chunk.strip()
        if not chunk:
            continue
        # chunk içinde boşlukla ayrılanları da al
        parts.extend([t for t in chunk.split() if t.strip()])
    # tekrarları temizle (sıra koruyarak)
    seen = set()
    out = []
    for t in parts:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def normalize_ingredient_text(s: str) -> str:
    """
    Dataset içindeki EN ingredient’leri canonical hale getirir.
    Amaç: 'red onions' / 'onions' -> 'onion', 'egg yolks' -> 'egg',
          'romano pepper' / 'green pepper' / 'pepper' -> 'pepper',
          'aubergine' / 'egg plants' -> 'eggplant'
    """
    x = s.strip().lower()

    # egg family
    if "egg" in x:
        return "egg"

    # onion family
    if "onion" in x:
        return "onion"

    # pepper family (romano pepper / green pepper / pepper / pul biber vb.)
    if "pepper" in x or "biber" in x:
        return "pepper"

    # eggplant family
    if "aubergine" in x or "egg plant" in x or "eggplant" in x:
        return "eggplant"

    # çok temel çoğul kırpma (potatoes -> potato gibi)
    # (abartmıyoruz, en azından 's' ile bitenleri)
    if len(x) > 3 and x.endswith("s"):
        x = x[:-1]

    return x


# Hafif TR->EN küçük sözlük (devasa değil; sadece çok sık olanlar)
TR_HINTS = {
    "soğan": "onion",
    "sogan": "onion",
    "yumurta": "egg",
    "biber": "pepper",
    "patlıcan": "eggplant",
    "patlican": "eggplant",
    "domates": "tomato",
    "sarımsak": "garlic",
    "sarimsak": "garlic",
    "peynir": "cheese",
    "tuz": "salt",
    "karabiber": "pepper",
}
