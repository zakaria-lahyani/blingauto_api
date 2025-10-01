"""
BlingAuto API - Main application entry point
Car Wash Management System
"""

import uvicorn
from app.interfaces.http_api import create_app
from app.core.config.settings import settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        reload=settings.is_development,
        workers=settings.workers if not settings.is_development else 1,
    )