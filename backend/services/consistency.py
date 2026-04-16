import logging
import re
from pydantic import BaseModel
from rapidfuzz import fuzz
from .extraction import ExtractionResult

logger = logging.getLogger(__name__)

class ConsistencyResult(BaseModel):
    passed: bool
    name_score: float
    mismatches: list[str]

def check_consistency(aadhaar_data: ExtractionResult, pan_data: ExtractionResult, utility_data: ExtractionResult) -> ConsistencyResult:
    try:
        mismatches = []
        passed = True
        
        aadhaar = aadhaar_data.fields
        pan = pan_data.fields
        util = utility_data.fields
        
        # 1. Name comparison (Aadhaar & PAN)
        name_a = str(aadhaar.get("name", "")).lower()
        name_p = str(pan.get("name", "")).lower()
        
        name_score = fuzz.token_sort_ratio(name_a, name_p)
        if name_score < 60:
            mismatches.append(f"Name mismatch: Aadhaar shows '{name_a}', PAN shows '{name_p}' (score: {name_score:.1f})")
            passed = False
        elif name_score < 80:
            mismatches.append(f"Partial name match: Aadhaar shows '{name_a}', PAN shows '{name_p}' (score: {name_score:.1f})")
            
        # 2. DOB comparison (Aadhaar vs PAN)
        dob_a = aadhaar.get("dob")
        dob_p = pan.get("dob")
        if dob_a and dob_p and dob_a != dob_p:
            mismatches.append(f"DOB mismatch: Aadhaar shows {dob_a}, PAN shows {dob_p}")
            passed = False
            
        # 3. Address/PIN comparison (Aadhaar vs Utility Bill)
        addr_a = aadhaar.get("address", "")
        addr_u = util.get("address", "")
        
        if addr_a and addr_u:
            pin_a_match = re.search(r'\b\d{6}\b', str(addr_a))
            pin_u_match = re.search(r'\b\d{6}\b', str(addr_u))
            
            if pin_a_match and pin_u_match:
                pin_a = pin_a_match.group(0)
                pin_u = pin_u_match.group(0)
                
                if pin_a != pin_u:
                    mismatches.append(f"PIN mismatch: Aadhaar shows {pin_a}, Utility shows {pin_u}")
                    passed = False
                    
        return ConsistencyResult(passed=passed, name_score=name_score, mismatches=mismatches)
        
    except Exception as e:
        logger.exception("Error during consistency checks")
        raise
