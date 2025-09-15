import re
from typing import List
from app.core.config import settings
from app.models.schemas import Entity


PRICE_RE = re.compile(r"([¥$]\s?\d{1,3}(?:[\,\.]\d{3})*(?:\.\d{2})?)")
URL_RE = re.compile(r"https?://\S+")


class NerService:
    def __init__(self) -> None:
        self.mock = settings.use_mock_mode

    def extract(self, text: str) -> List[Entity]:
        entities: List[Entity] = []
        for m in PRICE_RE.finditer(text):
            price_text = m.group(1)
            value = None
            digits = re.sub(r"[^0-9.]", "", price_text.replace(",", ""))
            try:
                value = float(digits)
            except Exception:
                value = None
            entities.append(
                Entity(type="PRICE", text=price_text, start=m.start(), end=m.end(), confidence=0.9, value=value, currency="JPY" if "¥" in price_text else None)
            )
        for m in URL_RE.finditer(text):
            entities.append(Entity(type="URL", text=m.group(0), start=m.start(), end=m.end(), confidence=0.9))
        # naive guessing garnae: first noun-like token heuristic in mock
        if "スカート" in text:
            idx = text.find("スカート")
            entities.append(Entity(type="PRODUCT", text="スカート", start=idx, end=idx + 4, confidence=0.8))
        if "skirt" in text.lower():
            idx = text.lower().find("skirt")
            entities.append(Entity(type="PRODUCT", text=text[idx:idx+5], start=idx, end=idx + 5, confidence=0.8))
        return entities
