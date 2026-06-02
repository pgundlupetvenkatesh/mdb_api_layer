"""
Pydantic models for API response validation.

Replaces JSON schema files with type-safe Python models.
Each model corresponds to a former .json schema in tests/schemas/.

.. module:: tests.schemas.models
   :synopsis: Pydantic response models for TMDB API validation.
   :no-index:
"""

from typing import Optional
from pydantic import BaseModel, Field, StrictBool, StrictInt, StrictStr

class GenericResponse(BaseModel):
    """
    Schema for generic error/status responses.

    Used to validate error responses across all endpoints when the API
    returns a status message instead of resource data (e.g., 404, 401).

    Replaces: ``generic_schema.json``

    Example response::
        {"status_message": "Resource not found.", "success": false, "status_code": 34}
    """
    status_message: str
    success: bool
    status_code: int

class RatingResponse(BaseModel):
    """
    Schema for add/delete movie rating responses.

    Validates the response structure when a rating is submitted or removed.
    Uses ``extra = "forbid"`` to reject any unexpected fields, matching the
    strict ``additionalProperties: false`` from the original JSON schema.

    Replaces: ``add_delete_rating_schema.json``

    Example response::
        {"success": true, "status_code": 1, "status_message": "Success."}
    """
    model_config = {"extra": "forbid"}  # equivalent to additionalProperties: false

    success: bool
    status_code: int
    status_message: str

# Nested model for production companies
class ProductionCompany(BaseModel):
    """
    Nested model for a production company within movie details.

    :param id: Unique identifier for the production company.
    :param logo_path: Path to the company logo image, or None if unavailable.
    :param name: Name of the production company.
    :param origin_country: ISO 3166-1 country code of the company's origin.
    """
    id: StrictInt = Field(ge=0)
    logo_path: Optional[str] = Field(default=None, pattern=r".*\.(png|jpg)$")
    name: StrictStr = Field(min_length=1)
    origin_country: Optional[str] = None

# Nested model for genres
class Genre(BaseModel):
    """
    Nested model for a movie genre.

    :param id: Unique identifier for the genre.
    :param name: Display name of the genre (e.g., "Action", "Comedy").
    """
    id: StrictInt = Field(ge=0)
    name: StrictStr = Field(min_length=1)

class MovieDetails(BaseModel):
    """
    Schema for movie details response from ``GET /3/movie/{movie_id}``.

    Validates the core fields returned by the TMDB movie details endpoint.
    Uses ``extra = "allow"`` to accept additional fields not explicitly
    defined here (e.g., overview, budget, revenue, runtime).

    Replaces: ``movie_schema.json``

    :param adult: Whether the movie is classified as adult content.
    :param id: Unique TMDB movie identifier.
    :param origin_country: List of ISO 3166-1 country codes.
    :param original_language: ISO 639-1 language code of the original language.
    :param original_title: Original title in the movie's native language.
    :param title: Localized title of the movie.
    :param release_date: Release date in ``YYYY-MM-DD`` format, or None.
    :param production_companies: List of companies that produced the movie.
    :param genres: List of genres the movie belongs to.
    """
    adult: StrictBool
    id: StrictInt = Field(ge=0)
    origin_country: list[str]                                  # may be empty
    original_language: StrictStr = Field(min_length=2, max_length=2)  # ISO 639-1
    original_title: StrictStr = Field(min_length=1)
    title: StrictStr = Field(min_length=1)
    release_date: Optional[str] = None
    production_companies: list[ProductionCompany]             # may be empty
    genres: list[Genre]                                       # may be empty

    model_config = {"extra": "allow"}  # allow fields not defined here (overview, etc.)

# Nested model for popular movie items
class PopularMovieItem(BaseModel):
    """
    Nested model for a single movie in the popular movies list.

    Represents one item in the ``results`` array returned by
    ``GET /3/movie/popular``.

    :param adult: Whether the movie is classified as adult content.
    :param backdrop_path: Path to the backdrop image, or None.
    :param genre_ids: List of genre IDs associated with the movie.
    :param id: Unique TMDB movie identifier.
    :param original_language: ISO 639-1 language code.
    :param original_title: Original title in the movie's native language.
    :param overview: Brief plot summary.
    :param popularity: TMDB popularity score.
    :param poster_path: Path to the poster image, or None.
    :param release_date: Release date in ``YYYY-MM-DD`` format.
    :param title: Localized title of the movie.
    :param video: Whether the movie has an associated video.
    :param vote_average: Average user rating (0.0–10.0).
    :param vote_count: Total number of user votes.
    """
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
    """
    Schema for popular movies list response from ``GET /3/movie/popular``.

    Validates the paginated response structure containing a list of
    popular movies.

    Replaces: ``popular_movies_schema.json``

    :param page: Current page number in the paginated results.
    :param results: List of popular movie items for this page.
    :param total_pages: Total number of available pages.
    :param total_results: Total number of popular movies across all pages.
    """
    page: int
    results: list[PopularMovieItem]
    total_pages: int
    total_results: int

class PersonDetails(BaseModel):
    """
    Schema for person details response from ``GET /3/person/{person_id}``.

    Validates the response structure for the TMDB person details endpoint.
    Uses ``extra = "allow"`` to accept additional fields not explicitly
    defined here (e.g., external_ids, combined_credits).

    Replaces: ``person_details_schema.json``

    :param adult: Whether the person is associated with adult content.
    :param also_known_as: Alternative names or aliases, or None.
    :param biography: Biographical text about the person.
    :param birthday: Date of birth in ``YYYY-MM-DD`` format.
    :param deathday: Date of death in ``YYYY-MM-DD`` format, or None if alive.
    :param gender: Gender identifier (0=not specified, 1=female, 2=male, 3=non-binary).
    :param homepage: Personal website URL, or None.
    :param id: Unique TMDB person identifier.
    :param imdb_id: IMDb identifier (e.g., ``nm0000093``).
    :param known_for_department: Primary department (e.g., "Acting", "Directing").
    :param name: Full name of the person.
    :param place_of_birth: City/country of birth, or None if unknown.
    :param popularity: TMDB popularity score.
    :param profile_path: Path to the profile image, or None.
    """
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