"""
Dependency injection for facilities feature.

Wires up use cases with repository implementations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from ..adapters.repositories import SQLAlchemyWashBayRepository, SQLAlchemyMobileTeamRepository
from ..ports.repositories import IWashBayRepository, IMobileTeamRepository
from ..use_cases import (
    CreateWashBayUseCase,
    ListWashBaysUseCase,
    UpdateWashBayUseCase,
    DeleteWashBayUseCase,
    CreateMobileTeamUseCase,
    ListMobileTeamsUseCase,
    UpdateMobileTeamUseCase,
    DeleteMobileTeamUseCase
)
from app.core.db import get_db_session


# Repository providers
async def get_wash_bay_repository(
    session: AsyncSession = Depends(get_db_session)
) -> IWashBayRepository:
    """Provide wash bay repository instance."""
    return SQLAlchemyWashBayRepository(session)


async def get_mobile_team_repository(
    session: AsyncSession = Depends(get_db_session)
) -> IMobileTeamRepository:
    """Provide mobile team repository instance."""
    return SQLAlchemyMobileTeamRepository(session)


# Wash Bay use case providers
async def get_create_wash_bay_use_case(
    repository: IWashBayRepository = Depends(get_wash_bay_repository)
) -> CreateWashBayUseCase:
    """Provide create wash bay use case."""
    return CreateWashBayUseCase(repository)


async def get_list_wash_bays_use_case(
    repository: IWashBayRepository = Depends(get_wash_bay_repository)
) -> ListWashBaysUseCase:
    """Provide list wash bays use case."""
    return ListWashBaysUseCase(repository)


async def get_update_wash_bay_use_case(
    repository: IWashBayRepository = Depends(get_wash_bay_repository)
) -> UpdateWashBayUseCase:
    """Provide update wash bay use case."""
    return UpdateWashBayUseCase(repository)


async def get_delete_wash_bay_use_case(
    repository: IWashBayRepository = Depends(get_wash_bay_repository)
) -> DeleteWashBayUseCase:
    """Provide delete wash bay use case."""
    return DeleteWashBayUseCase(repository)


# Mobile Team use case providers
async def get_create_mobile_team_use_case(
    repository: IMobileTeamRepository = Depends(get_mobile_team_repository)
) -> CreateMobileTeamUseCase:
    """Provide create mobile team use case."""
    return CreateMobileTeamUseCase(repository)


async def get_list_mobile_teams_use_case(
    repository: IMobileTeamRepository = Depends(get_mobile_team_repository)
) -> ListMobileTeamsUseCase:
    """Provide list mobile teams use case."""
    return ListMobileTeamsUseCase(repository)


async def get_update_mobile_team_use_case(
    repository: IMobileTeamRepository = Depends(get_mobile_team_repository)
) -> UpdateMobileTeamUseCase:
    """Provide update mobile team use case."""
    return UpdateMobileTeamUseCase(repository)


async def get_delete_mobile_team_use_case(
    repository: IMobileTeamRepository = Depends(get_mobile_team_repository)
) -> DeleteMobileTeamUseCase:
    """Provide delete mobile team use case."""
    return DeleteMobileTeamUseCase(repository)
