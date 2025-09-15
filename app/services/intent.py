from typing import List
from app.core.config import settings


INTENT_LABELS = ["product", "recipe", "event", "advertisement", "article"]


class IntentService:
    def __init__(self) -> None:
        self.mock = settings.use_mock_mode
        # Placeholder for model; for now mock scoring

    def predict(self, text: str, top_k: int = 3) -> List[tuple[str, float]]:
        # Simple heuristic mock: if price symbol present => product/advertisement
        scores = []
        base = {
            "product": 0.2,
            "recipe": 0.1,
            "event": 0.1,
            "advertisement": 0.2,
            "article": 0.1,
        }
        if "¥" in text or "$" in text:
            base["product"] += 0.4
            base["advertisement"] += 0.2
        if any(k in text for k in ["イベント", "開催", "ticket", "event"]):
            base["event"] += 0.4
        ranked = sorted(base.items(), key=lambda x: x[1], reverse=True)
        return ranked[: max(1, min(top_k, len(ranked)))]
