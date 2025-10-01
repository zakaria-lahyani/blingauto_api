"""
OpenAPI configuration and documentation.
According to TO_REFACTORE_ARCHITECTURE.md line 65.
"""

from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI


def custom_openapi(app: FastAPI):
    """
    Generate custom OpenAPI schema with proper documentation.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="BlingAuto Car Wash Management API",
        version="1.0.0",
        description="""
        ## Car Wash Management System API

        A comprehensive API for managing car wash business operations including:
        
        * **Authentication & Authorization** - User management with role-based access
        * **Booking Management** - Create, manage, and track car wash bookings
        * **Pricing & Quotes** - Calculate service prices and generate quotes
        * **Scheduling** - Resource allocation and availability management
        * **Vehicle Management** - Customer vehicle registration and management
        * **Service Management** - Service and category configuration
        
        ### Architecture
        
        Built with Clean Architecture principles:
        - Domain-driven design
        - Dependency inversion
        - Feature-based modular structure
        
        ### Authentication
        
        Uses JWT-based authentication with role-based access control:
        - **Admin**: Full system access
        - **Manager**: Business operations management
        - **Washer**: Service delivery operations
        - **Client**: Customer self-service portal
        """,
        routes=app.routes,
    )

    # Add custom tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "Health",
            "description": "System health and monitoring endpoints"
        },
        {
            "name": "Authentication", 
            "description": "User authentication and authorization"
        },
        {
            "name": "Bookings",
            "description": "Booking creation and management"
        },
        {
            "name": "Pricing",
            "description": "Price calculation and quotes"
        },
        {
            "name": "Scheduling",
            "description": "Resource scheduling and availability"
        },
        {
            "name": "Vehicles",
            "description": "Customer vehicle management"
        },
        {
            "name": "Services",
            "description": "Service and category management"
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def configure_openapi(app: FastAPI) -> None:
    """Configure OpenAPI documentation for the application."""
    app.openapi = lambda: custom_openapi(app)