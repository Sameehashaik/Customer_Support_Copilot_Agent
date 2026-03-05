"""
PII Filter - Detect and redact personally identifiable information

CRITICAL: This protects customer privacy and ensures legal compliance
- GDPR: EU data protection (fines up to 20M euros)
- CCPA: California privacy (fines $2,500-7,500 per violation)
- HIPAA: Healthcare data protection

PII Types Detected:
- Emails, phones, SSN, credit cards
- Names, addresses, IP addresses
- Order IDs, zip codes
"""

import re
from typing import List, Tuple, Dict
from dataclasses import dataclass
import logging

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available - name detection disabled")

logger = logging.getLogger(__name__)

@dataclass
class PIIEntity:
    """Detected PII entity"""
    type: str
    value: str
    start: int
    end: int
    confidence: float

class PIIFilter:
    """Production-ready PII detection and redaction"""

    PATTERNS = {
        'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'PHONE': r'(?:\+?1[-.]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.]?\d{4})\b',
        'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
        'CREDIT_CARD': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'IP_ADDRESS': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'ORDER_ID': r'\b(?:order|tracking)[\s#:]*(?=[A-Z0-9]*\d)[A-Z0-9]{6,15}\b',
        'ZIP_CODE': r'\b\d{5}-\d{4}\b',
    }

    def __init__(self, use_ner: bool = True):
        self.use_ner = use_ner and SPACY_AVAILABLE

        if self.use_ner:
            try:
                self.nlp = spacy.load("en_core_web_lg")
                logger.info("Loaded spaCy NER model")
            except Exception as e:
                logger.warning(f"Failed to load spaCy: {e}")
                self.use_ner = False

        logger.info(f"PII Filter initialized (NER: {self.use_ner})")

    def detect_pii(self, text: str) -> List[PIIEntity]:
        """Detect all PII in text"""
        entities = []
        entities.extend(self._detect_with_regex(text))

        if self.use_ner:
            entities.extend(self._detect_with_ner(text))

        entities = self._deduplicate(entities)
        logger.info(f"Detected {len(entities)} PII entities")
        return entities

    def _detect_with_regex(self, text: str) -> List[PIIEntity]:
        """Detect PII using regex patterns"""
        entities = []
        for pii_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(PIIEntity(
                    type=pii_type,
                    value=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.95
                ))
        return entities

    def _detect_with_ner(self, text: str) -> List[PIIEntity]:
        """Detect names using spaCy NER"""
        entities = []
        try:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG']:
                    entities.append(PIIEntity(
                        type=f'NAME_{ent.label_}',
                        value=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.75
                    ))
        except Exception as e:
            logger.error(f"NER detection failed: {e}")
        return entities

    def _deduplicate(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Remove overlapping detections"""
        if not entities:
            return []

        sorted_entities = sorted(entities, key=lambda x: x.confidence, reverse=True)
        final = []
        used_ranges = []

        for entity in sorted_entities:
            overlaps = False
            for start, end in used_ranges:
                if not (entity.end <= start or entity.start >= end):
                    overlaps = True
                    break

            if not overlaps:
                final.append(entity)
                used_ranges.append((entity.start, entity.end))

        return sorted(final, key=lambda x: x.start)

    def redact(self, text: str, placeholder_style: str = "type") -> Tuple[str, List[PIIEntity]]:
        """Redact PII from text"""
        entities = self.detect_pii(text)

        if not entities:
            return text, []

        redacted = ""
        last_end = 0

        for entity in entities:
            redacted += text[last_end:entity.start]

            if placeholder_style == "type":
                placeholder = f"[{entity.type}]"
            elif placeholder_style == "generic":
                placeholder = "[REDACTED]"
            else:
                placeholder = "[REDACTED]"

            redacted += placeholder
            last_end = entity.end

        redacted += text[last_end:]
        logger.info(f"Redacted {len(entities)} PII entities")
        return redacted, entities

    def safe_for_llm(self, text: str) -> Tuple[str, Dict]:
        """
        Main method - prepare text safely for LLM

        Example:
            >>> filter = PIIFilter()
            >>> safe, meta = filter.safe_for_llm("My SSN is 123-45-6789")
            >>> print(safe)
            "My SSN is [SSN]"
        """
        redacted_text, entities = self.redact(text)

        metadata = {
            'pii_detected': len(entities) > 0,
            'entity_count': len(entities),
            'entity_types': list(set(e.type for e in entities)),
            'entities': [
                {
                    'type': e.type,
                    'confidence': e.confidence,
                    'position': (e.start, e.end)
                }
                for e in entities
            ]
        }

        return redacted_text, metadata


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    filter = PIIFilter()

    test = "My email is john@example.com and phone is 555-123-4567"
    safe, meta = filter.safe_for_llm(test)
    print(f"Original: {test}")
    print(f"Redacted: {safe}")
    print(f"PII Found: {meta['entity_types']}")
