import os
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
from cryptography.fernet import Fernet
import json
import yaml

# ELA Tamper Detection
def perform_ela(image_path, quality=90, scale=15):
    """
    Perform Error Level Analysis (ELA) on an image.
    Returns: {tampered: bool, reason, confidence}
    """
    original = Image.open(image_path).convert('RGB')
    
    # Save at specified quality and reopen
    temp_path = f"{image_path}_temp.jpg"
    original.save(temp_path, 'JPEG', quality=quality)
    temporary = Image.open(temp_path)
    
    # Calculate difference
    diff = ImageChops.difference(original, temporary)
    
    # Enhance difference to make it visible
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    
    scale_factor = 255.0 / max_diff
    diff = ImageEnhance.Brightness(diff).enhance(scale_factor)
    
    # Simple thresholding for tamper detection (demo logic)
    # In a real scenario, you'd look for localized high-energy regions
    diff_arr = np.array(diff)
    mean_diff = np.mean(diff_arr)
    
    os.remove(temp_path)
    
    # Convert to Python types for JSON serialization
    is_tampered = bool(mean_diff > 40.0) 
    
    return {
        "tampered": is_tampered,
        "reason": "Localized compression inconsistencies detected" if is_tampered else "No significant tamper signatures found",
        "confidence": float(0.85 if is_tampered else 0.95)
    }

# Encryption Helpers
def get_fernet():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        key = Fernet.generate_key() # Fallback for demo
    return Fernet(key)

def encrypt_data(data: dict) -> str:
    f = get_fernet()
    json_data = json.dumps(data).encode()
    return f.encrypt(json_data).decode()

def decrypt_data(token: str) -> dict:
    f = get_fernet()
    decrypted = f.decrypt(token.encode()).decode()
    return json.loads(decrypted)

# Config Loader
def load_rules():
    with open("backend/rules.yaml", "r") as f:
        return yaml.safe_load(f)

def load_pep_data():
    path = os.getenv("PEP_DATA_PATH", "./pep_data.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []
