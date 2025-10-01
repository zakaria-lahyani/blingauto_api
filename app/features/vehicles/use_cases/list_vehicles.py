from dataclasses import dataclass
from typing import List, Optional

from app.core.errors import ValidationError
from app.features.vehicles.domain import Vehicle
from app.features.vehicles.ports import (
    IVehicleRepository,
    ICacheService,
)


@dataclass
class ListVehiclesRequest:
    customer_id: str
    include_deleted: bool = False
    page: int = 1
    limit: int = 20


@dataclass
class VehicleSummary:
    id: str
    make: str
    model: str
    year: int
    color: str
    license_plate: str
    is_default: bool
    is_deleted: bool
    display_name: str
    created_at: str


@dataclass
class ListVehiclesResponse:
    vehicles: List[VehicleSummary]
    total_count: int
    page: int
    limit: int
    has_next: bool
    default_vehicle_id: Optional[str] = None


class ListVehiclesUseCase:
    """Use case for listing customer vehicles."""
    
    def __init__(
        self,
        vehicle_repository: IVehicleRepository,
        cache_service: ICacheService,
    ):
        self._vehicle_repository = vehicle_repository
        self._cache_service = cache_service
    
    def execute(self, request: ListVehiclesRequest) -> ListVehiclesResponse:
        """Execute the list vehicles use case."""
        
        # Step 1: Validate pagination parameters
        if request.page < 1:
            raise ValidationError("Page must be greater than 0")
        if request.limit < 1 or request.limit > 100:
            raise ValidationError("Limit must be between 1 and 100")
        
        # Step 2: Calculate offset
        offset = (request.page - 1) * request.limit
        
        # Step 3: Try to get from cache first (for active vehicles only)
        cached_vehicles = None
        if not request.include_deleted and request.page == 1 and request.limit <= 20:
            cached_vehicles = self._cache_service.get_customer_vehicles(
                request.customer_id, include_deleted=False
            )
        
        if cached_vehicles is not None:
            # Use cached data
            vehicles = cached_vehicles
            total_count = len(vehicles)
            
            # Apply pagination to cached results
            paginated_vehicles = vehicles[offset:offset + request.limit]
        else:
            # Get from repository
            vehicles = self._vehicle_repository.list_by_customer(
                customer_id=request.customer_id,
                include_deleted=request.include_deleted,
                offset=offset,
                limit=request.limit,
            )
            
            # Get total count
            total_count = self._vehicle_repository.count_by_customer(
                request.customer_id, request.include_deleted
            )
            
            paginated_vehicles = vehicles
            
            # Cache active vehicles for future requests
            if not request.include_deleted and request.page == 1:
                all_active_vehicles = self._vehicle_repository.list_by_customer(
                    request.customer_id, include_deleted=False
                )
                self._cache_service.set_customer_vehicles(
                    request.customer_id, all_active_vehicles, include_deleted=False
                )
        
        # Step 4: Convert to summary format
        vehicle_summaries = [
            VehicleSummary(
                id=vehicle.id,
                make=vehicle.make,
                model=vehicle.model,
                year=vehicle.year,
                color=vehicle.color,
                license_plate=vehicle.license_plate,
                is_default=vehicle.is_default,
                is_deleted=vehicle.is_deleted,
                display_name=vehicle.display_name,
                created_at=vehicle.created_at.isoformat(),
            )
            for vehicle in paginated_vehicles
        ]
        
        # Step 5: Find default vehicle
        default_vehicle_id = None
        if not request.include_deleted:
            # Look for default in current page
            default_in_page = next((v for v in paginated_vehicles if v.is_default), None)
            if default_in_page:
                default_vehicle_id = default_in_page.id
            else:
                # Get default vehicle separately if not in current page
                default_vehicle = self._vehicle_repository.get_default_vehicle(request.customer_id)
                if default_vehicle:
                    default_vehicle_id = default_vehicle.id
        
        # Step 6: Calculate pagination info
        has_next = (offset + len(paginated_vehicles)) < total_count
        
        return ListVehiclesResponse(
            vehicles=vehicle_summaries,
            total_count=total_count,
            page=request.page,
            limit=request.limit,
            has_next=has_next,
            default_vehicle_id=default_vehicle_id,
        )