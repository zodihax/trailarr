from typing import Any
from exceptions import InvalidResponseError
from core.base.plex_manager.base import AsyncBasePlexManager


class PlexManager(AsyncBasePlexManager):
    def __init__(self, url: str, token: str):
        """
        Constructor for connection to Plex API

        Args:
            url (str): Host URL to Plex API
            token (str): Token for Plex API

        Returns:
            None
        """
        super().__init__(url, token)

    async def get_system_status(self) -> str:
        """Get the system status of the Plex API

        Args:
            None

        Returns:
            str: The status of the Plex API with version if successful.

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If API response is invalid
        """
        return await self._get_system_status()
    
    async def _get_all_section_ids(self):
        response = await self._request("GET", "/library/sections")
        sections = response.get('MediaContainer', {}).get('Directory', [])
        section_ids = [section['key'] for section in sections]
        return section_ids

    async def get_media(self, rating_key: int) -> dict[str, Any]:
        """Get media metadata from the Plex API with the rating key

        Args:
            rating_key (int): The rating key of the media to get

        Returns:
            dict[str, Any]: media from the Plex API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        media = await self._request("GET", f"/library/metadata/{rating_key}")
        if isinstance(media, dict):
            return media
        raise InvalidResponseError("Invalid response from Plex API")

    async def _get_all_media_by_type(self, media_type: int) -> list[dict[str, Any]]:
        """Get all media of a specific type from the Plex API.

        Args:
            media_type (int): The type of media to fetch (1 for movies, 2 for series, etc.).

        Returns:
            list[dict[str, Any]]: All media of the specified type with their Metadata from the Plex API.

        Raises:
            ConnectionError: If the connection is refused / response is not 200.
            ConnectionTimeoutError: If the connection times out.
            InvalidResponseError: If the API response is invalid.
        """
        section_ids = await self._get_all_section_ids()
        media = []
        for section_id in section_ids:
            response = await self._request("GET", f"/library/sections/{section_id}/all?type={media_type}")
            metadata = response.get('MediaContainer', {}).get('Metadata', [])
            if isinstance(media, list):
                media.extend(metadata)
            else:
                raise InvalidResponseError("Invalid response format for Metadata in Plex API")
        return media

    async def get_all_media(self) -> list[dict[str, Any]]:
        """Get all media (movies and series) from the Plex API."""
        movies = await self._get_all_media_by_type(1)
        series = await self._get_all_media_by_type(2)
        return movies + series
        
    async def has_trailers(self, rating_key):
        """Checks if media has trailers

        Args:
            rating_key (int): The rating key of the media to get

        Returns:
            bool: does the media have trailer

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        response = await self._request("GET", f"/library/metadata/{rating_key}/extras")
        extras = response.get('MediaContainer', {}).get('Metadata', [])
        trailers = [extra for extra in extras if extra.get('subtype') == 'trailer']
        return len(trailers) > 0