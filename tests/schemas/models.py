"""
Pydantic models for API response validation.

Replaces JSON schema files with type-safe Python models.
Each model corresponds to a former .json schema in tests/schemas/.
"""

from typing import Optional
from pydantic import BaseModel, Field


# Replaces: generic_schema.json
class GenericResponse(BaseModel):
    """Schema for error/status responses."""
    status_message: str
    success: bool
    status_code: int

# Replaces: add_delete_rating_schema.json (had additionalProperties: false)
class RatingResponse(BaseModel):
    """Schema for add/delete rating responses."""
    model_config = {"extra": "forbid"}  # equivalent to additionalProperties: false

    success: bool
    status_code: int
    status_message: str

# Nested model for production companies
class ProductionCompany(BaseModel):
    id: int
    logo_path: Optional[str] = None
    name: str
    origin_country: Optional[str] = None

# Nested model for genres
class Genre(BaseModel):
    id: int
    name: str

# Replaces: movie_schema.json
class MovieDetails(BaseModel):
    """Schema for movie details response."""
    adult: bool
    id: int
    origin_country: list[str]
    original_language: str
    original_title: str
    title: str
    release_date: Optional[str] = None
    production_companies: list[ProductionCompany]
    genres: Optional[list[Genre]] = None

    model_config = {"extra": "allow"}  # allow fields not defined here (overview, etc.)

# Nested model for popular movie items
class PopularMovieItem(BaseModel):
    adult: bool
    backdrop_path: Optional[str] = None
    genre_ids: list[int]
    id: int
    original_language: str
    original_title: str
    overview: str
    popularity: float
    poster_path: Optional[str] = None
    release_date: str
    title: str
    video: bool
    vote_average: float
    vote_count: int

    model_config = {"extra": "allow"}

class PopularMoviesResponse(BaseModel):
    """Schema for popular movies list response."""
    page: int
    results: list[PopularMovieItem]
    total_pages: int
    total_results: int

# Replaces: person_details_schema.json
class PersonDetails(BaseModel):
    """Schema for person details response."""
    adult: bool
    also_known_as: Optional[list[str]] = None
    biography: str
    birthday: str
    deathday: Optional[str] = None
    gender: int
    homepage: Optional[str] = None
    id: int
    imdb_id: str
    known_for_department: str
    name: str
    place_of_birth: Optional[str] = None
    popularity: float
    profile_path: Optional[str] = None

    model_config = {"extra": "allow"}