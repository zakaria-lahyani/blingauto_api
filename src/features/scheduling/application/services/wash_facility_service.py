"""
Wash facility management service
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Set
from uuid import UUID

from src.features.scheduling.domain.wash_facility_entities import (
    WashBay, MobileWashTeam, WashFacilityConfiguration, CapacityAllocation, WashType
)
from src.features.scheduling.infrastructure.database.wash_facility_repositories import (
    WashBayRepository, MobileWashTeamRepository, WashFacilityConfigurationRepository, CapacityAllocationRepository
)


class WashFacilityService:
    """Service for managing wash facility configuration and capacity"""
    
    def __init__(
        self,
        wash_bay_repo: WashBayRepository,
        mobile_team_repo: MobileWashTeamRepository,
        facility_config_repo: WashFacilityConfigurationRepository,
        capacity_allocation_repo: CapacityAllocationRepository
    ):
        self.wash_bay_repo = wash_bay_repo
        self.mobile_team_repo = mobile_team_repo
        self.facility_config_repo = facility_config_repo
        self.capacity_allocation_repo = capacity_allocation_repo
    
    async def create_wash_bay(
        self,
        name: str,
        bay_number: int,
        equipment_types: Optional[Set[str]] = None,
        max_vehicle_size: str = "standard",
        has_covered_area: bool = True,
        has_power_supply: bool = True,
        notes: Optional[str] = None
    ) -> WashBay:
        """Create a new wash bay"""
        wash_bay = WashBay(
            name=name,
            bay_number=bay_number,
            equipment_types=equipment_types,
            max_vehicle_size=max_vehicle_size,
            has_covered_area=has_covered_area,
            has_power_supply=has_power_supply,
            notes=notes
        )
        
        return await self.wash_bay_repo.create(wash_bay)
    
    async def create_mobile_wash_team(
        self,
        name: str,
        team_size: int,
        equipment_types: Optional[Set[str]] = None,
        service_radius_km: float = 50.0,
        max_vehicles_per_day: int = 8,
        hourly_rate: Optional[float] = None,
        base_location: Optional[Dict[str, float]] = None,
        notes: Optional[str] = None
    ) -> MobileWashTeam:
        """Create a new mobile wash team"""
        mobile_team = MobileWashTeam(
            name=name,
            team_size=team_size,
            equipment_types=equipment_types,
            service_radius_km=service_radius_km,
            max_vehicles_per_day=max_vehicles_per_day,
            hourly_rate=hourly_rate,
            base_location=base_location,
            notes=notes
        )
        
        return await self.mobile_team_repo.create(mobile_team)
    
    async def get_all_wash_bays(self, active_only: bool = True) -> List[WashBay]:
        """Get all wash bays"""
        return await self.wash_bay_repo.get_all(active_only=active_only)
    
    async def get_all_mobile_teams(self, active_only: bool = True) -> List[MobileWashTeam]:
        """Get all mobile teams"""
        return await self.mobile_team_repo.get_all(active_only=active_only)
    
    async def get_wash_bay(self, bay_id: UUID) -> Optional[WashBay]:
        """Get wash bay by ID"""
        return await self.wash_bay_repo.get_by_id(bay_id)
    
    async def get_mobile_team(self, team_id: UUID) -> Optional[MobileWashTeam]:
        """Get mobile team by ID"""
        return await self.mobile_team_repo.get_by_id(team_id)
    
    async def update_wash_bay(self, wash_bay: WashBay) -> WashBay:
        """Update wash bay"""
        return await self.wash_bay_repo.update(wash_bay)
    
    async def update_mobile_team(self, mobile_team: MobileWashTeam) -> MobileWashTeam:
        """Update mobile team"""
        return await self.mobile_team_repo.update(mobile_team)
    
    async def delete_wash_bay(self, bay_id: UUID) -> bool:
        """Delete wash bay"""
        return await self.wash_bay_repo.delete(bay_id)
    
    async def delete_mobile_team(self, team_id: UUID) -> bool:
        """Delete mobile team"""
        return await self.mobile_team_repo.delete(team_id)
    
    async def get_available_wash_bays_for_vehicle(self, vehicle_size: str) -> List[WashBay]:
        """Get wash bays that can accommodate vehicle size"""
        return await self.wash_bay_repo.get_available_for_vehicle_size(vehicle_size)
    
    async def get_facility_configuration(self) -> Optional[WashFacilityConfiguration]:
        """Get current facility configuration"""
        return await self.facility_config_repo.get_current_configuration()
    
    async def update_facility_configuration(
        self,
        facility_name: str,
        operating_hours: Optional[Dict] = None,
        default_service_duration_minutes: int = 60,
        buffer_between_services_minutes: int = 15,
        max_advance_booking_days: int = 30
    ) -> WashFacilityConfiguration:
        """Update facility configuration"""
        # Get current counts
        wash_bays = await self.get_all_wash_bays(active_only=True)
        mobile_teams = await self.get_all_mobile_teams(active_only=True)
        
        configuration = WashFacilityConfiguration(
            facility_name=facility_name,
            total_wash_bays=len(wash_bays),
            total_mobile_teams=len(mobile_teams),
            operating_hours=operating_hours,
            default_service_duration_minutes=default_service_duration_minutes,
            buffer_between_services_minutes=buffer_between_services_minutes,
            max_advance_booking_days=max_advance_booking_days
        )
        
        return await self.facility_config_repo.create_or_update(configuration)
    
    async def get_capacity_for_date_and_resource(
        self,
        date: datetime,
        resource_id: UUID,
        wash_type: WashType
    ) -> Optional[CapacityAllocation]:
        """Get capacity allocation for specific date and resource"""
        return await self.capacity_allocation_repo.get_allocation_for_date_and_resource(
            date=date,
            resource_id=resource_id,
            wash_type=wash_type
        )
    
    async def allocate_capacity(
        self,
        date: datetime,
        wash_type: WashType,
        resource_id: UUID,
        resource_name: str,
        booking_id: UUID,
        max_capacity: int = 1
    ) -> bool:
        """Allocate capacity for a booking"""
        allocation = await self.get_capacity_for_date_and_resource(date, resource_id, wash_type)
        
        if not allocation:
            # Create new allocation
            allocation = CapacityAllocation(
                date=date,
                wash_type=wash_type,
                resource_id=resource_id,
                resource_name=resource_name,
                max_capacity=max_capacity
            )
        
        if allocation.allocate_slot(booking_id):
            await self.capacity_allocation_repo.create_or_update_allocation(allocation)
            return True
        
        return False
    
    async def release_capacity(
        self,
        date: datetime,
        wash_type: WashType,
        resource_id: UUID,
        booking_id: UUID
    ) -> bool:
        """Release capacity for a booking"""
        allocation = await self.get_capacity_for_date_and_resource(date, resource_id, wash_type)
        
        if allocation and allocation.release_slot(booking_id):
            await self.capacity_allocation_repo.create_or_update_allocation(allocation)
            return True
        
        return False
    
    async def get_daily_capacity_summary(self, date: datetime) -> Dict[str, Dict]:
        """Get daily capacity summary for all resources"""
        return await self.capacity_allocation_repo.get_daily_capacity_summary(date)
    
    async def find_best_resource_for_booking(
        self,
        wash_type: WashType,
        date: datetime,
        required_equipment: Optional[Set[str]] = None,
        vehicle_size: str = "standard",
        customer_location: Optional[Dict[str, float]] = None
    ) -> Optional[object]:
        """Find the best available resource for a booking"""
        if wash_type == WashType.STATIONARY:
            # Find available wash bays
            suitable_bays = await self.get_available_wash_bays_for_vehicle(vehicle_size)
            
            # Filter by equipment if required
            if required_equipment:
                suitable_bays = [bay for bay in suitable_bays if bay.has_equipment(required_equipment)]
            
            # Check capacity for each bay
            for bay in suitable_bays:
                allocation = await self.get_capacity_for_date_and_resource(
                    date=date,
                    resource_id=bay.id,
                    wash_type=wash_type
                )
                
                if not allocation or allocation.is_available():
                    return bay
        
        elif wash_type == WashType.MOBILE:
            # Find available mobile teams
            suitable_teams = await self.get_all_mobile_teams(active_only=True)
            
            # Filter by location and equipment
            filtered_teams = []
            for team in suitable_teams:
                if customer_location and not team.can_service_location(customer_location):
                    continue
                if required_equipment and not team.has_equipment(required_equipment):
                    continue
                filtered_teams.append(team)
            
            # Check capacity for each team
            for team in filtered_teams:
                allocation = await self.get_capacity_for_date_and_resource(
                    date=date,
                    resource_id=team.id,
                    wash_type=wash_type
                )
                
                if not allocation or allocation.is_available():
                    return team
        
        return None
    
    async def get_facility_capacity_overview(self) -> Dict:
        """Get overview of facility capacity"""
        wash_bays = await self.get_all_wash_bays(active_only=True)
        mobile_teams = await self.get_all_mobile_teams(active_only=True)
        configuration = await self.get_facility_configuration()
        
        return {
            "total_wash_bays": len(wash_bays),
            "active_wash_bays": len([bay for bay in wash_bays if bay.is_active]),
            "total_mobile_teams": len(mobile_teams),
            "active_mobile_teams": len([team for team in mobile_teams if team.is_active]),
            "facility_name": configuration.facility_name if configuration else "Not configured",
            "max_advance_booking_days": configuration.max_advance_booking_days if configuration else 30,
            "default_service_duration": configuration.default_service_duration_minutes if configuration else 60,
            "buffer_between_services": configuration.buffer_between_services_minutes if configuration else 15
        }