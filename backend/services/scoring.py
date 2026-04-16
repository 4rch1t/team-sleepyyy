import logging
from pydantic import BaseModel
from .tamper_detection import TamperResult
from .extraction import ExtractionResult
from .consistency import ConsistencyResult
from .compliance import ComplianceResult

logger = logging.getLogger(__name__)

class ScoringResult(BaseModel):
    score: float
    decision: str
    breakdown: dict

def calculate_score(
    tamper_result: TamperResult,
    aadhaar_ext: ExtractionResult,
    pan_ext: ExtractionResult, 
    util_ext: ExtractionResult,
    consistency: ConsistencyResult,
    compliance: ComplianceResult
) -> ScoringResult:
    try:
        # Tamper Score
        tamper_score = 0.0 if tamper_result.is_tampered else 1.0
        
        # Extraction Score
        conf_sum = 0
        conf_count = 0
        for doc in [aadhaar_ext, pan_ext, util_ext]:
            confs = doc.fields.get("confidence", {})
            for k, val in confs.items():
                if val is not None:
                    conf_sum += float(val)
                    conf_count += 1
        
        extraction_score = (conf_sum / conf_count) if conf_count > 0 else 0.0
        
        # Consistency Score
        consistency_score = 0.0
        if consistency.passed:
            consistency_score = 1.0
        elif len([m for m in consistency.mismatches if "Partial name match" in m]) > 0 and not any("mismatch: Aadhaar" in m for m in consistency.mismatches if "Partial name match" not in m):
            consistency_score = 0.5
            
        # Compliance Score
        rules = compliance.rules_checked
        rules_passed = sum(1 for r in rules if r.passed)
        total_rules = len(rules)
        compliance_score = (rules_passed / total_rules) if total_rules > 0 else 0.0
        
        # Weighted Final Score
        final_score = (tamper_score * 0.30) + (extraction_score * 0.20) + (consistency_score * 0.25) + (compliance_score * 0.25)
        
        # Decision Boundaries
        if final_score >= 0.85:
            decision = "APPROVED"
        elif 0.60 <= final_score < 0.85:
            decision = "ESCALATED"
        else:
            decision = "REJECTED"
            
        # Special Hard Rejects overrides:
        
        if not consistency.passed:
            if decision == "APPROVED":
                decision = "ESCALATED"
                
        has_pep = any(not r.passed and r.rule_name == "PEP Screening" for r in rules)
        if has_pep and decision == "APPROVED":
            decision = "ESCALATED"
            
        # Tampering is immediate rejection.
        if tamper_result.is_tampered:
            decision = "REJECTED"
            
        low_confidence = aadhaar_ext.low_confidence_fields + pan_ext.low_confidence_fields + util_ext.low_confidence_fields

        breakdown = {
            "tamper": {
                "score": round(tamper_score, 2),
                "weight": 0.30,
                "details": tamper_result.reason
            },
            "extraction": {
                "score": round(extraction_score, 2),
                "weight": 0.20,
                "low_confidence_fields": list(set(low_confidence))
            },
            "consistency": {
                "score": round(consistency_score, 2),
                "weight": 0.25,
                "mismatches": consistency.mismatches
            },
            "compliance": {
                "score": round(compliance_score, 2),
                "weight": 0.25,
                "rules": [
                    {"rule": r.rule_name, "passed": r.passed, "reason": r.reason} for r in rules
                ]
            }
        }
        
        return ScoringResult(
            score=round(float(final_score), 4),
            decision=decision,
            breakdown=breakdown
        )
        
    except Exception:
        logger.exception("Error during scoring calculation")
        raise
