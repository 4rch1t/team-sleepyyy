import logging
import io
import numpy as np
from PIL import Image, ExifTags
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class TamperResult(BaseModel):
    is_tampered: bool
    confidence: float
    reason: str

def check_tampering(image_bytes: bytes) -> TamperResult:
    try:
        original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # 1. EXIF Check
        exif = original.getexif()
        if exif:
            for tag_id, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                if tag_name == "Software" and isinstance(value, str):
                    lower_val = value.lower()
                    if any(editor in lower_val for editor in ["photoshop", "gimp", "lightroom", "snapseed"]):
                        return TamperResult(is_tampered=True, confidence=95.0, reason=f"EXIF Software tag indicates known editor: {value}")
        
        # 2. Error Level Analysis (ELA)
        resaved_buffer = io.BytesIO()
        original.save(resaved_buffer, format="JPEG", quality=90)
        resaved_buffer.seek(0)
        resaved = Image.open(resaved_buffer).convert("RGB")
        
        ela_array = np.abs(np.array(original).astype(np.float32) - np.array(resaved).astype(np.float32))
        
        # Grid 3x3
        h, w, _ = ela_array.shape
        grid_h, grid_w = h // 3, w // 3
        
        if grid_h > 0 and grid_w > 0:
            for row in range(3):
                for col in range(3):
                    cell = ela_array[row*grid_h:(row+1)*grid_h, col*grid_w:(col+1)*grid_w]
                    mean_error = float(np.mean(cell))
                    if mean_error > 15.0:
                        reason = f"ELA anomaly detected in region {row},{col} — mean error {mean_error:.2f}. Consistent with localised image editing."
                        return TamperResult(is_tampered=True, confidence=87.0, reason=reason)

        return TamperResult(is_tampered=False, confidence=1.0, reason="No anomalies detected")
        
    except Exception as e:
        logger.exception("Error during tamper detection")
        raise
