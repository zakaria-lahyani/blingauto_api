"""Facilities use cases."""

from .create_wash_bay import CreateWashBayUseCase, CreateWashBayRequest, CreateWashBayResponse
from .list_wash_bays import ListWashBaysUseCase, ListWashBaysRequest, ListWashBaysResponse
from .update_wash_bay import UpdateWashBayUseCase, UpdateWashBayRequest, UpdateWashBayResponse
from .delete_wash_bay import DeleteWashBayUseCase, DeleteWashBayRequest, DeleteWashBayResponse

from .create_mobile_team import CreateMobileTeamUseCase, CreateMobileTeamRequest, CreateMobileTeamResponse
from .list_mobile_teams import ListMobileTeamsUseCase, ListMobileTeamsRequest, ListMobileTeamsResponse
from .update_mobile_team import UpdateMobileTeamUseCase, UpdateMobileTeamRequest, UpdateMobileTeamResponse
from .delete_mobile_team import DeleteMobileTeamUseCase, DeleteMobileTeamRequest, DeleteMobileTeamResponse

__all__ = [
    # Wash Bay use cases
    "CreateWashBayUseCase",
    "CreateWashBayRequest",
    "CreateWashBayResponse",
    "ListWashBaysUseCase",
    "ListWashBaysRequest",
    "ListWashBaysResponse",
    "UpdateWashBayUseCase",
    "UpdateWashBayRequest",
    "UpdateWashBayResponse",
    "DeleteWashBayUseCase",
    "DeleteWashBayRequest",
    "DeleteWashBayResponse",

    # Mobile Team use cases
    "CreateMobileTeamUseCase",
    "CreateMobileTeamRequest",
    "CreateMobileTeamResponse",
    "ListMobileTeamsUseCase",
    "ListMobileTeamsRequest",
    "ListMobileTeamsResponse",
    "UpdateMobileTeamUseCase",
    "UpdateMobileTeamRequest",
    "UpdateMobileTeamResponse",
    "DeleteMobileTeamUseCase",
    "DeleteMobileTeamRequest",
    "DeleteMobileTeamResponse",
]
