"""
NER Service for preprocessing text before LLM cleaning.
Uses SpaCy and Regex to identify and replace sensitive data with placeholders.
"""
import logging
import re
from typing import Dict, List, Tuple
import spacy

logger = logging.getLogger(__name__)

# Global counters for placeholders
PERSON_COUNTER = 0
ORG_COUNTER = 0
GEO_COUNTER = 0
ADDRESS_COUNTER = 0


def reset_counters():
    """Reset all placeholder counters for a new document."""
    global PERSON_COUNTER, ORG_COUNTER, GEO_COUNTER, ADDRESS_COUNTER
    PERSON_COUNTER = 0
    ORG_COUNTER = 0
    GEO_COUNTER = 0
    ADDRESS_COUNTER = 0


def get_person_placeholder() -> str:
    """Get next person placeholder: [ЛИЦО-1], [ЛИЦО-2], etc."""
    global PERSON_COUNTER
    PERSON_COUNTER += 1
    return f"[ЛИЦО-{PERSON_COUNTER}]"


def get_org_placeholder() -> str:
    """Get next organization placeholder: [ОРГ-1], [ОРГ-2], etc."""
    global ORG_COUNTER
    ORG_COUNTER += 1
    return f"[ОРГ-{ORG_COUNTER}]"


def get_geo_placeholder() -> str:
    """Get next geography placeholder: [ГЕО-1], [ГЕО-2], etc."""
    global GEO_COUNTER
    GEO_COUNTER += 1
    return f"[ГЕО-{GEO_COUNTER}]"


def get_address_placeholder() -> str:
    """Get next address placeholder: [АДРЕС-1], [АДРЕС-2], etc."""
    global ADDRESS_COUNTER
    ADDRESS_COUNTER += 1
    return f"[АДРЕС-{ADDRESS_COUNTER}]"


# Regex patterns for 100% accurate replacements
REGEX_PATTERNS = {
    # Phone numbers (various formats)
    'phone': [
        r'\+7[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}',  # +7-XXX-XXX-XX-XX
        r'8[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}',    # 8-XXX-XXX-XX-XX
        r'\+7\(\d{3}\)\d{3}-?\d{2}-?\d{2}',                   # +7(XXX)XXX-XX-XX
    ],
    # Email addresses
    'email': [
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ],
    # INN (ИНН) - 10 or 12 digits
    'inn': [
        r'ИНН[:\s]*\d{10,12}',
        r'\b\d{10}\b',  # Standalone 10-digit number (careful with this)
        r'\b\d{12}\b',  # Standalone 12-digit number (careful with this)
    ],
    # BIN (БИН) - 12 digits
    'bin': [
        r'БИН[:\s]*\d{12}',
        r'БИК[:\s]*\d{9}',
    ],
    # SNILS (СНИЛС) - XXX-XXX-XXX XX
    'snils': [
        r'СНИЛС[:\s]*\d{3}-\d{3}-\d{3}\s*\d{2}',
        r'\b\d{3}-\d{3}-\d{3}\s*\d{2}\b',
    ],
    # Passport numbers
    'passport': [
        r'паспорт[:\s]*\d{4}\s*\d{6}',
        r'паспорта[:\s]*\d{4}\s*\d{6}',
        r'\b\d{4}\s*\d{6}\b',  # Standalone passport number
    ],
    # License plates (Russian/Kazakh format)
    'license_plate': [
        r'[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}',
    ],
    # Bank accounts
    'bank_account': [
        r'\b\d{20}\b',  # 20-digit account number
    ],
    # Card numbers (simplified)
    'card': [
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    ],
    # Addresses (Russian/Kazakh)
    'address': [
        r'(?:ул\.|улица|көше)\s+[А-Яа-яӘәІіҢңҒғҮүҰұҚқӨөҺһ\w\s]+,?\s*(?:д\.|дом|үй)\s*\d+',
        r'(?:пр\.|проспект|даңғыл)\s+[А-Яа-яӘәІіҢңҒғҮүҰұҚқӨөҺһ\w\s]+,?\s*\d+',
        r'(?:кв\.|квартира|пәтер)\s*\d+',
    ],
}


def replace_with_regex(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Replace sensitive data using regex patterns.
    Returns cleaned text and replacement dictionary.
    """
    replacements = {}
    cleaned_text = text

    # Phone numbers
    for pattern in REGEX_PATTERNS['phone']:
        matches = re.finditer(pattern, cleaned_text)
        for match in matches:
            if match.group() not in replacements:
                replacements[match.group()] = "[ТЕЛЕФОН]"
        cleaned_text = re.sub(pattern, "[ТЕЛЕФОН]", cleaned_text)

    # Email addresses
    for pattern in REGEX_PATTERNS['email']:
        matches = re.finditer(pattern, cleaned_text)
        for match in matches:
            if match.group() not in replacements:
                replacements[match.group()] = "[EMAIL]"
        cleaned_text = re.sub(pattern, "[EMAIL]", cleaned_text)

    # INN
    for pattern in REGEX_PATTERNS['inn']:
        matches = re.finditer(pattern, cleaned_text)
        for match in matches:
            if match.group() not in replacements:
                replacements[match.group()] = "[ИНН]"
        cleaned_text = re.sub(pattern, "[ИНН]", cleaned_text)

    # BIN
    for pattern in REGEX_PATTERNS['bin']:
        matches = re.finditer(pattern, cleaned_text)
        for match in matches:
            if match.group() not in replacements:
                replacements[match.group()] = "[БИН]"
        cleaned_text = re.sub(pattern, "[БИН]", cleaned_text)

    # SNILS
    for pattern in REGEX_PATTERNS['snils']:
        matches = re.finditer(pattern, cleaned_text)
        for match in matches:
            if match.group() not in replacements:
                replacements[match.group()] = "[СНИЛС]"
        cleaned_text = re.sub(pattern, "[СНИЛС]", cleaned_text)

    # Passport
    for pattern in REGEX_PATTERNS['passport']:
        matches = re.finditer(pattern, cleaned_text)
        for match in matches:
            if match.group() not in replacements:
                replacements[match.group()] = "[ПАСПОРТ]"
        cleaned_text = re.sub(pattern, "[ПАСПОРТ]", cleaned_text)

    # License plates
    for pattern in REGEX_PATTERNS['license_plate']:
        matches = re.finditer(pattern, cleaned_text)
        for match in matches:
            if match.group() not in replacements:
                replacements[match.group()] = "[ГОСНОМЕР]"
        cleaned_text = re.sub(pattern, "[ГОСНОМЕР]", cleaned_text)

    # Bank accounts
    for pattern in REGEX_PATTERNS['bank_account']:
        matches = re.finditer(pattern, cleaned_text)
        for match in matches:
            if match.group() not in replacements:
                replacements[match.group()] = "[СЧЕТ]"
        cleaned_text = re.sub(pattern, "[СЧЕТ]", cleaned_text)

    # Card numbers
    for pattern in REGEX_PATTERNS['card']:
        matches = re.finditer(pattern, cleaned_text)
        for match in matches:
            if match.group() not in replacements:
                replacements[match.group()] = "[КАРТА]"
        cleaned_text = re.sub(pattern, "[КАРТА]", cleaned_text)

    # Addresses
    for pattern in REGEX_PATTERNS['address']:
        matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)
        for match in matches:
            if match.group() not in replacements:
                placeholder = get_address_placeholder()
                replacements[match.group()] = placeholder
                cleaned_text = cleaned_text.replace(match.group(), placeholder)

    logger.info(f"Regex replacements: {len(replacements)} items replaced")
    return cleaned_text, replacements


def load_spacy_models():
    """
    Load SpaCy models for Russian language.
    """
    try:
        # Load Russian model
        nlp_ru = spacy.load("ru_core_news_sm")
        logger.info("✓ Loaded Russian SpaCy model: ru_core_news_sm")
        return nlp_ru
    except OSError:
        logger.error("SpaCy model not found. Please install: python -m spacy download ru_core_news_sm")
        raise Exception("SpaCy model not found. Run: python -m spacy download ru_core_news_sm")


def extract_entities_with_spacy(text: str, nlp_ru) -> Tuple[str, Dict[str, str]]:
    """
    Extract named entities using SpaCy and replace them with placeholders.
    Returns cleaned text and replacement dictionary.
    """
    replacements = {}
    doc = nlp_ru(text)

    # Track unique entities to maintain consistency
    entity_map = {}

    for ent in doc.ents:
        entity_text = ent.text.strip()

        # Skip if already processed
        if entity_text in entity_map:
            continue

        # Process by entity type
        if ent.label_ == "PER" or ent.label_ == "PERSON":
            # Person names
            placeholder = get_person_placeholder()
            entity_map[entity_text] = placeholder
            replacements[entity_text] = placeholder
            logger.debug(f"Person identified: {entity_text} -> {placeholder}")

        elif ent.label_ == "ORG":
            # Organizations
            placeholder = get_org_placeholder()
            entity_map[entity_text] = placeholder
            replacements[entity_text] = placeholder
            logger.debug(f"Organization identified: {entity_text} -> {placeholder}")

        elif ent.label_ == "LOC" or ent.label_ == "GPE":
            # Locations and geo-political entities
            # Only replace specific cities/regions, not generic terms
            if len(entity_text) > 3 and not entity_text.lower() in ['город', 'село', 'район', 'область']:
                placeholder = get_geo_placeholder()
                entity_map[entity_text] = placeholder
                replacements[entity_text] = placeholder
                logger.debug(f"Location identified: {entity_text} -> {placeholder}")

    # Apply replacements to text
    cleaned_text = text
    for original, placeholder in replacements.items():
        # Use word boundaries for safer replacement
        cleaned_text = re.sub(r'\b' + re.escape(original) + r'\b', placeholder, cleaned_text)

    logger.info(f"SpaCy NER: {len(replacements)} entities identified and replaced")
    return cleaned_text, replacements


def preprocess_with_ner(text: str) -> Dict[str, any]:
    """
    Main NER preprocessing function.

    1. Apply regex replacements (100% accurate for phones, emails, IDs)
    2. Apply SpaCy NER (for names, organizations, locations)
    3. Return preprocessed text + replacement registry

    Args:
        text: Original text to preprocess

    Returns:
        Dict containing:
            - preprocessed_text: Text with entities replaced by placeholders
            - replacements: Dictionary of all replacements made
            - stats: Statistics about replacements
            - success: Whether preprocessing succeeded
    """
    try:
        logger.info(f"Starting NER preprocessing. Text length: {len(text)} characters")

        # Reset counters for new document
        reset_counters()

        # Step 1: Regex replacements (100% accuracy)
        logger.info("Step 1: Applying regex replacements...")
        text_after_regex, regex_replacements = replace_with_regex(text)

        # Step 2: SpaCy NER
        logger.info("Step 2: Applying SpaCy NER...")
        nlp_ru = load_spacy_models()
        text_after_ner, ner_replacements = extract_entities_with_spacy(text_after_regex, nlp_ru)

        # Combine all replacements
        all_replacements = {**regex_replacements, **ner_replacements}

        stats = {
            "total_replacements": len(all_replacements),
            "regex_replacements": len(regex_replacements),
            "ner_replacements": len(ner_replacements),
            "persons": PERSON_COUNTER,
            "organizations": ORG_COUNTER,
            "locations": GEO_COUNTER,
            "addresses": ADDRESS_COUNTER,
        }

        logger.info(f"NER preprocessing complete. Total replacements: {stats['total_replacements']}")
        logger.info(f"Stats: {stats}")

        return {
            "preprocessed_text": text_after_ner,
            "original_text": text,
            "replacements": all_replacements,
            "stats": stats,
            "success": True,
            "error": None
        }

    except Exception as e:
        error_msg = f"Error during NER preprocessing: {str(e)}"
        logger.error(error_msg)
        return {
            "preprocessed_text": None,
            "original_text": text,
            "replacements": {},
            "stats": {},
            "success": False,
            "error": error_msg
        }
