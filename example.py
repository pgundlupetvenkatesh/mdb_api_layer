"""
Example usage of the OMDB API client.

This script demonstrates how to use the OMDB API client to:
1. Search for movies
2. Get movie details by ID
3. Get movie details by title

Before running this script, make sure to:
1. Install dependencies: pip install -r requirements.txt
2. Create a .env file with your OMDB_API_KEY
"""

from src.api_client import OMDBClient
from src.config import Config
import json


def print_json(data):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2))


def main():
    """Main function demonstrating API client usage."""
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return
    
    # Initialize the client
    client = OMDBClient()
    
    print("=" * 80)
    print("OMDB API Client Example")
    print("=" * 80)
    
    # Example 1: Search for movies
    print("\n1. Searching for movies with term 'Batman'...")
    print("-" * 80)
    response = client.search_movies('Batman', page=1)
    if response.status_code == 200:
        data = response.json()
        if data.get('Response') == 'True':
            print(f"Found {data['totalResults']} results")
            print(f"\nFirst {len(data['Search'])} results:")
            for movie in data['Search'][:3]:
                print(f"  - {movie['Title']} ({movie['Year']}) - {movie['imdbID']}")
        else:
            print(f"Error: {data.get('Error')}")
    
    # Example 2: Get movie by IMDB ID
    print("\n2. Getting movie details by IMDB ID (tt0111161 - The Shawshank Redemption)...")
    print("-" * 80)
    response = client.get_by_id('tt0111161')
    if response.status_code == 200:
        data = response.json()
        if data.get('Response') == 'True':
            print(f"Title: {data['Title']}")
            print(f"Year: {data['Year']}")
            print(f"Director: {data['Director']}")
            print(f"Rating: {data['imdbRating']}/10")
            print(f"Plot: {data['Plot']}")
        else:
            print(f"Error: {data.get('Error')}")
    
    # Example 3: Get movie by title with year
    print("\n3. Getting movie details by title 'The Matrix' (1999)...")
    print("-" * 80)
    response = client.get_by_title('The Matrix', year='1999')
    if response.status_code == 200:
        data = response.json()
        if data.get('Response') == 'True':
            print(f"Title: {data['Title']}")
            print(f"Year: {data['Year']}")
            print(f"Director: {data['Director']}")
            print(f"Actors: {data['Actors']}")
            print(f"Rating: {data['imdbRating']}/10")
        else:
            print(f"Error: {data.get('Error')}")
    
    # Example 4: Search with filters
    print("\n4. Searching for movies with filters (Batman, year=2008, type=movie)...")
    print("-" * 80)
    response = client.search_movies('Batman', year='2008', content_type='movie')
    if response.status_code == 200:
        data = response.json()
        if data.get('Response') == 'True':
            print(f"Found {data['totalResults']} results")
            for movie in data['Search']:
                print(f"  - {movie['Title']} ({movie['Year']}) - Type: {movie['Type']}")
        else:
            print(f"Error: {data.get('Error')}")
    
    print("\n" + "=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == '__main__':
    main()
