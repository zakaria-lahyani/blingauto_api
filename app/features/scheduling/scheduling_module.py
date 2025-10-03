"""
Scheduling Feature Module.
Complete implementation of facility scheduling and resource management.
"""

from typing import Dict, Any

# Domain exports
from .domain.entities import (
    WashBay, MobileTeam, TimeSlot, SchedulingConstraints,
    VehicleSize, ResourceType, ResourceStatus, DayOfWeek,
    Location, BusinessHours
)
from .domain.policies import (
    ResourceAllocationPolicy, AvailabilityPolicy, 
    OptimizationPolicy, CapacityPolicy
)

# Use case exports
from .use_cases.check_availability import CheckAvailabilityUseCase, GetAvailableSlotsUseCase
from .use_cases.manage_resources import (
    CreateWashBayUseCase, CreateMobileTeamUseCase,
    UpdateWashBayUseCase, UpdateMobileTeamUseCase,
    ListResourcesUseCase, DeleteResourceUseCase
)
from .use_cases.manage_slots import (
    BookSlotUseCase, CancelSlotUseCase, RescheduleSlotUseCase
)

# Port exports
from .ports.repositories import (
    IWashBayRepository, IMobileTeamRepository,
    ITimeSlotRepository, ISchedulingConstraintsRepository
)
from .ports.services import IDistanceCalculationService

# Infrastructure exports
from app.features.scheduling.adapters.models import (
    TimeSlot as TimeSlotModel, SchedulingConstraints as ConstraintsModel,
    BusinessHours as BusinessHoursModel
)
# WashBay and MobileTeam models belong to facilities feature
from app.features.facilities.adapters.models import (
    WashBayModel, MobileTeamModel
)
from .adapters.repositories import (
    WashBayRepository, MobileTeamRepository,
    TimeSlotRepository, SchedulingConstraintsRepository
)

# API exports
from .api.router import router as scheduling_router
from .api.schemas import (
    AvailabilityCheckRequest, AvailabilityCheckResponse,
    GetSlotsRequest, GetSlotsResponse,
    LocationSchema, TimeSlotSchema,
    WashBaySchema, MobileTeamSchema, ResourceListResponse,
    BookingSlotRequest, BookingSlotResponse
)


class SchedulingFeature:
    """
    Scheduling feature module providing resource management and availability checking.
    
    This feature implements:
    - RG-FAC-001: Wash bay facility management
    - RG-FAC-002: Vehicle size constraints  
    - RG-FAC-003: Mobile team management
    - RG-FAC-004: Service radius limitations
    - RG-SCH-001: Business hours and constraints
    - RG-SCH-002: Advance booking requirements
    """
    
    def __init__(self):
        self.name = "scheduling"
        self.version = "1.0.0"
        self.description = "Facility scheduling and resource management"
    
    def get_router(self):
        """Get the API router for this feature."""
        return scheduling_router
    
    def get_models(self):
        """Get the database models for this feature."""
        return [
            WashBayModel,
            MobileTeamModel, 
            TimeSlotModel,
            ConstraintsModel,
            BusinessHoursModel
        ]
    
    def get_use_cases(self) -> Dict[str, Any]:
        """Get all use cases for dependency injection."""
        return {
            # Availability checking
            "check_availability": CheckAvailabilityUseCase,
            "get_available_slots": GetAvailableSlotsUseCase,
            
            # Resource management
            "create_wash_bay": CreateWashBayUseCase,
            "create_mobile_team": CreateMobileTeamUseCase,
            "update_wash_bay": UpdateWashBayUseCase,
            "update_mobile_team": UpdateMobileTeamUseCase,
            "list_resources": ListResourcesUseCase,
            "delete_resource": DeleteResourceUseCase,
            
            # Slot management
            "book_slot": BookSlotUseCase,
            "cancel_slot": CancelSlotUseCase,
            "reschedule_slot": RescheduleSlotUseCase,
        }
    
    def get_repositories(self) -> Dict[str, Any]:
        """Get all repositories for dependency injection."""
        return {
            "wash_bay_repository": WashBayRepository,
            "mobile_team_repository": MobileTeamRepository,
            "time_slot_repository": TimeSlotRepository,
            "scheduling_constraints_repository": SchedulingConstraintsRepository,
        }


# Module instance for easy import
scheduling_feature = SchedulingFeature()

__all__ = [
    # Feature module
    "SchedulingFeature",
    "scheduling_feature",
    
    # Domain
    "WashBay", "MobileTeam", "TimeSlot", "SchedulingConstraints",
    "VehicleSize", "ResourceType", "ResourceStatus", "DayOfWeek",
    "Location", "BusinessHours",
    
    # Policies
    "ResourceAllocationPolicy", "AvailabilityPolicy", 
    "OptimizationPolicy", "CapacityPolicy",
    
    # Use cases
    "CheckAvailabilityUseCase", "GetAvailableSlotsUseCase",
    "CreateWashBayUseCase", "CreateMobileTeamUseCase",
    "UpdateWashBayUseCase", "UpdateMobileTeamUseCase",
    "ListResourcesUseCase", "DeleteResourceUseCase",
    "BookSlotUseCase", "CancelSlotUseCase", "RescheduleSlotUseCase",
    
    # Ports
    "IWashBayRepository", "IMobileTeamRepository",
    "ITimeSlotRepository", "ISchedulingConstraintsRepository",
    "IDistanceCalculationService",
    
    # Infrastructure
    "WashBayModel", "MobileTeamModel", "TimeSlotModel",
    "ConstraintsModel", "BusinessHoursModel",
    "WashBayRepository", "MobileTeamRepository",
    "TimeSlotRepository", "SchedulingConstraintsRepository",
    
    # API
    "scheduling_router",
    "AvailabilityCheckRequest", "AvailabilityCheckResponse",
    "GetSlotsRequest", "GetSlotsResponse",
    "LocationSchema", "TimeSlotSchema",
    "WashBaySchema", "MobileTeamSchema", "ResourceListResponse",
    "BookingSlotRequest", "BookingSlotResponse",
]