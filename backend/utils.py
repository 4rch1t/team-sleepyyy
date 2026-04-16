import os
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
from cryptography.fernet import Fernet
import json
import yaml
import base64
from fpdf import FPDF

# Image Encoding
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

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
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Dark Background for Header
        pdf.set_fill_color(10, 10, 10)
        pdf.rect(0, 0, 210, 50, "F")
        
        # Header
        pdf.set_font("helvetica", "B", 30)
        pdf.set_text_color(255, 77, 0) # VerifAI Orange
        pdf.set_xy(10, 15)
        pdf.cell(0, 15, "VERIFAI", ln=True, align="L")
        
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(150, 150, 150)
        pdf.set_xy(10, 28)
        pdf.cell(0, 10, "AI-POWERED KYC + AML DOCUMENT VERIFICATION", ln=True, align="L")
        
        # Decision Badge on Header
        decision = str(report_data.get('decision', 'REJECTED')).upper()
        if decision == "APPROVED":
            pdf.set_fill_color(0, 255, 0)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_fill_color(255, 0, 0)
            pdf.set_text_color(255, 255, 255)
            
        pdf.set_xy(150, 18)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(50, 12, decision, ln=True, align="C", fill=True)
        
        # Report Metadata
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(10, 60)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(100, 10, f"REPORT ID: {report_data.get('id', 'N/A')}", ln=False)
        pdf.cell(0, 10, f"GENERATED ON: {report_data.get('created_at', 'N/A')}", ln=True, align="R")
        
        pdf.ln(10)
        
        # Section Styling Helper
        def add_section_header(title):
            pdf.set_font("helvetica", "B", 14)
            pdf.set_text_color(255, 77, 0)
            pdf.cell(0, 10, title, ln=True)
            pdf.set_draw_color(255, 77, 0)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
            pdf.ln(5)
            pdf.set_text_color(0, 0, 0)

        # 1. PERSONAL PROFILE SUMMARY
        add_section_header("1. PERSONAL PROFILE SUMMARY")
        extraction = report_data.get("stage_outputs", {})
        if isinstance(extraction, dict):
            extraction = extraction.get("extraction", {})
        else:
            extraction = {}
            
        # Use Aadhaar as primary source for profile
        profile_data = extraction.get("aadhaar", {}) or extraction.get("pan", {}) or {}
        
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(50, 10, "PRIMARY NAME:", ln=False)
        pdf.set_font("helvetica", "", 11)
        pdf.cell(0, 10, str(profile_data.get("name", "N/A")), ln=True)
        
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(50, 10, "VERIFIED IDENTITY:", ln=False)
        pdf.set_font("helvetica", "", 11)
        pdf.cell(0, 10, str(profile_data.get("id_number", "N/A")), ln=True)
        
        pdf.ln(5)

        # 2. EXECUTIVE SUMMARY & REASONING
        add_section_header("2. AI REASONING & COMPLIANCE SUMMARY")
        pdf.set_font("helvetica", "", 11)
        for reason in report_data.get("reasons", []):
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(30, 8, "[ANALYSIS]", ln=False)
            pdf.set_font("helvetica", "", 11)
            # Use 0 for width with ln=True to move to next line correctly
            pdf.multi_cell(0, 8, str(reason), ln=True)
            pdf.ln(2)
        pdf.ln(5)
        
        # 3. STAGE 1: FORENSICS
        add_section_header("3. STAGE 1: IMAGE FORENSICS (ELA)")
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(60, 10, "DOCUMENT SOURCE", 1, 0, "C")
        pdf.cell(60, 10, "FORENSIC STATUS", 1, 0, "C")
        pdf.cell(70, 10, "RESULT", 1, 1, "C")
        
        pdf.set_font("helvetica", "", 10)
        tamper_data = report_data.get("stage_outputs", {})
        if isinstance(tamper_data, dict):
            tamper_data = tamper_data.get("tamper", [])
        else:
            tamper_data = []
            
        for t in tamper_data:
            doc = str(t.get('document', 'N/A')).upper()
            status = "TAMPERED" if t.get("tamper") else "CLEAN"
            result = "FAIL" if t.get("tamper") else "PASS"
            pdf.cell(60, 10, doc, 1, 0, "C")
            pdf.cell(60, 10, status, 1, 0, "C")
            pdf.cell(70, 10, result, 1, 1, "C")
        pdf.ln(5)
        
        # 4. STAGE 2: MULTI-MODAL AI EXTRACTION
        add_section_header("4. STAGE 2: AI DATA EXTRACTION DETAILS")
        for doc, info in extraction.items():
            if not info: continue
            pdf.set_fill_color(245, 245, 245)
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 10, f"SOURCE: {doc.upper()}", ln=True, fill=True)
            
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(40, 8, "FIELD", 1, 0, "C")
            pdf.cell(150, 8, "EXTRACTED VALUE", 1, 1, "C")
            
            pdf.set_font("helvetica", "", 10)
            pdf.cell(40, 8, "NAME", 1, 0, "L")
            pdf.cell(150, 8, str(info.get('name', 'N/A')), 1, 1, "L")
            pdf.cell(40, 8, "ID NUMBER", 1, 0, "L")
            pdf.cell(150, 8, str(info.get('id_number', 'N/A')), 1, 1, "L")
            pdf.ln(5)
        
        # 5. STAGE 3-4: REGULATORY
        add_section_header("5. STAGE 3-4: REGULATORY & AML COMPLIANCE")
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(120, 10, "COMPLIANCE RULE", 1, 0, "C")
        pdf.cell(70, 10, "STATUS", 1, 1, "C")
        
        pdf.set_font("helvetica", "", 10)
        for c in report_data.get("checks", []):
            status = "COMPLIANT" if c.get("pass") else "VIOLATION"
            pdf.cell(120, 10, str(c.get('rule', 'N/A')), 1, 0, "L")
            pdf.cell(70, 10, status, 1, 1, "C")
            
        pdf.output(output_path)
        return output_path
    except Exception as e:
        print(f"PDF Generation Error: {str(e)}")
        # If it fails, we at least log it
        raise e
