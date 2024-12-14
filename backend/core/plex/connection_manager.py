from core.base.connection_manager import PlexConnectionManager
from core.base.database.models.connection import ConnectionRead
from core.plex.api_manager import PlexManager


class PlexConnectionManager(PlexConnectionManager):
    """Connection manager for working with the Plex application."""

    connection_id: int

    def __init__(self, connection: ConnectionRead):
        """Initialize the PlexConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        plex_manager = PlexManager(connection.url, connection.api_key)
        self.connection_id = connection.id
        super().__init__(
            connection,
            plex_manager,
        )
