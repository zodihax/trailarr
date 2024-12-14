from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class ArrType(Enum):
    RADARR = "radarr"
    SONARR = "sonarr"

class MediaType(Enum):
    PLEX = "plex"

class MonitorType(Enum):
    # MONITOR_ALL = "all"
    MONITOR_MISSING = "missing"
    MONITOR_NEW = "new"
    MONITOR_NONE = "none"
    MONITOR_SYNC = "sync"


# Note: Creating a separate model for PathMappingCRU to avoid unwanted DB updates \
# on PathMapping table in database.
class PathMappingCRU(SQLModel):
    """Path Mapping model to use for Create, Read, and Update operations."""

    id: int | None = Field(default=None)
    connection_id: int | None = Field(default=None)
    path_from: str
    path_to: str


class PathMapping(SQLModel, table=True):
    """Path Mappings used to map remote paths to local paths. \n
    Can be set per Connection. \n
    Set `path_from` to Radarr/Sonarr root folder. \n
    Set `path_to` to local folder path that Trailarr can see. \n
    """

    id: int | None = Field(default=None, primary_key=True)
    connection_id: int | None = Field(default=None, foreign_key="connection.id")
    path_from: str
    path_to: str


class ConnectionBase(SQLModel):
    """Base class for the Connection model. \n
    Note: \n
        🚨**DO NOT USE THIS CLASS DIRECTLY.**🚨 \n
    Use ConnectionCreate, ConnectionRead, or ConnectionUpdate instead.
    """

    name: str
    arr_type: ArrType
    media_type: MediaType
    url: str
    api_key: str
    plex_token: str
    monitor: MonitorType
    # path_mappings: list[PathMappingCreate] = []


class Connection(ConnectionBase, table=True):
    """Connection model for the database. This is the main model for the application. \n
    Note: \n
        🚨**DO NOT USE THIS CLASS DIRECTLY.**🚨 \n
    Use ConnectionCreate, ConnectionRead, or ConnectionUpdate instead.
    """

    id: int | None = Field(default=None, primary_key=True)
    added_at: datetime = Field(default_factory=get_current_time)
    path_mappings: list[PathMapping] = Relationship()


class ConnectionCreate(ConnectionBase):
    """Connection model for creating a new connection. This is used in the API while creating."""

    path_mappings: list[PathMappingCRU]


class ConnectionRead(ConnectionBase):
    """Connection model for reading a connection. This is used in the API to return data."""

    id: int
    added_at: datetime
    path_mappings: list[PathMappingCRU]


class ConnectionUpdate(ConnectionBase):
    """Connection model for updating a connection. This is used in the API while updating."""

    name: str | None = None
    arr_type: ArrType | None = None
    media_type: MediaType | None = None
    url: str | None = None
    api_key: str | None = None
    plex_token: str | None = None
    monitor: MonitorType | None = None
    path_mappings: list[PathMappingCRU]
