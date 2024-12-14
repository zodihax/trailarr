from abc import ABC
from functools import cache
from typing import Any, Callable, Protocol

from app_logger import ModuleLogger
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.helpers import MediaReadDC, MediaUpdateDC
from core.files_handler import FilesHandler
from core.base.database.models.connection import ConnectionRead, MonitorType
from core.base.database.models.media import MediaCreate, MonitorStatus

logger = ModuleLogger("ConnectionManager")


class ArrManagerProtocol(Protocol):
    """Abstract class for getting data from the Arr APIs."""

    async def get_system_status(self) -> str:
        """Get the system status from the Arr application. \n
        Returns:
            str: The system status from the Arr application."""
        raise NotImplementedError("Subclasses must implement this method")

    async def get_all_media(self) -> list[dict[str, Any]]:
        """Get all media from the Arr application. \n
        Returns:
            list[dict[str, Any]]: The media from the Arr application."""
        raise NotImplementedError("Subclasses must implement this method")
    

class PlexManagerProtocol(Protocol):
    """Abstract class for getting data from the Plex APIs."""

    async def get_system_status(self) -> str:
        """Get the system status from Plex. \n
        Returns:
            str: The system status from Plex."""
        raise NotImplementedError("Subclasses must implement this method")
    
    async def get_all_media(self) -> list[dict[str, Any]]:
        """Get all media from Plex. \n
        Returns:
            list[dict[str, Any]]: The media from Plex."""
        raise NotImplementedError("Subclasses must implement this method")


class BaseConnectionManager(ABC):
    """Connection manager for working with the Arr applications.
    Abstract class that provides the base functionality for working with the Arr applications.
    """

    arr_manager: ArrManagerProtocol
    connection_id: int
    inline_trailer: bool
    monitor: MonitorType
    parse_media: Callable[[int, dict[str, Any]], MediaCreate]

    def __init__(
        self,
        connection: ConnectionRead,
        arr_manager: ArrManagerProtocol,
        parse_media: Callable[[int, dict[str, Any]], MediaCreate],
        inline_trailer: bool,
    ):
        """Initialize the ArrConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        self.connection_id = connection.id
        self.path_mappings = connection.path_mappings
        self.monitor = connection.monitor
        self.arr_manager = arr_manager
        self.parse_media = parse_media
        self.inline_trailer = inline_trailer

    async def get_system_status(self):
        """Get the system status from the Arr application. \n
        Returns:
            str: The system status from the Arr application.
            None: If the system status could not be retrieved."""
        try:
            return await self.arr_manager.get_system_status()
        except Exception:
            return None

    async def get_media_data(self) -> list[dict[str, Any]]:
        """Get the data from the Arr application. \n
        Returns:
            - list[dict[str, Any]]: The data from the Arr application.
            - An empty list if the data could not be retrieved."""
        try:
            return await self.arr_manager.get_all_media()
        except Exception:
            logger.error("Failed to get media data from Arr application.")
            return []

    async def _parse_data(self) -> list[MediaCreate]:
        """Parse media received from the Arr API to objects that can be added to database.\n
        Returns:
            list[_MediaCreate]: list of parsed media objects."""
        media_data = await self.get_media_data()
        return [
            self.parse_media(self.connection_id, each_media_data)
            for each_media_data in media_data
        ]

    def _apply_path_mappings(self, media_list: list[MediaCreate]) -> list[MediaCreate]:
        """Update the paths of the media based on the path mappings.\n
        Args:
            media_list (list[MediaCreate]): The list of media objects.\n
        Returns:
            list[MediaCreate]: The updated list of media objects."""
        # If no path mappings exist, return the media list as is
        if len(self.path_mappings) == 0:
            return media_list
        # Loop through the media_list and apply the path mappings
        updated_media_list: list[MediaCreate] = []
        media_path_updated = False
        for media in media_list:
            if not media.folder_path:
                updated_media_list.append(media)
                continue
            for path_mapping in self.path_mappings:
                if media.folder_path.startswith(path_mapping.path_from):
                    media.folder_path = media.folder_path.replace(
                        path_mapping.path_from, path_mapping.path_to
                    )
                    media.folder_path = media.folder_path.replace("\\", "/")
                    updated_media_list.append(media)
                    media_path_updated = True
                    break
            if not media_path_updated:
                media.folder_path = media.folder_path.replace("\\", "/")
                updated_media_list.append(media)
        return updated_media_list

    async def _check_trailer(self, folder_path: str) -> bool:
        """Check if a trailer exists for the media in the folder path.\n
        Args:
            folder_path (str): The folder path to check for the trailer.\n
        Returns:
            bool: True if the trailer exists, False otherwise."""
        trailer_exists = await FilesHandler.check_trailer_exists(
            path=folder_path,
            check_inline_file=self.inline_trailer,
        )
        return trailer_exists

    @cache
    def _check_monitoring(
        self, is_new: bool, trailer_exists: bool, arr_monitored: bool
    ) -> bool:
        """Check if the media should be monitored based on the monitor type.\n
        Args:
            is_new (bool): Flag indicating media is newly created in database.
            trailer_exists (bool): Flag indicating if a trailer exists on disk.
            arr_monitored (bool): Flag indicating if media is monitored in Arr application.\n
        Returns:
            bool: True if the media should be monitored, False otherwise."""
        # If Trailer already exists, no need to monitor
        if trailer_exists:
            return False
        # Disable monitoring if monitor is set to none
        if self.monitor == MonitorType.MONITOR_NONE:
            return False
        # Monitor trailers if set to monitor missing
        if self.monitor == MonitorType.MONITOR_MISSING:
            return True
        # Monitor trailers if set to monitor new
        if self.monitor == MonitorType.MONITOR_NEW:
            return is_new
        # Sync monitor based on arr monitor status
        if self.monitor == MonitorType.MONITOR_SYNC:
            return arr_monitored
        return False

    @cache
    def _get_media_status(
        self, trailer_exists: bool, monitor: bool, current_status: MonitorStatus
    ) -> MonitorStatus:
        """Get the media status based on the trailer and monitoring status.\n
        Args:
            trailer_exists (bool): Flag indicating if a trailer exists on disk.
            monitor (bool): Flag indicating if the media should be monitored.
            current_status (MonitorStatus): The current media status.\n
        Returns:
            MonitorStatus: The new media status."""
        # If media is already downloading, return downloading status
        if current_status == MonitorStatus.DOWNLOADING:
            return MonitorStatus.DOWNLOADING
        # If trailer exists, return downloaded status
        if trailer_exists:
            return MonitorStatus.DOWNLOADED
        # If media is monitored, return monitored status
        if monitor:
            return MonitorStatus.MONITORED
        # Else, return missing status
        return MonitorStatus.MISSING

    def create_or_update_bulk(self, media_data: list[MediaCreate]) -> list[MediaReadDC]:
        """Create or update media in the database and return MediaRead objects.\n
        Args:
            media_data (list[MovieCreate]): The movie data to create or update.\n
        Returns:
            list[MediaReadDC]: A list of MediaRead objects."""
        movie_read_list = MediaDatabaseManager().create_or_update_bulk(media_data)
        return [
            MediaReadDC(
                id=movie_read.id,
                created=created,
                folder_path=movie_read.folder_path,
                arr_monitored=movie_read.arr_monitored,
                monitor=movie_read.monitor,
                status=movie_read.status,
            )
            for movie_read, created in movie_read_list
        ]

    def remove_deleted_media(self, media_ids: list[int]) -> None:
        """Remove the media from the database that are not present in the Arr application. \n
        Args:
            media_ids (list[int]): List of media ids to remove."""
        MediaDatabaseManager().delete_except(self.connection_id, media_ids)
        return

    def update_media_status_bulk(self, media_update_list: list[MediaUpdateDC]):
        """Update the media status in the database. \n
        Args:
            media_update_list (list[MediaUpdateDC]): List of media update data."""
        MediaDatabaseManager().update_media_status_bulk(media_update_list)
        return

    async def refresh(self):
        """Gets new data from Arr API and saves it to the database."""
        # Get the parsed data from the Arr API
        parsed_media = await self._parse_data()
        if len(parsed_media) == 0:
            logger.warning("No media found in the Arr application")
            return
        # Apply path mappings to the media folder paths
        parsed_media2 = self._apply_path_mappings(parsed_media)
        # Create or update the media in the database
        media_res = self.create_or_update_bulk(parsed_media2)
        # Delete any media that is not present in the Arr application
        media_ids = [media.id for media in media_res]
        self.remove_deleted_media(media_ids)
        # Check if media has trailer and should be monitored
        update_list: list[MediaUpdateDC] = []
        for media_read in media_res:
            if media_read.folder_path is None:
                trailer_exists = False
            else:
                trailer_exists = await self._check_trailer(media_read.folder_path)
            # Check if monitor is already enabled
            if media_read.monitor:
                monitor_media = True
            else:
                # Else, check if monitor needs to be enabled now
                monitor_media = self._check_monitoring(
                    media_read.created, trailer_exists, media_read.arr_monitored
                )
            # Set media status based on trailer and monitoring status
            status = self._get_media_status(
                trailer_exists, monitor_media, media_read.status
            )
            # Append to the update list
            update_list.append(
                MediaUpdateDC(
                    id=media_read.id,
                    monitor=monitor_media,
                    status=status,
                    trailer_exists=trailer_exists,
                )
            )
        # Update the database with trailer and monitoring status
        self.update_media_status_bulk(update_list)
        return

class PlexConnectionManager(ABC):
    """Connection manager for working with Plex.
    Abstract class that provides the base functionality for working with Plex.
    """

    plex_manager: PlexManagerProtocol
    connection_id: int
    parse_media: Callable[[int, dict[str, Any]], MediaCreate]

    def __init__(
        self,
        connection: ConnectionRead,
        plex_manager: PlexManagerProtocol,
        parse_media: Callable[[int, dict[str, Any]], MediaCreate],
    ):
        """Initialize the PlexConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        self.connection_id = connection.id
        self.plex_manager = plex_manager
        self.parse_media = parse_media

    async def get_system_status(self):
        """Get the system status from Plex. \n
        Returns:
            str: The system status from Plex.
            None: If the system status could not be retrieved."""
        try:
            return await self.plex_manager.get_system_status()
        except Exception:
            return None
        
    async def get_media_data(self) -> list[dict[str, Any]]:
        """Get the data from Plex. \n
        Returns:
            - list[dict[str, Any]]: The data from the Plex.
            - An empty list if the data could not be retrieved."""
        try:
            return await self.plex_manager.get_all_media()
        except Exception:
            logger.error("Failed to get media data from Plex.")
            return []

    async def _parse_data(self) -> list[MediaCreate]:
        """Parse media received from the Plex API to objects that can be added to database.\n
        Returns:
            list[_MediaCreate]: list of parsed media objects."""
        media_data = await self.get_media_data()
        return [
            self.parse_media(self.connection_id, each_media_data)
            for each_media_data in media_data
        ]
    
    def get_media(self, title: str, year: int) -> int | None:
        """Queries the database to get a match of media by title and year.
        
        Args:
            title (str): Title of the media.
            year (int): Release year of the media.
            
        Returns:
            int: The ID of the matching media if found.
            None: If no matching media is found.
        """
        titles = MediaDatabaseManager().search(title)        
        if not titles:
            return None        
        for media in titles:
            if media.title.lower() == title.lower() and media.year == year:
                return MediaCreate(
                    id=media.id
                )    
        return None

    def update_bulk(self, media_data: list[MediaCreate]) -> list[MediaReadDC]:
        """Update existing media in the database based on Plex data.
        
        Args:
            media_data (list[MediaCreate]): The media data to update.

        Returns:
            list[MediaReadDC]: A list of updated MediaRead objects for existing entries.
        """
        # Filter the provided media_data to update only existing entries
        existing_media = [
            media for media in media_data 
            if self.get_media(media.title, media.year) is not None
        ]

        existing_media2 = [
            MediaCreate(
                id=self.get_media(media.title, media.year),
                plex_ratingkey=media.plex_ratingkey
            )
            for media in existing_media
        ]        
        
        # Update existing media in bulk
        updated_media = MediaDatabaseManager().create_or_update_bulk(existing_media2)
        
        # Convert database results to MediaReadDC objects
        return [
            MediaReadDC(
                id=media_read.id,
                created=created,
                plex_ratingkey=media_read.plex_ratingkey
            )
            for media_read, created in updated_media
        ]

    
    def update_media_status_bulk(self, media_update_list: list[MediaUpdateDC]) -> None:
        """Update the media attributes in the database.
        
        Args:
            media_update_list (list[MediaUpdateDC]): List of media update data.
        """
        MediaDatabaseManager().update_media_status_bulk(media_update_list)


    async def refresh(self):
        """Gets new data from Plex API and updates the plex_trailer_exists field for existing entries."""
        # Fetch and parse media data from Plex
        parsed_media = await self._parse_data()
        if len(parsed_media) == 0:
            logger.warning("No media found in Plex")
            return

        media_res = self.update_bulk(parsed_media)

        # Prepare media update list for `plex_trailer_exists`
        update_list: list[MediaUpdateDC] = []
        for media_read in media_res:
            plex_trailer_exists = await self.plex_manager.has_trailers(media_read.rating_key)
            # Append to the update list
            update_list.append(
                MediaUpdateDC(
                    id=media_read.id,
                    plex_trailer_exists=plex_trailer_exists,
                    plex_ratingkey=media_read.plex_ratingkey
                )
            )
        # Update the database with trailer and monitoring status
        self.update_media_status_bulk(update_list)
        return

