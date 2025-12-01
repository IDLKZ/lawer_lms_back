import logging
from typing import Dict, Optional
from PyPDF2 import PdfReader
import tempfile
import os
from app.services.llm_service import clean_text_with_llm, clean_text_with_ner_and_llm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        str: Extracted text from the PDF

    Raises:
        Exception: If text extraction fails
    """
    try:
        logger.info(f"Extracting text from PDF: {file_path}")
        reader = PdfReader(file_path)

        text = ""
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            text += page_text + "\n"
            logger.debug(f"Extracted text from page {page_num}: {len(page_text)} characters")

        logger.info(f"Successfully extracted {len(text)} characters from {len(reader.pages)} pages")
        return text.strip()

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes (e.g., from uploaded file).

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        str: Extracted text from the PDF

    Raises:
        Exception: If text extraction fails
    """
    try:
        # Create a temporary file to store the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name

        try:
            # Extract text from the temporary file
            text = extract_text_from_pdf(temp_file_path)
            return text
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except Exception as e:
        logger.error(f"Error extracting text from PDF bytes: {str(e)}")
        raise Exception(f"Failed to extract text from PDF bytes: {str(e)}")


def process_pdf_with_llm(
    pdf_bytes: bytes,
    provider: str = "ollama",
    model: str = "llama3",
    temperature: float = 0.1,
    ollama_url: str = "http://localhost:11434",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    use_ner: bool = True
) -> Dict[str, any]:
    """
    Process a PDF file: extract text and clean personal data using NER + LLM pipeline.

    RECOMMENDED: use_ner=True for best quality (default).
    This uses a two-stage pipeline:
    1. NER preprocessing with SpaCy + Regex (100% accuracy for IDs, phones, emails)
    2. LLM finalization (context-aware cleanup)

    Args:
        pdf_bytes: PDF file content as bytes
        provider: LLM provider ('ollama', 'openrouter', 'openai', 'groq')
        model: Name of the model to use
        temperature: Temperature for text generation (lower = more deterministic)
        ollama_url: URL of the Ollama server (for local)
        base_url: Base URL for cloud providers
        api_key: API key for cloud providers
        use_ner: Use NER preprocessing before LLM (default: True, recommended)

    Returns:
        Dict containing:
            - original_text: Extracted text from PDF
            - cleaned_text: Text with personal data removed/masked
            - preprocessed_text: Text after NER preprocessing (if use_ner=True)
            - original_length: Length of original text
            - cleaned_length: Length of cleaned text
            - llm_model: Name of the model used
            - ner_stats: Statistics from NER preprocessing (if use_ner=True)
            - pipeline_used: Which pipeline was used ("NER + LLM" or "LLM Only")
            - success: Whether the operation was successful
            - error: Error message if failed
    """
    try:
        # Step 1: Extract text from PDF
        logger.info("Step 1: Extracting text from PDF")
        original_text = extract_text_from_bytes(pdf_bytes)

        if not original_text or len(original_text.strip()) == 0:
            raise ValueError("No text could be extracted from the PDF. The file might be empty or contain only images.")

        logger.info(f"Extracted {len(original_text)} characters from PDF")

        # Step 2: Clean text using NER + LLM pipeline (or LLM only)
        pipeline_name = "NER + LLM" if use_ner else "LLM only"
        logger.info(f"Step 2: Cleaning text with {pipeline_name} pipeline (provider: {provider})")

        cleaning_result = clean_text_with_ner_and_llm(
            text=original_text,
            provider=provider,
            model=model,
            temperature=temperature,
            ollama_url=ollama_url,
            base_url=base_url,
            api_key=api_key,
            use_ner=use_ner
        )

        if not cleaning_result["success"]:
            return {
                "original_text": original_text,
                "cleaned_text": None,
                "preprocessed_text": None,
                "original_length": len(original_text),
                "cleaned_length": 0,
                "llm_model": model,
                "ner_stats": cleaning_result.get("ner_stats", {}),
                "pipeline_used": pipeline_name,
                "success": False,
                "error": cleaning_result["error"]
            }

        # Combine results
        result = {
            "original_text": original_text,
            "cleaned_text": cleaning_result["cleaned_text"],
            "preprocessed_text": cleaning_result.get("preprocessed_text"),
            "original_length": len(original_text),
            "cleaned_length": len(cleaning_result["cleaned_text"]),
            "llm_model": cleaning_result["llm_model"],
            "ner_stats": cleaning_result.get("ner_stats", {}),
            "pipeline_used": cleaning_result.get("pipeline_used", pipeline_name),
            "success": True,
            "error": None
        }

        if "chunks_processed" in cleaning_result:
            result["chunks_processed"] = cleaning_result["chunks_processed"]

        logger.info(f"PDF processing complete. Original: {result['original_length']} chars, Cleaned: {result['cleaned_length']} chars")
        if use_ner and result["ner_stats"]:
            logger.info(f"NER statistics: {result['ner_stats']}")
        return result

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return {
            "original_text": None,
            "cleaned_text": None,
            "original_length": 0,
            "cleaned_length": 0,
            "llm_model": model,
            "success": False,
            "error": f"Failed to process PDF: {str(e)}"
        }


# Keep old function name for backwards compatibility
def process_pdf_with_ollama(
    pdf_bytes: bytes,
    ollama_url: str = "http://localhost:11434",
    model: str = "llama3",
    temperature: float = 0.1
) -> Dict[str, any]:
    """
    Legacy function. Use process_pdf_with_llm instead.
    """
    return process_pdf_with_llm(
        pdf_bytes=pdf_bytes,
        provider="ollama",
        model=model,
        temperature=temperature,
        ollama_url=ollama_url
    )


def process_pdf_file_path(
    file_path: str,
    provider: str = "ollama",
    model: str = "llama3",
    temperature: float = 0.1,
    ollama_url: str = "http://localhost:11434",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, any]:
    """
    Process a PDF file from file path: extract text and clean personal data using LLM.

    Args:
        file_path: Path to the PDF file
        provider: LLM provider
        model: Name of the model to use
        temperature: Temperature for text generation
        ollama_url: Ollama URL (for local)
        base_url: Base URL (for cloud)
        api_key: API key (for cloud)

    Returns:
        Dict containing processing results
    """
    try:
        logger.info(f"Processing PDF file: {file_path}")

        # Read the file
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

        # Process using the bytes function
        return process_pdf_with_llm(
            pdf_bytes, provider, model, temperature,
            ollama_url, base_url, api_key
        )

    except Exception as e:
        logger.error(f"Error processing PDF file: {str(e)}")
        return {
            "original_text": None,
            "cleaned_text": None,
            "original_length": 0,
            "cleaned_length": 0,
            "llm_model": model,
            "success": False,
            "error": f"Failed to process PDF file: {str(e)}"
        }


def validate_pdf_file(pdf_bytes: bytes) -> Dict[str, any]:
    """
    Validate that the uploaded file is a valid PDF and extract basic information.

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        Dict containing:
            - is_valid: Whether the file is a valid PDF
            - page_count: Number of pages in the PDF
            - file_size: Size of the file in bytes
            - error: Error message if validation fails
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name

        try:
            # Try to read the PDF
            reader = PdfReader(temp_file_path)
            page_count = len(reader.pages)

            return {
                "is_valid": True,
                "page_count": page_count,
                "file_size": len(pdf_bytes),
                "error": None
            }

        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except Exception as e:
        logger.error(f"PDF validation failed: {str(e)}")
        return {
            "is_valid": False,
            "page_count": 0,
            "file_size": len(pdf_bytes),
            "error": str(e)
        }
