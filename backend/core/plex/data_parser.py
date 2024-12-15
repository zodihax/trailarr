from typing import Any

from pydantic import BaseModel, Field

from core.base.database.models.media import MediaUpdate


class PlexDataParser(BaseModel):
    """Class to parse the data from Plex."""

    connection_id: int = Field(default=0)
    title: str = Field()
    year: int = Field()
    plex_rating_key: int = Field(validation_alias="ratingKey")
    plex_trailer_exists: bool | None = Field(default=False)
    
def parse_media(connection_id: int, media_data: dict[str, Any]) -> MediaUpdate:
    """Parse the media data from Plex to a MovieCreate object.\n
    Args:
        connection_id (int): The connection id.
        media_data (dict[str, Any]): The media data from Plex.\n
    Returns:
        MovieCreate: The movie data as a MovieCreate object."""
    media_parsed = PlexDataParser(**media_data)
    media_parsed.connection_id = connection_id

    return MediaUpdate.model_validate(media_parsed.model_dump())
