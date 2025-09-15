from typing import Optional
from app.core.config import settings
from app.utils.logging import logger

try:
    from transformers import MarianMTModel, MarianTokenizer  # type: ignore
    import torch  # type: ignore
except Exception:  # pragma: no cover
    MarianMTModel = None  # type: ignore
    MarianTokenizer = None  # type: ignore
    torch = None  # type: ignore


class TranslationService:
    def __init__(self) -> None:
        self.mock = settings.use_mock_mode or (MarianMTModel is None)
        self.model: Optional["MarianMTModel"] = None
        self.tokenizer: Optional["MarianTokenizer"] = None
        if not self.mock:
            try:
                self.tokenizer = MarianTokenizer.from_pretrained(settings.translation_model)
                self.model = MarianMTModel.from_pretrained(settings.translation_model)
            except Exception as exc:  # pragma: no cover
                logger.warning("translation_model_init_failed", error=str(exc))
                self.mock = True
        else:
            logger.info("translation_mock_mode_enabled")

    def translate(self, text: str, src_lang: str = "ja", tgt_lang: str = "en") -> str:
        if self.mock or self.model is None or self.tokenizer is None:
            return "Blue skirt ¥5,000. Sale this week!"
        inputs = self.tokenizer(text, return_tensors="pt", padding=True)
        with torch.no_grad():  # type: ignore
            outputs = self.model.generate(**inputs, max_new_tokens=256)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
