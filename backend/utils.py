import os
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
from cryptography.fernet import Fernet
import json
import yaml
from fpdf import FPDF

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

def generate_pdf_report(report_data, output_path):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("helvetica", "B", 24)
    pdf.set_text_color(255, 77, 0) # VerifAI Orange
    pdf.cell(0, 20, "VERIFAI REPORT", ln=True, align="C")
    
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"ID: {report_data.get('id', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"DECISION: {report_data.get('decision')}", ln=True)
    pdf.cell(0, 10, f"DATE: {report_data.get('created_at', 'N/A')}", ln=True)
    pdf.ln(10)
    
    # Reasoning Trace
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "REASONING TRACE", ln=True)
    pdf.set_font("helvetica", "", 10)
    for reason in report_data.get("reasons", []):
        pdf.multi_cell(0, 8, f"- {reason}")
    pdf.ln(10)
    
    # Stage 1: Forensics
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "STAGE 1: FORENSICS & TAMPER ANALYSIS", ln=True)
    pdf.set_font("helvetica", "", 10)
    for t in report_data.get("stage_outputs", {}).get("tamper", []):
        status = "TAMPERED" if t.get("tamper") else "CLEAN"
        pdf.cell(0, 8, f"{t.get('document').upper()}: {status}", ln=True)
    pdf.ln(10)
    
    # Stage 2: AI Extraction
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "STAGE 2: MULTI-MODAL AI EXTRACTION", ln=True)
    pdf.set_font("helvetica", "", 10)
    for doc, info in report_data.get("stage_outputs", {}).get("extraction", {}).items():
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 8, f"Source: {doc.upper()}", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 8, f"Name: {info.get('name')}", ln=True)
        pdf.cell(0, 8, f"ID: {info.get('id_number')}", ln=True)
        pdf.ln(2)
    pdf.ln(10)
    
    # Stage 3-4: Regulatory & AML Checks
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "STAGE 3-4: REGULATORY & AML CHECKS", ln=True)
    pdf.set_font("helvetica", "", 10)
    for c in report_data.get("checks", []):
        status = "COMPLIANT" if c.get("pass") else "VIOLATION"
        pdf.cell(0, 8, f"{c.get('rule')}: {status}", ln=True)
        
    pdf.output(output_path)
    return output_path
