import asyncio
import io
import logging

log = logging.getLogger("background-pingu")

try:
    from PIL import Image
    import pytesseract
    _ocr_available = True
except ImportError:
    _ocr_available = False

_IMAGE_TYPES = ("image/png", "image/jpeg", "image/webp")
_MAX_IMAGE_BYTES = 8 * 1024 * 1024


async def extract_text(message) -> str:
    if not _ocr_available:
        return ""

    images = [
        a for a in message.attachments
        if a.content_type and a.content_type in _IMAGE_TYPES
        and a.size <= _MAX_IMAGE_BYTES
    ]
    if not images:
        return ""

    parts: list[str] = []
    for attachment in images[:2]:
        try:
            data = await attachment.read()
            text = await asyncio.to_thread(_run_ocr, data)
            if text:
                log.info("OCR %s: %s", attachment.filename, text[:120])
                parts.append(text)
            else:
                log.info("OCR %s: empty result", attachment.filename)
        except Exception:
            log.warning("OCR failed for %s", attachment.filename, exc_info=True)
    return " ".join(parts)


def _run_ocr(data: bytes) -> str:
    img = Image.open(io.BytesIO(data))
    return pytesseract.image_to_string(img, timeout=5).strip()
