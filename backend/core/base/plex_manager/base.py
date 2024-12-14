from typing import Any
from exceptions import InvalidResponseError
from core.base.plex_manager.request_manager import AsyncRequestManager


class AsyncBasePlexManager(AsyncRequestManager):
    """Base class for async requests to Plex API"""

    def __init__(self, url: str, token: str, version: str = ""):
        """
        Constructor for connection to Plex API

        Args:
            url (str): Host URL to Plex API
            token (str): Plex Token for Plex API

        Returns:
            None
        """
        super().__init__(url, token)

    async def _get_system_status(self) -> str:
        """Get the system status of the Plex API
        Returns:
            str: The status of the Plex API if successful.

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If API response is invalid
        """
        status: str | dict[str, Any] | list[dict[str, Any]] = await self._request(
            "GET", "/identity"
        )
        if isinstance(status, str):
            raise InvalidResponseError(status)
        if not isinstance(status, dict):
            raise InvalidResponseError("Unknown Error")

        # Now status is a dict, check if the app_name and version is in the response
        machine_identifyer = status.get("machineIdentifier")
        version = status.get("version")
        if machine_identifyer and version:
            return f"Plex Connection Successful! Version: {version}, Machine Identifyer {version}"
        raise InvalidResponseError(
            f"Invalid Host ({self.host_url}) or Plex Token ({self.token}), "
            f"not a Plex instance."
        )

    async def ping(self) -> str | dict[str, str] | list[dict[str, Any]]:
        """Ping the Plex API

        Args:
            None

        Returns:
            str | dict[str, str] | list[dict[str, Any]]: The response from the Plex API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        return await self._request("GET", "/identity")
