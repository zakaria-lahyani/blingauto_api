from typing import List, Dict, Any
from decimal import Decimal

from .exceptions import ValidationError, BusinessRuleViolationError
from .entities import Category, Service, CategoryStatus, ServiceStatus


class CategoryManagementPolicy:
    """Policy class for category management rules."""
    
    @staticmethod
    def validate_category_creation(category: Category) -> None:
        """Validate category creation according to business rules."""
        if not category.name or not category.name.strip():
            raise ValidationError("Category name is required")
        
        # Additional business logic validation
        if category.name.lower() in ['admin', 'system', 'internal']:
            raise ValidationError("Category name is reserved")
    
    @staticmethod
    def validate_category_name_uniqueness(
        name: str,
        category_id: str,
        existing_categories: List[Category]
    ) -> None:
        """Validate category name uniqueness (RG-SVC-001)."""
        normalized_name = name.strip().lower()
        
        for category in existing_categories:
            if (category.id != category_id and 
                category.name.lower() == normalized_name and
                category.status != CategoryStatus.INACTIVE):
                raise ValidationError(f"Category name '{name}' already exists")
    
    @staticmethod
    def validate_category_deletion(
        category: Category,
        active_services_count: int
    ) -> None:
        """Validate category deletion constraints (RG-SVC-002)."""
        if category.status == CategoryStatus.INACTIVE:
            raise BusinessRuleViolationError("Category is already inactive")
        
        if active_services_count > 0:
            raise BusinessRuleViolationError(
                f"Cannot deactivate category with {active_services_count} active services. "
                "Please deactivate or move all services first."
            )
    
    @staticmethod
    def suggest_category_ordering(categories: List[Category]) -> List[Category]:
        """Suggest optimal category ordering based on business logic."""
        # Sort by display order, then by name
        return sorted(categories, key=lambda c: (c.display_order, c.name.lower()))
    
    @staticmethod
    def calculate_category_statistics(
        category: Category,
        services: List[Service]
    ) -> Dict[str, Any]:
        """Calculate category statistics for business insights."""
        category_services = [s for s in services if s.category_id == category.id]
        active_services = [s for s in category_services if s.is_active]
        popular_services = [s for s in active_services if s.is_popular]
        
        if not category_services:
            return {
                "total_services": 0,
                "active_services": 0,
                "popular_services": 0,
                "average_price": Decimal('0.00'),
                "average_duration": 0,
                "price_range": {"min": Decimal('0.00'), "max": Decimal('0.00')},
            }
        
        prices = [s.price for s in active_services]
        durations = [s.duration_minutes for s in active_services]
        
        return {
            "total_services": len(category_services),
            "active_services": len(active_services),
            "popular_services": len(popular_services),
            "average_price": sum(prices) / len(prices) if prices else Decimal('0.00'),
            "average_duration": sum(durations) // len(durations) if durations else 0,
            "price_range": {
                "min": min(prices) if prices else Decimal('0.00'),
                "max": max(prices) if prices else Decimal('0.00'),
            },
        }


class ServiceManagementPolicy:
    """Policy class for service management rules."""
    
    @staticmethod
    def validate_service_creation(service: Service) -> None:
        """Validate service creation according to business rules."""
        if not service.category_id or not service.category_id.strip():
            raise ValidationError("Service must belong to a category")
        
        if not service.name or not service.name.strip():
            raise ValidationError("Service name is required")
    
    @staticmethod
    def validate_service_name_uniqueness_in_category(
        name: str,
        category_id: str,
        service_id: str,
        existing_services: List[Service]
    ) -> None:
        """Validate service name uniqueness within category (RG-SVC-003)."""
        normalized_name = name.strip().lower()
        
        for service in existing_services:
            if (service.id != service_id and 
                service.category_id == category_id and
                service.name.lower() == normalized_name and
                service.status != ServiceStatus.ARCHIVED):
                raise ValidationError(f"Service name '{name}' already exists in this category")
    
    @staticmethod
    def validate_pricing_rules(price: Decimal, service_type: str = "standard") -> None:
        """Validate pricing according to business rules (RG-SVC-004)."""
        if price <= 0:
            raise ValidationError("Service price must be positive")
        
        # Business rule: Maximum price limits based on service type
        max_prices = {
            "standard": Decimal('500.00'),
            "premium": Decimal('1000.00'),
            "luxury": Decimal('2000.00'),
        }
        
        max_price = max_prices.get(service_type, Decimal('500.00'))
        if price > max_price:
            raise ValidationError(f"Price cannot exceed ${max_price} for {service_type} services")
        
        # Validate price precision (max 2 decimal places)
        if price.as_tuple().exponent < -2:
            raise ValidationError("Price cannot have more than 2 decimal places")
    
    @staticmethod
    def validate_duration_rules(duration_minutes: int) -> None:
        """Validate duration according to business rules (RG-SVC-005)."""
        if duration_minutes <= 0:
            raise ValidationError("Service duration must be positive")
        
        # Business rule: Duration must be in 15-minute increments
        if duration_minutes % 15 != 0:
            raise ValidationError("Service duration must be in 15-minute increments")
        
        # Business rule: Minimum and maximum duration limits
        if duration_minutes < 15:
            raise ValidationError("Service duration must be at least 15 minutes")
        
        if duration_minutes > 480:  # 8 hours
            raise ValidationError("Service duration cannot exceed 8 hours (480 minutes)")
    
    @staticmethod
    def validate_popular_service_limits(
        service: Service,
        current_popular_services: List[Service],
        max_popular_per_category: int = 3
    ) -> None:
        """Validate popular service limits (RG-SVC-006)."""
        if not service.is_popular:
            return  # No validation needed for non-popular services
        
        category_popular_services = [
            s for s in current_popular_services 
            if s.category_id == service.category_id and s.id != service.id
        ]
        
        if len(category_popular_services) >= max_popular_per_category:
            raise BusinessRuleViolationError(
                f"Category already has {max_popular_per_category} popular services. "
                "Please remove popular status from another service first."
            )
    
    @staticmethod
    def suggest_service_pricing(
        service: Service,
        similar_services: List[Service]
    ) -> Dict[str, Decimal]:
        """Suggest pricing based on similar services."""
        if not similar_services:
            return {
                "suggested_price": service.price,
                "min_price": service.price * Decimal('0.8'),
                "max_price": service.price * Decimal('1.2'),
            }
        
        prices = [s.price for s in similar_services if s.is_active]
        if not prices:
            return {
                "suggested_price": service.price,
                "min_price": service.price,
                "max_price": service.price,
            }
        
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        return {
            "suggested_price": avg_price,
            "min_price": min_price,
            "max_price": max_price,
            "current_price": service.price,
            "price_position": "below_average" if service.price < avg_price else 
                           "above_average" if service.price > avg_price else "average",
        }
    
    @staticmethod
    def calculate_service_profitability(
        service: Service,
        booking_count: int,
        period_days: int,
        cost_per_service: Decimal = Decimal('0.00')
    ) -> Dict[str, Any]:
        """Calculate service profitability metrics."""
        if period_days <= 0:
            raise ValidationError("Period must be positive")
        
        total_revenue = service.price * booking_count
        total_cost = cost_per_service * booking_count
        profit = total_revenue - total_cost
        
        profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')
        daily_average = booking_count / period_days
        
        return {
            "booking_count": booking_count,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "profit": profit,
            "profit_margin_percent": profit_margin,
            "daily_average_bookings": daily_average,
            "revenue_per_day": total_revenue / period_days,
        }


class ServiceRecommendationPolicy:
    """Policy class for service recommendations and suggestions."""
    
    @staticmethod
    def recommend_complementary_services(
        selected_service: Service,
        available_services: List[Service]
    ) -> List[Service]:
        """Recommend complementary services based on business logic."""
        # Filter to active services from different categories
        complementary = []
        
        for service in available_services:
            if (service.is_active and 
                service.category_id != selected_service.category_id and
                service.id != selected_service.id):
                complementary.append(service)
        
        # Sort by popularity, then by price
        complementary.sort(key=lambda s: (not s.is_popular, s.price))
        
        return complementary[:5]  # Return top 5 recommendations
    
    @staticmethod
    def suggest_service_bundles(
        services: List[Service],
        max_bundle_duration: int = 180,  # 3 hours
        target_price_range: tuple = (Decimal('50.00'), Decimal('200.00'))
    ) -> List[Dict[str, Any]]:
        """Suggest service bundles based on business rules."""
        bundles = []
        active_services = [s for s in services if s.is_active]
        
        # Generate 2-service bundles
        for i, service1 in enumerate(active_services):
            for service2 in active_services[i+1:]:
                total_duration = service1.duration_minutes + service2.duration_minutes
                total_price = service1.price + service2.price
                
                if (total_duration <= max_bundle_duration and
                    target_price_range[0] <= total_price <= target_price_range[1]):
                    
                    # Calculate bundle discount (5-15%)
                    discount_percent = Decimal('0.10')  # 10% default
                    bundle_price = total_price * (Decimal('1.00') - discount_percent)
                    
                    bundles.append({
                        "services": [service1, service2],
                        "original_price": total_price,
                        "bundle_price": bundle_price,
                        "savings": total_price - bundle_price,
                        "total_duration": total_duration,
                        "discount_percent": discount_percent * 100,
                    })
        
        # Sort by savings (highest first)
        bundles.sort(key=lambda b: b["savings"], reverse=True)
        return bundles[:3]  # Return top 3 bundles
    
    @staticmethod
    def analyze_service_demand(
        service: Service,
        historical_bookings: List[Dict[str, Any]],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze service demand patterns."""
        if not historical_bookings:
            return {
                "demand_level": "unknown",
                "trend": "stable",
                "peak_days": [],
                "recommendations": [],
            }
        
        # Analyze booking patterns
        total_bookings = len(historical_bookings)
        daily_average = total_bookings / period_days
        
        # Determine demand level
        if daily_average >= 5:
            demand_level = "high"
        elif daily_average >= 2:
            demand_level = "medium"
        elif daily_average >= 0.5:
            demand_level = "low"
        else:
            demand_level = "very_low"
        
        recommendations = []
        
        if demand_level == "high":
            recommendations.append("Consider increasing price or adding capacity")
        elif demand_level == "low":
            recommendations.append("Consider promotional pricing or bundling")
        elif demand_level == "very_low":
            recommendations.append("Review service positioning or consider discontinuation")
        
        return {
            "demand_level": demand_level,
            "daily_average": daily_average,
            "total_bookings": total_bookings,
            "recommendations": recommendations,
        }