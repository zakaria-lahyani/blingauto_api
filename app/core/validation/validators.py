"""
Comprehensive validation utilities for the car wash application.
Provides consistent validation across all features.
"""

import re
import phonenumbers
from datetime import datetime, date
from decimal import Decimal
from typing import Any, List, Optional, Union
from email_validator import validate_email, EmailNotValidError


class ValidationError(Exception):
    """Custom validation error."""
    
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class Validators:
    """Collection of validation utilities."""
    
    # Regex patterns
    LICENSE_PLATE_PATTERN = re.compile(r'^[A-Z0-9\-\s]{2,15}$')
    VIN_PATTERN = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')
    NAME_PATTERN = re.compile(r'^[a-zA-Z\s\-\.\']{2,50}$')
    
    # Vehicle data constants
    VALID_VEHICLE_TYPES = ['car', 'truck', 'suv', 'van', 'motorcycle', 'rv']
    VALID_VEHICLE_SIZES = ['compact', 'standard', 'large', 'oversized']
    
    # Service constraints
    MIN_SERVICE_PRICE = Decimal('5.00')
    MAX_SERVICE_PRICE = Decimal('1000.00')
    MIN_SERVICE_DURATION = 15  # minutes
    MAX_SERVICE_DURATION = 480  # minutes (8 hours)
    
    # Booking constraints
    MIN_BOOKING_ADVANCE_HOURS = 2
    MAX_BOOKING_ADVANCE_DAYS = 90
    MIN_BOOKING_DURATION = 30  # minutes
    MAX_BOOKING_DURATION = 480  # minutes
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address format."""
        if not email or not email.strip():
            raise ValidationError("Email is required", "email")
        
        try:
            validated_email = validate_email(email.strip())
            return validated_email.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email format: {str(e)}", "email")
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength."""
        if not password:
            raise ValidationError("Password is required", "password")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long", "password")
        
        if len(password) > 128:
            raise ValidationError("Password cannot exceed 128 characters", "password")
        
        # Check for at least one uppercase, one lowercase, one digit
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter", "password")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter", "password")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit", "password")
        
        return password
    
    @staticmethod
    def validate_name(name: str, field_name: str = "name") -> str:
        """Validate person name."""
        if not name or not name.strip():
            raise ValidationError(f"{field_name.title()} is required", field_name)
        
        name = name.strip()
        
        if len(name) < 2:
            raise ValidationError(f"{field_name.title()} must be at least 2 characters", field_name)
        
        if len(name) > 50:
            raise ValidationError(f"{field_name.title()} cannot exceed 50 characters", field_name)
        
        if not Validators.NAME_PATTERN.match(name):
            raise ValidationError(f"{field_name.title()} contains invalid characters", field_name)
        
        return name
    
    @staticmethod
    def validate_phone_number(phone: str, country_code: str = "US") -> Optional[str]:
        """Validate and format phone number."""
        if not phone or not phone.strip():
            return None
        
        try:
            parsed_number = phonenumbers.parse(phone.strip(), country_code)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError("Invalid phone number format", "phone_number")
            
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValidationError("Invalid phone number format", "phone_number")
    
    @staticmethod
    def validate_vehicle_make(make: str) -> str:
        """Validate vehicle make."""
        if not make or not make.strip():
            raise ValidationError("Vehicle make is required", "make")
        
        make = make.strip().title()
        
        if len(make) < 2:
            raise ValidationError("Vehicle make must be at least 2 characters", "make")
        
        if len(make) > 50:
            raise ValidationError("Vehicle make cannot exceed 50 characters", "make")
        
        return make
    
    @staticmethod
    def validate_vehicle_model(model: str) -> str:
        """Validate vehicle model."""
        if not model or not model.strip():
            raise ValidationError("Vehicle model is required", "model")
        
        model = model.strip()
        
        if len(model) < 1:
            raise ValidationError("Vehicle model is required", "model")
        
        if len(model) > 50:
            raise ValidationError("Vehicle model cannot exceed 50 characters", "model")
        
        return model
    
    @staticmethod
    def validate_vehicle_year(year: int) -> int:
        """Validate vehicle year."""
        current_year = datetime.now().year
        
        if year < 1900:
            raise ValidationError("Vehicle year cannot be before 1900", "year")
        
        if year > current_year + 2:
            raise ValidationError(f"Vehicle year cannot be more than {current_year + 2}", "year")
        
        return year
    
    @staticmethod
    def validate_license_plate(license_plate: str) -> str:
        """Validate license plate format."""
        if not license_plate or not license_plate.strip():
            raise ValidationError("License plate is required", "license_plate")
        
        license_plate = license_plate.strip().upper()
        
        if not Validators.LICENSE_PLATE_PATTERN.match(license_plate):
            raise ValidationError("Invalid license plate format", "license_plate")
        
        return license_plate
    
    @staticmethod
    def validate_vin(vin: str) -> Optional[str]:
        """Validate VIN (Vehicle Identification Number)."""
        if not vin or not vin.strip():
            return None
        
        vin = vin.strip().upper()
        
        if not Validators.VIN_PATTERN.match(vin):
            raise ValidationError("Invalid VIN format (must be 17 alphanumeric characters)", "vin")
        
        return vin
    
    @staticmethod
    def validate_vehicle_type(vehicle_type: str) -> str:
        """Validate vehicle type."""
        if not vehicle_type or not vehicle_type.strip():
            raise ValidationError("Vehicle type is required", "vehicle_type")
        
        vehicle_type = vehicle_type.strip().lower()
        
        if vehicle_type not in Validators.VALID_VEHICLE_TYPES:
            raise ValidationError(
                f"Invalid vehicle type. Must be one of: {', '.join(Validators.VALID_VEHICLE_TYPES)}",
                "vehicle_type"
            )
        
        return vehicle_type
    
    @staticmethod
    def validate_vehicle_size(vehicle_size: str) -> str:
        """Validate vehicle size."""
        if not vehicle_size or not vehicle_size.strip():
            raise ValidationError("Vehicle size is required", "vehicle_size")
        
        vehicle_size = vehicle_size.strip().lower()
        
        if vehicle_size not in Validators.VALID_VEHICLE_SIZES:
            raise ValidationError(
                f"Invalid vehicle size. Must be one of: {', '.join(Validators.VALID_VEHICLE_SIZES)}",
                "vehicle_size"
            )
        
        return vehicle_size
    
    @staticmethod
    def validate_color(color: str) -> str:
        """Validate vehicle color."""
        if not color or not color.strip():
            raise ValidationError("Vehicle color is required", "color")
        
        color = color.strip().title()
        
        if len(color) < 3:
            raise ValidationError("Vehicle color must be at least 3 characters", "color")
        
        if len(color) > 30:
            raise ValidationError("Vehicle color cannot exceed 30 characters", "color")
        
        return color
    
    @staticmethod
    def validate_service_price(price: Union[float, Decimal]) -> Decimal:
        """Validate service price."""
        if price is None:
            raise ValidationError("Service price is required", "price")
        
        try:
            price = Decimal(str(price))
        except (ValueError, TypeError):
            raise ValidationError("Invalid price format", "price")
        
        if price < Validators.MIN_SERVICE_PRICE:
            raise ValidationError(f"Service price must be at least ${Validators.MIN_SERVICE_PRICE}", "price")
        
        if price > Validators.MAX_SERVICE_PRICE:
            raise ValidationError(f"Service price cannot exceed ${Validators.MAX_SERVICE_PRICE}", "price")
        
        return price
    
    @staticmethod
    def validate_service_duration(duration: int) -> int:
        """Validate service duration in minutes."""
        if duration is None:
            raise ValidationError("Service duration is required", "duration_minutes")
        
        if not isinstance(duration, int) or duration <= 0:
            raise ValidationError("Service duration must be a positive integer", "duration_minutes")
        
        if duration < Validators.MIN_SERVICE_DURATION:
            raise ValidationError(f"Service duration must be at least {Validators.MIN_SERVICE_DURATION} minutes", "duration_minutes")
        
        if duration > Validators.MAX_SERVICE_DURATION:
            raise ValidationError(f"Service duration cannot exceed {Validators.MAX_SERVICE_DURATION} minutes", "duration_minutes")
        
        return duration
    
    @staticmethod
    def validate_booking_datetime(booking_datetime: datetime) -> datetime:
        """Validate booking date and time."""
        if not booking_datetime:
            raise ValidationError("Booking date and time is required", "scheduled_at")
        
        now = datetime.utcnow()
        
        # Check if in the past
        if booking_datetime <= now:
            raise ValidationError("Booking cannot be scheduled in the past", "scheduled_at")
        
        # Check minimum advance time
        min_advance = now.replace(hour=now.hour + Validators.MIN_BOOKING_ADVANCE_HOURS)
        if booking_datetime < min_advance:
            raise ValidationError(f"Booking must be at least {Validators.MIN_BOOKING_ADVANCE_HOURS} hours in advance", "scheduled_at")
        
        # Check maximum advance time
        max_advance = now.replace(day=now.day + Validators.MAX_BOOKING_ADVANCE_DAYS)
        if booking_datetime > max_advance:
            raise ValidationError(f"Booking cannot be more than {Validators.MAX_BOOKING_ADVANCE_DAYS} days in advance", "scheduled_at")
        
        return booking_datetime
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> tuple:
        """Validate GPS coordinates."""
        try:
            lat = float(latitude)
            lng = float(longitude)
        except (ValueError, TypeError):
            raise ValidationError("Invalid coordinate format", "location")
        
        if not (-90 <= lat <= 90):
            raise ValidationError("Latitude must be between -90 and 90", "latitude")
        
        if not (-180 <= lng <= 180):
            raise ValidationError("Longitude must be between -180 and 180", "longitude")
        
        return lat, lng
    
    @staticmethod
    def validate_uuid(uuid_str: str, field_name: str = "id") -> str:
        """Validate UUID format."""
        if not uuid_str or not uuid_str.strip():
            raise ValidationError(f"{field_name.title()} is required", field_name)
        
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        if not uuid_pattern.match(uuid_str.strip()):
            raise ValidationError(f"Invalid {field_name} format", field_name)
        
        return uuid_str.strip()
    
    @staticmethod
    def validate_pagination(page: int, limit: int) -> tuple:
        """Validate pagination parameters."""
        if page < 1:
            raise ValidationError("Page must be greater than 0", "page")
        
        if limit < 1:
            raise ValidationError("Limit must be greater than 0", "limit")
        
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100", "limit")
        
        return page, limit
    
    @staticmethod
    def validate_text_length(text: str, min_length: int, max_length: int, field_name: str, required: bool = True) -> Optional[str]:
        """Validate text length constraints."""
        if not text or not text.strip():
            if required:
                raise ValidationError(f"{field_name.title()} is required", field_name)
            return None
        
        text = text.strip()
        
        if len(text) < min_length:
            raise ValidationError(f"{field_name.title()} must be at least {min_length} characters", field_name)
        
        if len(text) > max_length:
            raise ValidationError(f"{field_name.title()} cannot exceed {max_length} characters", field_name)
        
        return text