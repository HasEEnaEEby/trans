from typing import Optional
from app.core.config import settings
from app.utils.logging import logger

try:
    import easyocr  # type: ignore
except Exception:  # pragma: no cover
    easyocr = None


class OcrService:
    def __init__(self) -> None:
        self.mock = settings.use_mock_mode
        self.reader: Optional["easyocr.Reader"] = None
        if not self.mock and easyocr is not None:
            try:
                self.reader = easyocr.Reader(["ja", "en"], gpu=False)
                logger.info("easyocr_initialized", langs=["ja", "en"]) 
            except Exception as exc:  # pragma: no cover
                logger.warning("easyocr_init_failed", error=str(exc))
                self.mock = True
        else:
            logger.info("ocr_mock_mode_enabled")

    def extract_text(self, image_bytes: bytes) -> str:
        if self.mock or self.reader is None:
            return "青いスカート ¥5,000。今週のセール！"
        try:
            result = self.reader.readtext(image_bytes, detail=0, paragraph=True)
            return "\n".join(result)
        except Exception as exc:  # pragma: no cover
            logger.error("ocr_failed", error=str(exc))
            return ""
