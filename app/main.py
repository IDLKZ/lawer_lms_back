from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api import auth, courses, ai, tests, results, summaries, cases, case_results, users
from app.services.llm_service import test_llm_connection
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown events.
    """
    # Startup
    try:
        provider = settings.LLM_PROVIDER
        logger.info(f"Testing connection to LLM ({provider})...")

        connection_result = test_llm_connection(
            provider=provider,
            model=settings.LLM_MODEL,
            ollama_url=settings.OLLAMA_URL,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY
        )

        if connection_result["connected"]:
            if provider == "ollama":
                logger.info(f"✓ Ollama connection successful at {settings.OLLAMA_URL}")
                logger.info(f"✓ Available models: {', '.join(connection_result.get('available_models', []))}")

                if connection_result["model_available"]:
                    logger.info(f"✓ Model '{settings.LLM_MODEL}' is available and ready to use")
                else:
                    logger.warning(f"⚠ Model '{settings.LLM_MODEL}' not found in available models")
                    logger.warning(f"  Please run: ollama pull {settings.LLM_MODEL}")
            else:
                logger.info(f"✓ Cloud LLM connection successful ({provider})")
                logger.info(f"✓ Using base URL: {settings.LLM_BASE_URL}")
                logger.info(f"✓ Model '{settings.LLM_MODEL}' is ready to use")
        else:
            if provider == "ollama":
                logger.error(f"✗ Failed to connect to Ollama: {connection_result['error']}")
                logger.error(f"  Please ensure Ollama is running at {settings.OLLAMA_URL}")
                logger.error(f"  You can start it with: ollama serve")
            else:
                logger.error(f"✗ Failed to connect to cloud LLM ({provider}): {connection_result['error']}")
                logger.error(f"  Please check your LLM_BASE_URL and LLM_API_KEY in .env")

    except Exception as e:
        logger.error(f"Error during startup initialization: {str(e)}")

    yield

    # Shutdown (cleanup code goes here if needed)
    logger.info("Application shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API для системы обучения (LMS) правоохранительной академии",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(courses.router, prefix=settings.API_V1_STR)
app.include_router(cases.router, prefix=settings.API_V1_STR)
app.include_router(case_results.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(tests.router, prefix=settings.API_V1_STR)
app.include_router(summaries.router, prefix=settings.API_V1_STR)
app.include_router(results.router, prefix=settings.API_V1_STR)



@app.get("/")
def read_root():
    """
    Root endpoint - API health check.
    """
    return {
        "message": "Добро пожаловать в LMS API для правоохранительной академии",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
