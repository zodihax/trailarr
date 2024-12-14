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

    async def get_all_movies(self):
        """Get all movies from the Plex API

        Returns:
            list[str, Any]: All movies with their Metadata from the Plex API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        section_ids = await self._get_all_section_ids()
        movies = []
        for section_id in section_ids:
            response = await self._request("GET", f"/library/sections/{section_id}/all?type=1")
            movies.extend(response.get('MediaContainer', {}).get('Metadata', []))
        if isinstance(movies, list):
            return movies
        raise InvalidResponseError("Invalid response from Plex API")

    async def get_all_series(self):
        """Get all series from the Plex API

        Returns:
            list[str, Any]: All series with their Metadata from the Plex API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        section_ids = await self._get_all_section_ids()
        series = []
        for section_id in section_ids:
            response = await self._request("GET", f"/library/sections/{section_id}/all?type=2")
            series.extend(response.get('MediaContainer', {}).get('Metadata', []))
        if isinstance(series, list):
            return series
        raise InvalidResponseError("Invalid response from Plex API")
    
    async def get_movie(self, title, year=None):
        """Get rating key of movie from the Plex API

        Returns:
            str: rating key

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        metadata = self.get_all_movies()
        for item in metadata:
            plex_title = item.get('title', '').lower()
            plex_year = item.get('year')

            if plex_title == title.lower():
                if year is None or str(plex_year) == str(year):
                    return item.get('ratingKey')
        return None
    
    async def get_series(self, title, year=None):
        """Get rating key of series from the Plex API

        Returns:
            str: rating key

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        metadata = self.get_all_series()
        for item in metadata:
            plex_title = item.get('title', '').lower()
            plex_year = item.get('year')

            if plex_title == title.lower():
                if year is None or str(plex_year) == str(year):
                    return item.get('ratingKey')
        return None

    async def get_all_media(self):
        """Get all media from the Plex API

        Returns:
            list[str, Any]: All series with their Metadata from the Plex API
        """
        movies = await self.get_all_movies()
        series = await self.get_all_series()
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