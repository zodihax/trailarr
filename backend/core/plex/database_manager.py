# from core.base.database.manager.base import DatabaseManager
# from core.radarr.models import Movie, MovieCreate, MovieRead, MovieUpdate


# class MovieDatabaseManager(DatabaseManager[Movie, MovieCreate, MovieRead, MovieUpdate]):
#     """CRUD operations for movie database table."""

#     def __init__(self):
#         super().__init__(db_model=Movie, read_model=MovieRead)

async def update_media_entries(self):
    # Fetch all entries from the database
    entries = await self.get_all_entries()
    
    for entry in entries:
        if entry.is_movie:
            # Search for the movie and retrieve its rating key
            rating_key = await self.search_movie_by_title_and_year(entry.title, entry.year)
        else:
            # Search for the series and retrieve its rating key
            rating_key = await self.search_series_by_title_and_year(entry.title, entry.year)
        
        if rating_key:
            # Perform the update with MediaUpdate
            update_data = MediaUpdate(
                title=entry.title,
                year=entry.year,
                is_movie=entry.is_movie,
                plex_rating_key=rating_key,
                updated_at=datetime.utcnow()  # Set the updated timestamp
            )
            await self.update_media_entry(entry.id, update_data)