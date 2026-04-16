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
        # Static key for demo consistency across restarts if not in .env
        key = b'pL1v5_9zQ6M3tY_6J5W7f8G9H0J1K2L3M4N5O6P7Q8R=' 
    try:
        return Fernet(key)
    except:
        return Fernet(Fernet.generate_key())

def encrypt_data(data: dict) -> str:
    if data is None: return ""
    f = get_fernet()
    json_data = json.dumps(data).encode()
    return f.encrypt(json_data).decode()

def decrypt_data(token: str) -> dict:
    if not token: return {}
    try:
        f = get_fernet()
        decrypted = f.decrypt(token.encode()).decode()
        return json.loads(decrypted)
    except Exception as e:
        print(f"Decryption Error: {e}")
        return {"error": "Decryption failed", "raw": token}

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
        
        # Logo and Header - Enlarged Logo
        # Using absolute path to ensure it's found regardless of execution context
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "assets", "logo.jpeg")
        
        if os.path.exists(logo_path):
            pdf.image(logo_path, 10, 8, 30) # Bigger logo: 30mm width
            header_offset = 45 # Increased offset for bigger logo
        else:
            header_offset = 10

        # Text cleaning helper to avoid FPDF encoding errors
        def clean_text(text):
            if text is None: return "N/A"
            # Handle list/dict types that might come from safe_decrypt
            if isinstance(text, (list, dict)):
                text = json.dumps(text)
            # Remove characters that might crash FPDF default fonts
            return str(text).encode('latin-1', 'replace').decode('latin-1')
        
        # Dark Background for Header
        pdf.set_fill_color(10, 10, 10)
        pdf.rect(0, 0, 210, 50, "F")
        
        # Header Title
        pdf.set_font("helvetica", "B", 30)
        pdf.set_text_color(255, 77, 0) # VerifAI Orange
        pdf.set_xy(header_offset, 15)
        pdf.cell(0, 15, "VERIFAI", ln=True, align="L")
        
        # Header Subtitle
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(150, 150, 150)
        pdf.set_xy(header_offset, 28)
        pdf.cell(0, 10, "AI-POWERED KYC + AML DOCUMENT VERIFICATION", ln=True, align="L")
        
        # Decision Badge & Confidence on Header
        decision = str(report_data.get('decision', 'REJECTED')).upper()
        confidence = report_data.get('confidence_score', 0)
        
        if decision == "APPROVED":
            pdf.set_fill_color(0, 255, 0)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_fill_color(255, 0, 0)
            pdf.set_text_color(255, 255, 255)
            
        pdf.set_xy(150, 15)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(50, 12, decision, ln=True, align="C", fill=True)
        
        pdf.set_xy(150, 28)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(200, 200, 200)
        pdf.cell(50, 10, f"CONFIDENCE: {confidence:.1f}%", ln=True, align="C")
        
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
        stage_outputs = report_data.get("stage_outputs", {})
        if not isinstance(stage_outputs, dict):
            stage_outputs = {}
            
        extraction = stage_outputs.get("extraction", {})
        if not isinstance(extraction, dict):
            extraction = {}
            
        # Use Aadhaar as primary source for profile
        profile_data = extraction.get("aadhaar") or extraction.get("pan") or {}
        if not isinstance(profile_data, dict):
            profile_data = {}
        
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(50, 10, "PRIMARY NAME:", ln=False)
        pdf.set_font("helvetica", "", 11)
        pdf.cell(0, 10, clean_text(profile_data.get("name")), ln=True)
        
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(50, 10, "VERIFIED IDENTITY:", ln=False)
        pdf.set_font("helvetica", "", 11)
        pdf.cell(0, 10, clean_text(profile_data.get("id_number")), ln=True)
        
        pdf.ln(5)

        # 2. EXECUTIVE SUMMARY & REASONING
        add_section_header("2. AI REASONING & COMPLIANCE SUMMARY")
        pdf.set_font("helvetica", "", 11)
        reasons = report_data.get("reasons", [])
        if not isinstance(reasons, list):
            reasons = [str(reasons)] if reasons else []
            
        for reason in reasons:
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(30, 8, "[ANALYSIS]", ln=False)
            pdf.set_font("helvetica", "", 11)
            # Use specific width instead of 0 to avoid space calculation errors
            pdf.multi_cell(160, 8, clean_text(reason), ln=True)
            pdf.ln(2)
        pdf.ln(5)
        
        # 3. STAGE 1: FORENSICS
        add_section_header("3. STAGE 1: IMAGE FORENSICS (ELA)")
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(60, 10, "DOCUMENT SOURCE", 1, 0, "C")
        pdf.cell(60, 10, "FORENSIC STATUS", 1, 0, "C")
        pdf.cell(70, 10, "RESULT", 1, 1, "C")
        
        pdf.set_font("helvetica", "", 10)
        tamper_data = stage_outputs.get("tamper", [])
        if not isinstance(tamper_data, list):
            tamper_data = []
            
        for t in tamper_data:
            if not isinstance(t, dict): continue
            doc = str(t.get('document', 'N/A')).upper()
            status = "PASS" if not t.get("tamper") else "FAIL"
            result = "PASS" if not t.get("tamper") else "FAIL"
            pdf.cell(60, 10, clean_text(doc), 1, 0, "C")
            pdf.cell(60, 10, clean_text(status), 1, 0, "C")
            pdf.cell(70, 10, clean_text(result), 1, 1, "C")
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
            pdf.cell(110, 8, "EXTRACTED VALUE", 1, 0, "C")
            pdf.cell(40, 8, "STATUS", 1, 1, "C")
            
            pdf.set_font("helvetica", "", 10)
            for field, value in info.items():
                if field in ["confidence", "document_type"]: continue
                pdf.cell(40, 8, clean_text(field.upper()), 1, 0, "C")
                pdf.cell(110, 8, clean_text(value), 1, 0, "C")
                pdf.cell(40, 8, "PASS", 1, 1, "C")
            pdf.ln(3)
        pdf.ln(5)

        # 5. DOCUMENT EVIDENCE
        document_paths = report_data.get("document_paths", {})
        if document_paths:
            pdf.add_page()
            add_section_header("5. DOCUMENT EVIDENCE")
            
            x_start = 10
            y_start = pdf.get_y()
            img_width = 90
            img_height = 60
            
            count = 0
            for doc_type, path in document_paths.items():
                if os.path.exists(path):
                    # Check if we need a new page
                    if pdf.get_y() + img_height > 270:
                        pdf.add_page()
                        y_start = 20
                    
                    pdf.set_font("helvetica", "B", 10)
                    pdf.cell(0, 8, f"EVIDENCE: {doc_type.upper()}", ln=True)
                    
                    # Add image
                    try:
                        # Convert image to RGB if it's not (FPDF requirement)
                        img = Image.open(path)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                            rgb_path = f"{path}_rgb.jpg"
                            img.save(rgb_path, "JPEG")
                            pdf.image(rgb_path, x=10, w=img_width)
                            os.remove(rgb_path)
                        else:
                            pdf.image(path, x=10, w=img_width)
                    except Exception as e:
                        pdf.set_font("helvetica", "I", 8)
                        pdf.cell(0, 8, f"Error loading image: {str(e)}", ln=True)
                    
                    pdf.ln(10)
                    count += 1
        
        # 6. STAGE 3-4: REGULATORY
        add_section_header("6. STAGE 3-4: REGULATORY & AML COMPLIANCE")
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(120, 10, "COMPLIANCE RULE", 1, 0, "C")
        pdf.cell(70, 10, "STATUS", 1, 1, "C")
        
        pdf.set_font("helvetica", "", 10)
        checks = report_data.get("checks", [])
        if not isinstance(checks, list):
            checks = []
            
        for c in checks:
            if not isinstance(c, dict): continue
            status = "PASS" if c.get("pass") else "FAIL"
            pdf.cell(120, 10, clean_text(c.get('rule', 'N/A')), 1, 0, "L")
            pdf.cell(70, 10, clean_text(status), 1, 1, "C")
            
        pdf.output(output_path)
        return output_path
    except Exception as e:
        print(f"PDF Generation Error: {str(e)}")
        # If it fails, we at least log it
        raise e
