import logging
import re
from datetime import datetime
from pydantic import BaseModel
from rapidfuzz import fuzz
from .extraction import ExtractionResult

logger = logging.getLogger(__name__)

PEP_LIST = [
   "Narendra Modi", "Amit Shah", "Rahul Gandhi", "Arvind Kejriwal", 
   "Mamata Banerjee", "Yogi Adityanath", "Nitish Kumar", "Sharad Pawar",
   "Uddhav Thackeray", "Hemant Soren", "K Chandrashekar Rao", "MK Stalin",
   "Pinarayi Vijayan", "Bhupesh Baghel", "Ashok Gehlot", "Sukhvinder Singh",
   "Pushkar Singh Dhami", "Shivraj Singh Chouhan", "Eknath Shinde", "Devendra Fadnavis"
]

class RuleResult(BaseModel):
    rule_name: str
    passed: bool
    reason: str

class ComplianceResult(BaseModel):
    rules_checked: list[RuleResult]
    passed: bool

def check_compliance(aadhaar_data: ExtractionResult, pan_data: ExtractionResult, utility_data: ExtractionResult) -> ComplianceResult:
    try:
        rules = []
        
        aadhaar = aadhaar_data.fields
        pan = pan_data.fields
        util = utility_data.fields
        
        # Rule 1: PAN format
        pan_id = str(pan.get("id_number", "")).strip()
        if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan_id):
            rules.append(RuleResult(rule_name="PAN Format", passed=True, reason=f"{pan_id} matches required format"))
        else:
            rules.append(RuleResult(rule_name="PAN Format", passed=False, reason=f"{pan_id} is largely invalid format"))
            
        # Rule 2: Aadhaar format
        aadhaar_id = str(aadhaar.get("id_number", "")).strip().replace(" ", "").replace("-", "")
        if re.match(r'^\d{12}$', aadhaar_id):
            rules.append(RuleResult(rule_name="Aadhaar Format", passed=True, reason="12-digit number validated"))
        else:
            rules.append(RuleResult(rule_name="Aadhaar Format", passed=False, reason="Aadhaar format is invalid"))
            
        # Rule 3: Utility bill recency
        issue_date_str = util.get("issue_date")
        if issue_date_str:
            try:
                issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d")
                days_diff = (datetime.now() - issue_date).days
                if days_diff <= 90:
                    rules.append(RuleResult(rule_name="Utility Bill Recency", passed=True, reason="Bill is within 90 days"))
                else:
                    rules.append(RuleResult(rule_name="Utility Bill Recency", passed=False, reason=f"Bill dated {issue_date_str} exceeds 90-day RBI requirement"))
            except ValueError:
                rules.append(RuleResult(rule_name="Utility Bill Recency", passed=False, reason="Invalid date format on bill"))
        else:
            rules.append(RuleResult(rule_name="Utility Bill Recency", passed=False, reason="No issue date found on bill"))
            
        # Rule 4: PEP screening
        pep_match = False
        pep_reason = "No PEP match found"
        name_ToCheck = str(aadhaar.get("name", ""))
        if name_ToCheck and name_ToCheck != "None":
            for pep in PEP_LIST:
                score = fuzz.token_sort_ratio(name_ToCheck.lower(), pep.lower())
                if score >= 85:
                    pep_match = True
                    pep_reason = f"Potential PEP Match ({score:.1f}% confidence for {pep})"
                    break
        rules.append(RuleResult(rule_name="PEP Screening", passed=not pep_match, reason=pep_reason))
        
        all_passed = all(r.passed for r in rules)
        
        return ComplianceResult(rules_checked=rules, passed=all_passed)
        
    except Exception as e:
        logger.exception("Error during compliance checks")
        raise
