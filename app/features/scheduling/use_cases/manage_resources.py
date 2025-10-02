"""
Resource Management Use Cases for Scheduling Feature.
Implements facility management rules RG-FAC-001 to RG-FAC-004.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from decimal import Decimal

from app.core.errors import NotFoundError, ValidationError, BusinessRuleViolationError
from ..domain.entities import WashBay, MobileTeam, VehicleSize, ResourceStatus, Location
from ..domain.policies import ResourceAllocationPolicy, CapacityPolicy
from ..ports.repositories import IWashBayRepository, IMobileTeamRepository, ITimeSlotRepository


@dataclass
class CreateWashBayRequest:
    bay_number: str
    max_vehicle_size: VehicleSize
    equipment_types: List[str] = None
    location: Optional[Location] = None


@dataclass
class CreateWashBayResponse:
    bay_id: str
    bay_number: str
    max_vehicle_size: str
    equipment_types: List[str]
    status: str


@dataclass
class CreateMobileTeamRequest:
    team_name: str
    base_location: Location
    service_radius_km: Decimal = Decimal('50')
    daily_capacity: int = 8
    equipment_types: List[str] = None


@dataclass
class CreateMobileTeamResponse:
    team_id: str
    team_name: str
    base_location: Dict[str, float]
    service_radius_km: float
    daily_capacity: int
    equipment_types: List[str]
    status: str


@dataclass
class ListResourcesRequest:
    resource_type: Optional[str] = None  # wash_bay, mobile_team, or None for all
    status_filter: Optional[str] = None
    location_filter: Optional[Location] = None
    radius_km: Optional[Decimal] = None


@dataclass
class ResourceSummary:
    id: str
    type: str
    name: str
    status: str
    utilization: float
    location: Optional[Dict[str, float]] = None


@dataclass
class ListResourcesResponse:
    resources: List[ResourceSummary]
    total_count: int


class CreateWashBayUseCase:
    """Use case for creating new wash bay resources."""
    
    def __init__(self, wash_bay_repository: IWashBayRepository):
        self._wash_bay_repository = wash_bay_repository
    
    def execute(self, request: CreateWashBayRequest) -> CreateWashBayResponse:
        """Execute create wash bay use case."""
        
        # Create wash bay entity with validation
        wash_bay = WashBay.create(
            bay_number=request.bay_number,
            max_vehicle_size=request.max_vehicle_size,
            equipment_types=request.equipment_types or [],
            location=request.location
        )
        
        # Save to repository
        saved_bay = self._wash_bay_repository.create(wash_bay)
        
        return CreateWashBayResponse(
            bay_id=saved_bay.id,
            bay_number=saved_bay.bay_number,
            max_vehicle_size=saved_bay.max_vehicle_size.value,
            equipment_types=saved_bay.equipment_types,
            status=saved_bay.status.value
        )


class CreateMobileTeamUseCase:
    """Use case for creating new mobile team resources."""
    
    def __init__(self, mobile_team_repository: IMobileTeamRepository):
        self._mobile_team_repository = mobile_team_repository
    
    def execute(self, request: CreateMobileTeamRequest) -> CreateMobileTeamResponse:
        """Execute create mobile team use case."""
        
        # Create mobile team entity with validation
        mobile_team = MobileTeam.create(
            team_name=request.team_name,
            base_location=request.base_location,
            service_radius_km=request.service_radius_km,
            daily_capacity=request.daily_capacity,
            equipment_types=request.equipment_types or []
        )
        
        # Save to repository
        saved_team = self._mobile_team_repository.create(mobile_team)
        
        return CreateMobileTeamResponse(
            team_id=saved_team.id,
            team_name=saved_team.team_name,
            base_location={
                "latitude": float(saved_team.base_location.latitude),
                "longitude": float(saved_team.base_location.longitude)
            },
            service_radius_km=float(saved_team.service_radius_km),
            daily_capacity=saved_team.daily_capacity,
            equipment_types=saved_team.equipment_types,
            status=saved_team.status.value
        )


class UpdateWashBayUseCase:
    """Use case for updating wash bay resources."""
    
    def __init__(self, wash_bay_repository: IWashBayRepository):
        self._wash_bay_repository = wash_bay_repository
    
    def execute(self, bay_id: str, updates: Dict[str, Any]) -> CreateWashBayResponse:
        """Execute update wash bay use case."""
        
        # Get existing wash bay
        wash_bay = self._wash_bay_repository.get_by_id(bay_id)
        if not wash_bay:
            raise NotFoundError(f"Wash bay {bay_id} not found")
        
        # Apply updates
        if 'bay_number' in updates:
            wash_bay.bay_number = updates['bay_number']
        
        if 'max_vehicle_size' in updates:
            try:
                wash_bay.max_vehicle_size = VehicleSize(updates['max_vehicle_size'])
            except ValueError:
                raise ValidationError(f"Invalid vehicle size: {updates['max_vehicle_size']}")
        
        if 'equipment_types' in updates:
            wash_bay.equipment_types = updates['equipment_types']
        
        if 'status' in updates:
            try:
                wash_bay.status = ResourceStatus(updates['status'])
            except ValueError:
                raise ValidationError(f"Invalid status: {updates['status']}")
        
        wash_bay.updated_at = datetime.now(timezone.utc)
        
        # Save changes
        updated_bay = self._wash_bay_repository.update(wash_bay)
        
        return CreateWashBayResponse(
            bay_id=updated_bay.id,
            bay_number=updated_bay.bay_number,
            max_vehicle_size=updated_bay.max_vehicle_size.value,
            equipment_types=updated_bay.equipment_types,
            status=updated_bay.status.value
        )


class UpdateMobileTeamUseCase:
    """Use case for updating mobile team resources."""
    
    def __init__(self, mobile_team_repository: IMobileTeamRepository):
        self._mobile_team_repository = mobile_team_repository
    
    def execute(self, team_id: str, updates: Dict[str, Any]) -> CreateMobileTeamResponse:
        """Execute update mobile team use case."""
        
        # Get existing mobile team
        mobile_team = self._mobile_team_repository.get_by_id(team_id)
        if not mobile_team:
            raise NotFoundError(f"Mobile team {team_id} not found")
        
        # Apply updates
        if 'team_name' in updates:
            mobile_team.team_name = updates['team_name']
        
        if 'service_radius_km' in updates:
            mobile_team.service_radius_km = Decimal(str(updates['service_radius_km']))
        
        if 'daily_capacity' in updates:
            mobile_team.daily_capacity = updates['daily_capacity']
        
        if 'equipment_types' in updates:
            mobile_team.equipment_types = updates['equipment_types']
        
        if 'status' in updates:
            try:
                mobile_team.status = ResourceStatus(updates['status'])
            except ValueError:
                raise ValidationError(f"Invalid status: {updates['status']}")
        
        mobile_team.updated_at = datetime.now(timezone.utc)
        
        # Save changes
        updated_team = self._mobile_team_repository.update(mobile_team)
        
        return CreateMobileTeamResponse(
            team_id=updated_team.id,
            team_name=updated_team.team_name,
            base_location={
                "latitude": float(updated_team.base_location.latitude),
                "longitude": float(updated_team.base_location.longitude)
            },
            service_radius_km=float(updated_team.service_radius_km),
            daily_capacity=updated_team.daily_capacity,
            equipment_types=updated_team.equipment_types,
            status=updated_team.status.value
        )


class ListResourcesUseCase:
    """Use case for listing and filtering resources."""
    
    def __init__(
        self,
        wash_bay_repository: IWashBayRepository,
        mobile_team_repository: IMobileTeamRepository,
        time_slot_repository: ITimeSlotRepository
    ):
        self._wash_bay_repository = wash_bay_repository
        self._mobile_team_repository = mobile_team_repository
        self._time_slot_repository = time_slot_repository
    
    def execute(self, request: ListResourcesRequest) -> ListResourcesResponse:
        """Execute list resources use case."""
        
        resources = []
        
        # Get wash bays if requested
        if not request.resource_type or request.resource_type == "wash_bay":
            wash_bays = self._wash_bay_repository.get_all_active()
            
            for bay in wash_bays:
                # Apply status filter
                if request.status_filter and bay.status.value != request.status_filter:
                    continue
                
                # Calculate utilization
                utilization = self._calculate_wash_bay_utilization(bay)
                
                resources.append(ResourceSummary(
                    id=bay.id,
                    type="wash_bay",
                    name=f"Bay {bay.bay_number}",
                    status=bay.status.value,
                    utilization=utilization,
                    location={
                        "latitude": float(bay.location.latitude),
                        "longitude": float(bay.location.longitude)
                    } if bay.location else None
                ))
        
        # Get mobile teams if requested
        if not request.resource_type or request.resource_type == "mobile_team":
            mobile_teams = self._mobile_team_repository.get_all_active()
            
            for team in mobile_teams:
                # Apply status filter
                if request.status_filter and team.status.value != request.status_filter:
                    continue
                
                # Apply location filter
                if request.location_filter and request.radius_km:
                    distance = team.base_location.distance_to(request.location_filter)
                    if distance > request.radius_km:
                        continue
                
                # Calculate utilization
                utilization = self._calculate_mobile_team_utilization(team)
                
                resources.append(ResourceSummary(
                    id=team.id,
                    type="mobile_team",
                    name=team.team_name,
                    status=team.status.value,
                    utilization=utilization,
                    location={
                        "latitude": float(team.base_location.latitude),
                        "longitude": float(team.base_location.longitude)
                    }
                ))
        
        return ListResourcesResponse(
            resources=resources,
            total_count=len(resources)
        )
    
    def _calculate_wash_bay_utilization(self, wash_bay: WashBay) -> float:
        """Calculate wash bay utilization for today."""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_bookings = self._time_slot_repository.get_bookings_for_resource(
            wash_bay.id, today, today.replace(hour=23, minute=59, second=59)
        )
        
        return CapacityPolicy.get_capacity_utilization(wash_bay, today, today_bookings)
    
    def _calculate_mobile_team_utilization(self, mobile_team: MobileTeam) -> float:
        """Calculate mobile team utilization for today."""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_bookings = self._time_slot_repository.get_bookings_for_resource(
            mobile_team.id, today, today.replace(hour=23, minute=59, second=59)
        )
        
        return CapacityPolicy.get_capacity_utilization(mobile_team, today, today_bookings)


class DeleteResourceUseCase:
    """Use case for deactivating resources."""
    
    def __init__(
        self,
        wash_bay_repository: IWashBayRepository,
        mobile_team_repository: IMobileTeamRepository,
        time_slot_repository: ITimeSlotRepository
    ):
        self._wash_bay_repository = wash_bay_repository
        self._mobile_team_repository = mobile_team_repository
        self._time_slot_repository = time_slot_repository
    
    def execute(self, resource_id: str, resource_type: str) -> bool:
        """Execute delete resource use case."""
        
        # Check for active bookings
        future_bookings = self._time_slot_repository.get_bookings_for_resource(
            resource_id,
            datetime.now(timezone.utc),
            datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)
        )
        
        if future_bookings:
            raise BusinessRuleViolationError(
                f"Cannot delete resource with {len(future_bookings)} active future bookings"
            )
        
        if resource_type == "wash_bay":
            wash_bay = self._wash_bay_repository.get_by_id(resource_id)
            if not wash_bay:
                raise NotFoundError(f"Wash bay {resource_id} not found")
            
            wash_bay.deactivate()
            self._wash_bay_repository.update(wash_bay)
            return True
        
        elif resource_type == "mobile_team":
            mobile_team = self._mobile_team_repository.get_by_id(resource_id)
            if not mobile_team:
                raise NotFoundError(f"Mobile team {resource_id} not found")
            
            mobile_team.status = ResourceStatus.INACTIVE
            mobile_team.updated_at = datetime.now(timezone.utc)
            self._mobile_team_repository.update(mobile_team)
            return True
        
        else:
            raise ValidationError(f"Invalid resource type: {resource_type}")