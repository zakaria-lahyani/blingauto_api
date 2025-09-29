"""
Scheduling Feature Configuration
"""
from typing import List, Optional, Dict, Set
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from datetime import time


class SchedulingConfig(BaseSettings):
    """Scheduling feature specific configuration"""
    
    # Feature settings
    table_prefix: str = Field(default="schedule_", description="Table prefix for scheduling tables")
    cache_key_prefix: str = Field(default="schedule", description="Cache key prefix")
    
    # Scheduling engine
    enable_auto_scheduling: bool = Field(default=True, description="Enable automatic scheduling")
    scheduling_algorithm: str = Field(default="first_fit", description="Scheduling algorithm: first_fit, best_fit, round_robin")
    max_scheduling_attempts: int = Field(default=5, description="Max attempts to find a schedule slot")
    
    # Time slot management
    slot_duration_minutes: int = Field(default=30, description="Default time slot duration")
    min_slot_duration_minutes: int = Field(default=15, description="Minimum time slot duration")
    max_slot_duration_minutes: int = Field(default=480, description="Maximum time slot duration (8 hours)")
    slot_buffer_minutes: int = Field(default=5, description="Buffer time between slots")
    
    # Worker management
    max_workers: int = Field(default=10, description="Maximum number of workers")
    min_workers_required: int = Field(default=1, description="Minimum workers required for operation")
    enable_worker_specialization: bool = Field(default=True, description="Enable worker skill specialization")
    auto_assign_workers: bool = Field(default=True, description="Auto-assign workers to slots")
    
    # Shift management
    default_shift_hours: int = Field(default=8, description="Default shift duration in hours")
    min_shift_hours: int = Field(default=4, description="Minimum shift duration")
    max_shift_hours: int = Field(default=12, description="Maximum shift duration")
    break_duration_minutes: int = Field(default=30, description="Break duration in minutes")
    breaks_per_shift: int = Field(default=1, description="Number of breaks per shift")
    
    # Availability patterns
    default_availability_pattern: str = Field(default="weekdays", description="Default availability: weekdays, weekends, daily")
    allow_split_shifts: bool = Field(default=False, description="Allow workers to have split shifts")
    require_consecutive_slots: bool = Field(default=False, description="Require consecutive time slots for workers")
    
    # Overtime and constraints
    enable_overtime: bool = Field(default=True, description="Allow overtime scheduling")
    max_overtime_hours_per_day: int = Field(default=4, description="Max overtime hours per day")
    max_overtime_hours_per_week: int = Field(default=10, description="Max overtime hours per week")
    overtime_premium_rate: float = Field(default=1.5, description="Overtime pay rate multiplier")
    
    # Schedule optimization
    optimize_for: str = Field(default="efficiency", description="Optimization target: efficiency, cost, worker_satisfaction")
    consider_worker_preferences: bool = Field(default=True, description="Consider worker time preferences")
    minimize_schedule_gaps: bool = Field(default=True, description="Minimize gaps in schedules")
    balance_workload: bool = Field(default=True, description="Balance workload across workers")
    
    # Skills and qualifications
    require_skill_matching: bool = Field(default=True, description="Require skill matching for assignments")
    allow_skill_upgrades: bool = Field(default=True, description="Allow workers to be assigned above their skill level")
    skill_levels: List[str] = Field(
        default=["trainee", "junior", "senior", "specialist", "supervisor"],
        description="Available skill levels"
    )
    
    # Schedule changes
    allow_schedule_modifications: bool = Field(default=True, description="Allow schedule modifications")
    min_notice_hours_for_changes: int = Field(default=24, description="Minimum notice for schedule changes")
    auto_notify_schedule_changes: bool = Field(default=True, description="Auto-notify workers of changes")
    
    # Recurring schedules
    enable_recurring_schedules: bool = Field(default=True, description="Enable recurring schedule patterns")
    max_recurrence_weeks: int = Field(default=52, description="Maximum weeks for recurring schedules")
    auto_generate_future_schedules: bool = Field(default=True, description="Auto-generate future schedules")
    schedule_generation_weeks_ahead: int = Field(default=4, description="Weeks ahead to generate schedules")
    
    # Conflict resolution
    auto_resolve_conflicts: bool = Field(default=True, description="Auto-resolve scheduling conflicts")
    conflict_resolution_strategy: str = Field(default="priority", description="Conflict resolution: priority, seniority, random")
    notify_scheduling_conflicts: bool = Field(default=True, description="Notify about conflicts")
    
    # Performance and caching
    cache_schedules_ttl: int = Field(default=1800, description="Cache TTL for schedules (30 min)")
    cache_availability_ttl: int = Field(default=300, description="Cache TTL for worker availability")
    cache_assignments_ttl: int = Field(default=600, description="Cache TTL for worker assignments")
    
    # Reporting and analytics
    track_schedule_efficiency: bool = Field(default=True, description="Track scheduling efficiency metrics")
    track_worker_utilization: bool = Field(default=True, description="Track worker utilization rates")
    generate_schedule_reports: bool = Field(default=True, description="Generate scheduling reports")
    
    # Audit and compliance
    track_schedule_changes: bool = Field(default=True, description="Track all schedule modifications")
    log_assignment_reasons: bool = Field(default=True, description="Log reasons for worker assignments")
    enforce_labor_law_compliance: bool = Field(default=True, description="Enforce labor law constraints")
    
    class Config:
        env_prefix = "SCHEDULING_"
        extra = "ignore"
    
    @validator("scheduling_algorithm")
    def validate_algorithm(cls, v):
        """Validate scheduling algorithm"""
        valid_algorithms = ["first_fit", "best_fit", "round_robin", "priority_based"]
        if v not in valid_algorithms:
            raise ValueError(f"Scheduling algorithm must be one of: {valid_algorithms}")
        return v
    
    @validator("optimize_for")
    def validate_optimization_target(cls, v):
        """Validate optimization target"""
        valid_targets = ["efficiency", "cost", "worker_satisfaction", "customer_satisfaction"]
        if v not in valid_targets:
            raise ValueError(f"Optimization target must be one of: {valid_targets}")
        return v
    
    @validator("conflict_resolution_strategy")
    def validate_conflict_strategy(cls, v):
        """Validate conflict resolution strategy"""
        valid_strategies = ["priority", "seniority", "random", "skill_based"]
        if v not in valid_strategies:
            raise ValueError(f"Conflict resolution strategy must be one of: {valid_strategies}")
        return v
    
    @validator("max_workers")
    def validate_max_workers(cls, v, values):
        """Ensure max workers is greater than min required"""
        min_workers = values.get("min_workers_required", 1)
        if v < min_workers:
            raise ValueError("Max workers must be greater than or equal to min workers required")
        return v
    
    @validator("slot_duration_minutes")
    def validate_slot_duration(cls, v, values):
        """Ensure slot duration is within valid range"""
        min_duration = values.get("min_slot_duration_minutes", 15)
        max_duration = values.get("max_slot_duration_minutes", 480)
        if not min_duration <= v <= max_duration:
            raise ValueError(f"Slot duration must be between {min_duration} and {max_duration} minutes")
        return v
    
    @validator("skill_levels")
    def validate_skill_levels(cls, v):
        """Ensure at least basic skill levels are present"""
        if not v or len(v) == 0:
            raise ValueError("At least one skill level must be defined")
        return v
    
    def is_valid_skill_level(self, skill_level: str) -> bool:
        """Check if skill level is valid"""
        return skill_level in self.skill_levels
    
    def get_skill_level_index(self, skill_level: str) -> int:
        """Get numeric index for skill level (for comparison)"""
        try:
            return self.skill_levels.index(skill_level)
        except ValueError:
            return -1
    
    def can_worker_handle_skill_level(self, worker_skill: str, required_skill: str) -> bool:
        """Check if worker can handle required skill level"""
        if not self.require_skill_matching:
            return True
        
        worker_index = self.get_skill_level_index(worker_skill)
        required_index = self.get_skill_level_index(required_skill)
        
        if worker_index == -1 or required_index == -1:
            return False
        
        # Worker can handle their level or lower
        # If skill upgrades allowed, they can handle one level higher
        max_allowed = worker_index + (1 if self.allow_skill_upgrades else 0)
        return required_index <= max_allowed
    
    def get_total_shift_minutes(self) -> int:
        """Get total shift duration including breaks"""
        break_time = self.breaks_per_shift * self.break_duration_minutes
        return (self.default_shift_hours * 60) + break_time
    
    def get_working_minutes_per_shift(self) -> int:
        """Get actual working minutes per shift (excluding breaks)"""
        return self.default_shift_hours * 60
    
    def get_cache_key_for_worker_schedule(self, worker_id: str, date: str) -> str:
        """Get cache key for worker's schedule on specific date"""
        return f"{self.cache_key_prefix}:worker:{worker_id}:schedule:{date}"
    
    def get_cache_key_for_time_slot(self, date: str, time_slot: str) -> str:
        """Get cache key for time slot availability"""
        return f"{self.cache_key_prefix}:slot:{date}:{time_slot}"
    
    def get_cache_key_for_worker_availability(self, worker_id: str) -> str:
        """Get cache key for worker availability"""
        return f"{self.cache_key_prefix}:worker:{worker_id}:availability"


# Singleton instance
_scheduling_config: Optional[SchedulingConfig] = None


def get_scheduling_config() -> SchedulingConfig:
    """Get scheduling configuration singleton"""
    global _scheduling_config
    if _scheduling_config is None:
        _scheduling_config = SchedulingConfig()
    return _scheduling_config