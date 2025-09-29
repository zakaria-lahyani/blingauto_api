#!/usr/bin/env python3
"""
Simple test script for email verification system
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.features.auth.config import AuthConfig
from src.features.auth.auth_module import AuthModule
from src.shared.simple_database import init_database, create_tables


async def test_email_verification():
    """Test email verification system"""
    print("Car Wash API - Email Verification Test")
    print("=" * 50)
    
    # Initialize database
    print("Initializing database...")
    init_database()
    await create_tables()
    
    # Configure auth with mock email for testing
    print("Configuring auth module...")
    auth_config = AuthConfig(
        email_provider="mock",
        app_url="http://localhost:8000",
        from_email="test@carwash.com",
        support_email="support@carwash.com"
    )
    
    # Initialize auth module
    auth_module = AuthModule(auth_config)
    await auth_module.initialize()
    print("Auth module initialized successfully")
    
    # Test user data
    test_email = "test@example.com"
    test_password = "TestPassword123!"
    
    try:
        print(f"\nStep 1: Registering user {test_email}")
        
        # Register user (this should send verification email)
        user = await auth_module.auth_service.register_user(
            email=test_email,
            password=test_password,
            first_name="John",
            last_name="Doe",
            phone="+1234567890"
        )
        
        print(f"User registered with ID: {user.id}")
        print(f"Email verified status: {user.email_verified}")
        print(f"Has verification token: {bool(user.email_verification_token)}")
        
        # Check mock email
        from src.shared.services.email_service import get_email_service
        email_service = get_email_service()
        provider = email_service.get_provider()
        
        if hasattr(provider, 'get_sent_emails'):
            sent_emails = provider.get_sent_emails()
            print(f"Sent emails count: {len(sent_emails)}")
            
            if sent_emails:
                latest_email = sent_emails[-1]
                print(f"Latest email to: {latest_email['to']}")
                print(f"Subject: {latest_email['subject']}")
                
                # Extract token from email
                html_body = latest_email['html_body']
                if "token=" in html_body:
                    import re
                    token_match = re.search(r'token=([a-zA-Z0-9-_]+)', html_body)
                    if token_match:
                        verification_token = token_match.group(1)
                        print(f"Extracted token: {verification_token[:20]}...")
                        
                        print("\nStep 2: Verifying email with token")
                        
                        # Verify email
                        verified_user = await auth_module.email_verification_service.verify_email_with_token(verification_token)
                        
                        if verified_user:
                            print("Email verification successful!")
                            print(f"Email verified: {verified_user.email_verified}")
                            print(f"Verified at: {verified_user.email_verified_at}")
                        else:
                            print("Email verification failed")
                    else:
                        print("Could not extract token from email")
                else:
                    print("No verification token found in email")
        
        print("\nStep 3: Testing login")
        
        # Try to login after verification
        try:
            login_user, access_token, refresh_token = await auth_module.auth_service.authenticate_user(
                email=test_email,
                password=test_password
            )
            print("Login successful!")
            print(f"Access token: {access_token[:30]}...")
        except Exception as login_error:
            print(f"Login failed: {login_error}")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await auth_module.shutdown()
        print("Test completed")


async def test_smtp_config():
    """Test SMTP configuration"""
    print("\nTesting SMTP Configuration")
    print("=" * 50)
    
    smtp_config = AuthConfig(
        email_provider="smtp",
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="test@gmail.com",
        smtp_password="test-password",
        smtp_use_tls=True,
        from_email="test@gmail.com",
        app_url="https://mycompany.com"
    )
    
    print("SMTP config created successfully")
    print(f"Provider: {smtp_config.email_provider}")
    print(f"Host: {smtp_config.smtp_host}:{smtp_config.smtp_port}")
    print(f"TLS: {smtp_config.smtp_use_tls}")
    print(f"From: {smtp_config.from_email}")
    
    # Check production readiness
    is_ready, issues = smtp_config.is_production_ready()
    print(f"Production ready: {is_ready}")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"  - {issue}")


if __name__ == "__main__":
    asyncio.run(test_email_verification())
    asyncio.run(test_smtp_config())
    print("\nAll tests completed!")