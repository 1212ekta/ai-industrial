"""OCR service — wraps PaddleOCR for scanned PDFs and image uploads.

The PaddleOCR engine is lazily instantiated (and cached) since model
loading is expensive and not every document needs it.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.logging import logger


@lru_cache(maxsize=1)
def _get_ocr_engine():
    from paddleocr import PaddleOCR

    return PaddleOCR(use_angle_cls=True, lang="en", show_log=False)


class OCRService:
    def extract_text_from_file(self, file_path: str) -> str:
        try:
            engine = _get_ocr_engine()
            result = engine.ocr(file_path, cls=True)
            return self._flatten_result(result)
        except Exception as exc:
            logger.error(f"OCR failed for {file_path}: {exc}")
            return ""

    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        import numpy as np
        from PIL import Image
        import io

        try:
            engine = _get_ocr_engine()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            arr = np.array(image)
            result = engine.ocr(arr, cls=True)
            return self._flatten_result(result)
        except Exception as exc:
            logger.error(f"OCR (in-memory) failed: {exc}")
            return ""

    @staticmethod
    def _flatten_result(result) -> str:
        if not result:
            return ""
        lines = []
        for block in result:
            if not block:
                continue
            for line in block:
                # line = [box, (text, confidence)]
                try:
                    lines.append(line[1][0])
                except (IndexError, TypeError):
                    continue
        return "\n".join(lines)
