"""
Pydantic models for API response validation.

Replaces JSON schema files with type-safe Python models.
Each model corresponds to a former .json schema in tests/schemas/.

.. module:: tests.schemas.models
   :synopsis: Pydantic response models for TMDB API validation.
   :no-index:
"""

from typing import Optional
from pydantic import BaseModel, Field, StrictBool, StrictFloat, StrictInt, StrictStr, create_model

class GenericResponse(BaseModel):
    """
    Schema for generic error/status responses.

    Used to validate error responses across all endpoints when the API
    returns a status message instead of resource data (e.g., 404, 401).

    Replaces: ``generic_schema.json``

    Example response::
        {"status_message": "Resource not found.", "success": false, "status_code": 34}
    """
    model_config = {"extra": "forbid"}  # error body is exactly these three fields

    status_message: StrictStr = Field(min_length=1)
    success: StrictBool
    status_code: StrictInt = Field(ge=0)

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

    success: StrictBool
    status_code: StrictInt = Field(ge=0)
    status_message: StrictStr = Field(min_length=1)

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

# Nested model for movie list items
class MovieListItem(BaseModel):
    """
    Nested model for a single movie in a paginated movie list.

    Represents one item in the ``results`` array shared by TMDB's list-style
    endpoints (e.g. ``GET /3/movie/popular``, ``GET /3/search/movie``).

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
    adult: StrictBool
    backdrop_path: Optional[str] = Field(default=None, pattern=r".*\.(png|jpg)$")
    genre_ids: list[int]                                       # may be empty
    id: StrictInt = Field(ge=0)
    original_language: StrictStr = Field(min_length=2, max_length=2)  # ISO 639-1
    original_title: StrictStr = Field(min_length=1)
    overview: str                                              # may be empty
    popularity: StrictFloat = Field(ge=0)
    poster_path: Optional[str] = Field(default=None, pattern=r".*\.(png|jpg)$")
    release_date: str                                          # may be empty
    title: StrictStr = Field(min_length=1)
    video: StrictBool
    vote_average: StrictFloat = Field(ge=0, le=10)
    vote_count: StrictInt = Field(ge=0)

    model_config = {"extra": "allow"}

def paginated_movie_list(ge=1):
    """
    Build the base model for a paginated movie-list response.

    TMDB's list-style movie endpoints (popular, search, discover, trending)
    share one envelope: a ``page`` number, a ``results`` array of
    ``MovieListItem`` (required non-empty here — endpoints whose empty-result
    case is valid assert it directly in the test instead), and
    ``total_pages`` / ``total_results`` counts. Each endpoint subclasses the
    returned base so it keeps a distinct, individually-registered model name
    while sharing this field definition.

    :param ge: Lower bound applied to the integer pagination fields
               (``page``, ``total_pages``, ``total_results``). Defaults to 1;
               popular passes 0 for its looser contract.
    :return: A Pydantic base model class with the shared paginated fields.
    """
    return create_model(
        "PaginatedMovieList",
        page=(StrictInt, Field(ge=ge)),
        results=(list[MovieListItem], Field(min_length=1)),
        total_pages=(StrictInt, Field(ge=ge)),
        total_results=(StrictInt, Field(ge=ge)),
    )

class PopularMoviesResponse(paginated_movie_list(ge=0)):
    """
    Schema for popular movies list response from ``GET /3/movie/popular``.

    Validates the paginated response structure containing a list of
    popular movies. Result items use the shared ``MovieListItem`` model.

    Replaces: ``popular_movies_schema.json``
    """

class TrendingMoviesResponse(paginated_movie_list()):
    """
    Schema for trending movies list response from
    ``GET /3/trending/movie/{time_window}``.

    Validates the paginated response structure containing the movies trending
    over the requested time window (``day`` or ``week``). Result items use the
    shared ``MovieListItem`` model.
    """

class SearchMoviesResponse(paginated_movie_list()):
    """
    Schema for movie search response from ``GET /3/search/movie``.

    Validates the paginated response structure containing the movies that
    matched a search query. Result items use the shared ``MovieListItem``
    model. ``results`` requires at least one item — searches expected to
    return no matches are asserted directly in the test instead of via
    this schema.
    """

class DiscoverMoviesResponse(paginated_movie_list()):
    """
    Schema for movie discovery response from ``GET /3/discover/movie``.

    Validates the paginated response structure containing the movies that
    matched the discover filter/sort criteria. Result items use the shared
    ``MovieListItem`` model. ``results`` requires at least one item —
    filter combinations expected to match nothing are asserted directly
    in the test instead of via this schema.
    """

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
    adult: StrictBool
    also_known_as: list[str]                                   # always present, may be empty
    biography: StrictStr                                       # may be empty
    birthday: Optional[str] = None                             # null for some people
    deathday: Optional[str] = None
    gender: StrictInt = Field(ge=0, le=3)                      # 0=n/a, 1=F, 2=M, 3=non-binary
    homepage: Optional[str] = None
    id: StrictInt = Field(ge=0)
    imdb_id: Optional[str] = None                              # null for some people
    known_for_department: StrictStr = Field(min_length=1)
    name: StrictStr = Field(min_length=1)
    place_of_birth: Optional[str] = None
    popularity: StrictFloat = Field(ge=0)
    profile_path: Optional[str] = Field(default=None, pattern=r".*\.(png|jpg)$")

    model_config = {"extra": "allow"}

class NetworkDetails(BaseModel):
    """
    Schema for network details response from ``GET /3/network/{network_id}``.

    Validates the response structure for the TMDB network details endpoint.
    The body is small and fully enumerated, so ``extra = "forbid"`` keeps
    the contract strict.

    :param headquarters: Network headquarters location, may be empty.
    :param homepage: Network website URL, may be empty.
    :param id: Unique TMDB network identifier.
    :param logo_path: Path to the network logo image, or None.
    :param name: Name of the network.
    :param origin_country: ISO 3166-1 country code, may be empty (e.g., Netflix).
    """
    headquarters: StrictStr                                    # may be empty
    homepage: StrictStr                                        # may be empty
    id: StrictInt = Field(ge=1)
    logo_path: Optional[str] = Field(default=None, pattern=r".*\.(png|jpg)$")
    name: StrictStr = Field(min_length=1)
    origin_country: StrictStr                                  # empty for some networks

    model_config = {"extra": "forbid"}

# Nested model for a review's author
class AuthorDetails(BaseModel):
    """
    Nested model for the ``author_details`` block of a review.

    :param name: Author's display name, may be empty.
    :param username: Author's TMDB username.
    :param avatar_path: Path to the author's avatar, or None. Unlike other
                        ``*_path`` fields this is NOT constrained to an image
                        extension — TMDB may store a gravatar URL here
                        (e.g. ``/https://secure.gravatar.com/...``).
    :param rating: The author's rating for the media (0–10), or None.
    """
    name: StrictStr                                            # may be empty
    username: StrictStr = Field(min_length=1)
    avatar_path: Optional[str] = None                         # may be a gravatar URL, not just an image path
    rating: Optional[float] = Field(default=None, ge=0, le=10)

    model_config = {"extra": "forbid"}

class ReviewDetails(BaseModel):
    """
    Schema for review details response from ``GET /3/review/{review_id}``.

    Validates the response structure for the TMDB review details endpoint.
    The body is small and fully enumerated, so ``extra = "forbid"`` keeps
    the contract strict.

    :param id: Unique TMDB review identifier (24-character hex string).
    :param author: Author's display name.
    :param author_details: Nested author metadata (name, username, avatar, rating).
    :param content: The review text.
    :param created_at: Creation timestamp (ISO 8601).
    :param iso_639_1: ISO 639-1 language code of the review.
    :param media_id: TMDB id of the reviewed media.
    :param media_title: Title of the reviewed media.
    :param media_type: Media type of the reviewed item (e.g. ``movie``).
    :param updated_at: Last-updated timestamp (ISO 8601).
    :param url: Public URL of the review on themoviedb.org.
    """
    id: StrictStr = Field(min_length=1)
    author: StrictStr = Field(min_length=1)
    author_details: AuthorDetails
    content: StrictStr = Field(min_length=1)
    created_at: StrictStr = Field(min_length=1)
    iso_639_1: StrictStr = Field(min_length=1)
    media_id: StrictInt = Field(ge=0)
    media_title: StrictStr = Field(min_length=1)
    media_type: StrictStr = Field(min_length=1)
    updated_at: StrictStr = Field(min_length=1)
    url: StrictStr = Field(min_length=1)

    model_config = {"extra": "forbid"}