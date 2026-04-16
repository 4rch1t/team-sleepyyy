import logging
import base64
import json
from pydantic import BaseModel
from openai import OpenAI
from config import settings

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class ExtractionResult(BaseModel):
    fields: dict
    low_confidence_fields: list[str]
    raw_response: str

def extract_document_data(image_bytes: bytes, document_type: str) -> ExtractionResult:
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = """You are a document extraction system. Extract fields from this Indian KYC document into JSON. Return ONLY valid JSON, no explanation, no markdown.
        Schema: {
          'name': string,
          'dob': 'YYYY-MM-DD or null',
          'id_number': string,
          'address': string or null,
          'issue_date': 'YYYY-MM-DD or null',
          'document_type': 'AADHAAR|PAN|UTILITY_BILL',
          'confidence': {
            'name': float 0-1,
            'dob': float 0-1,
            'id_number': float 0-1,
            'address': float 0-1,
            'issue_date': float 0-1
          }
        }"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=1024,
            temperature=0
        )
        
        raw_text = response.choices[0].message.content
        if raw_text.startswith("```json"):
            raw_text = raw_text.split("```json")[-1].replace("```", "").strip()
            
        data = json.loads(raw_text)
        
        confidences = data.get("confidence", {})
        low_confidence = [field for field, conf in confidences.items() if (conf is not None and conf < 0.75)]
        
        return ExtractionResult(
            fields=data,
            low_confidence_fields=low_confidence,
            raw_response=raw_text
        )
    except Exception as e:
        logger.exception(f"Error during data extraction for document: {document_type}")
        raise
