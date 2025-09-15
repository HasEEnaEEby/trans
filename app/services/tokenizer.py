from typing import List
from app.core.config import settings
from app.utils.logging import logger

try:
    from fugashi import Tagger  # type: ignore
except Exception:  # pragma: no cover
    Tagger = None  # type: ignore


class TokenizerService:
    def __init__(self) -> None:
        self.mock = settings.use_mock_mode
        if not self.mock and Tagger is not None:
            try:
                self.tagger = Tagger()
            except Exception as exc:  # pragma: no cover
                logger.warning("mecab_init_failed", error=str(exc))
                self.mock = True
        else:
            self.tagger = None

    def tokenize(self, text: str) -> List[str]:
        if self.mock or self.tagger is None:
            return text.split()
        return [word.surface for word in self.tagger(text)]
