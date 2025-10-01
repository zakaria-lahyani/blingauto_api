from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from app.core.config import settings


def setup_cors(app):
    """Setup CORS middleware."""
    app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )