import logging
from typing import Dict
from openai import OpenAI

logger = logging.getLogger(__name__)


def clean_text_with_cloud_llm(
    text: str,
    prompt: str,
    base_url: str,
    api_key: str,
    model: str,
    temperature: float = 0.1
) -> Dict[str, any]:
    """
    Clean personal data from text using cloud LLM (OpenRouter, OpenAI, Groq, etc.).

    Args:
        text: The text to clean
        prompt: The system/user prompt for cleaning
        base_url: Base URL of the API (e.g., https://openrouter.ai/api/v1)
        api_key: API key for authentication
        model: Name of the model to use
        temperature: Temperature for generation (lower = more deterministic)

    Returns:
        Dict containing:
            - cleaned_text: Text with personal data removed/masked
            - original_length: Length of original text
            - cleaned_length: Length of cleaned text
            - llm_model: Name of the model used
            - success: Whether the operation was successful
            - error: Error message if failed
    """
    try:
        logger.info(f"Starting text cleaning with cloud LLM: {model}")
        logger.info(f"Original text length: {len(text)} characters")
        logger.info(f"Using base URL: {base_url}")

        # Create OpenAI client with custom base URL
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )

        # Prepare the full prompt
        full_prompt = prompt.format(text=text)

        logger.info(f"Sending request to cloud LLM")

        # Send request to cloud API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            temperature=temperature,
            max_tokens=16000  # Allow sufficient tokens for cleaned text output
        )

        # Log response details for debugging
        logger.info(f"Response received. Choices count: {len(response.choices)}")
        if response.choices:
            logger.info(f"First choice finish_reason: {response.choices[0].finish_reason}")

        # Extract cleaned text from response
        cleaned_text = response.choices[0].message.content if response.choices else None

        if not cleaned_text:
            logger.error(f"Empty response from LLM. Response object: {response}")
            logger.error(f"Response choices: {response.choices if hasattr(response, 'choices') else 'No choices'}")
            raise ValueError("Cloud LLM returned empty response")

        logger.info(f"Cleaned text length: {len(cleaned_text)} characters")
        logger.info(f"Cleaning completed successfully")

        return {
            "cleaned_text": cleaned_text.strip(),
            "original_length": len(text),
            "cleaned_length": len(cleaned_text.strip()),
            "llm_model": model,
            "success": True,
            "error": None
        }

    except Exception as e:
        error_msg = f"Error during cloud LLM text cleaning: {str(e)}"
        logger.error(error_msg)
        return {
            "cleaned_text": None,
            "original_length": len(text),
            "cleaned_length": 0,
            "llm_model": model,
            "success": False,
            "error": error_msg
        }


def test_cloud_llm_connection(
    base_url: str,
    api_key: str,
    model: str
) -> Dict[str, any]:
    """
    Test connection to cloud LLM service.

    Args:
        base_url: Base URL of the API
        api_key: API key for authentication
        model: Model to test

    Returns:
        Dict with connection status
    """
    try:
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )

        # Try a simple request to test connection
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=16  # Minimum required by most providers
        )

        logger.info(f"Cloud LLM connection successful. Model: {model}")

        return {
            "connected": True,
            "model_available": True,
            "requested_model": model,
            "error": None
        }

    except Exception as e:
        error_msg = f"Failed to connect to cloud LLM: {str(e)}"
        logger.error(error_msg)
        return {
            "connected": False,
            "model_available": False,
            "requested_model": model,
            "error": error_msg
        }


def clean_large_text_with_cloud_llm(
    text: str,
    prompt: str,
    base_url: str,
    api_key: str,
    model: str,
    temperature: float = 0.1,
    max_chunk_size: int = 12000
) -> Dict[str, any]:
    """
    Clean large text by processing it in chunks using cloud LLM.

    Args:
        text: The text to clean
        prompt: The cleaning prompt template
        base_url: Base URL of the API
        api_key: API key
        model: Model name
        temperature: Temperature for generation
        max_chunk_size: Maximum size of each chunk

    Returns:
        Dict with cleaned text and metadata
    """
    from app.services.llm_service import chunk_text

    try:
        # Split text into chunks
        chunks = chunk_text(text, max_chunk_size)

        if len(chunks) == 1:
            # Process single chunk
            return clean_text_with_cloud_llm(text, prompt, base_url, api_key, model, temperature)

        # Process multiple chunks
        logger.info(f"Processing {len(chunks)} chunks with cloud LLM")
        cleaned_chunks = []
        total_original_length = 0
        total_cleaned_length = 0

        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {i}/{len(chunks)}")
            result = clean_text_with_cloud_llm(chunk, prompt, base_url, api_key, model, temperature)

            if not result["success"]:
                return result

            cleaned_chunks.append(result["cleaned_text"])
            total_original_length += result["original_length"]
            total_cleaned_length += result["cleaned_length"]

        # Combine cleaned chunks
        cleaned_text = "\n\n".join(cleaned_chunks)

        logger.info(f"All chunks processed successfully with cloud LLM")

        return {
            "cleaned_text": cleaned_text,
            "original_length": total_original_length,
            "cleaned_length": total_cleaned_length,
            "llm_model": model,
            "success": True,
            "error": None,
            "chunks_processed": len(chunks)
        }

    except Exception as e:
        error_msg = f"Error processing large text with cloud LLM: {str(e)}"
        logger.error(error_msg)
        return {
            "cleaned_text": None,
            "original_length": len(text),
            "cleaned_length": 0,
            "llm_model": model,
            "success": False,
            "error": error_msg
        }
