"""
Amadeus Hotel API client for fetching hotel data.
Handles OAuth2 authentication and hotel search queries.
"""

import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)


class AmadeusClient:
    """Client for interacting with Amadeus Hotel Search API."""

    def __init__(self, client_id: str, client_secret: str, base_url: str = "https://api.amadeus.com"):
        """
        Initialize Amadeus API client.

        Args:
            client_id: Amadeus API Client ID
            client_secret: Amadeus API Client Secret
            base_url: Base URL for Amadeus API
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.access_token = None
        self.token_expiry = None
        self.session = requests.Session()

    def _get_access_token(self) -> str:
        """
        Obtain OAuth2 access token from Amadeus API.
        Tokens are cached until expiry.

        Returns:
            Access token string

        Raises:
            requests.exceptions.RequestException: If token request fails
        """
        # Return cached token if still valid
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        try:
            auth_url = f"{self.base_url}/v1/security/oauth2/token"
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            response = self.session.post(auth_url, data=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            self.access_token = data.get("access_token")
            expires_in = data.get("expires_in", 1800)  # Default 30 minutes
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 60s early

            logger.info("Amadeus access token obtained successfully")
            return self.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to obtain Amadeus access token: {e}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers with authorization.

        Returns:
            Dictionary of HTTP headers
        """
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def search_hotels_by_city(self, city: str, check_in: Optional[str] = None, check_out: Optional[str] = None) -> List[Dict]:
        """
        Search for hotels in a city.

        Args:
            city: City name to search for
            check_in: Check-in date (YYYY-MM-DD). Defaults to tomorrow.
            check_out: Check-out date (YYYY-MM-DD). Defaults to check_in + 1 day.

        Returns:
            List of hotel dictionaries with details

        Raises:
            ValueError: If city is empty
            requests.exceptions.RequestException: If API request fails
        """
        if not city or not city.strip():
            raise ValueError("City name cannot be empty")

        # Set default dates
        if check_in is None:
            check_in = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if check_out is None:
            check_out = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        try:
            search_url = f"{self.base_url}/v2/reference-data/locations/get"
            params = {
                "subType": "CITY",
                "keyword": city,
            }

            headers = self._get_headers()
            response = self.session.get(search_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            locations = response.json().get("data", [])
            if not locations:
                logger.warning(f"No locations found for city: {city}")
                return []

            # Get the first matching city
            city_id = locations[0].get("id")
            if not city_id:
                logger.warning(f"No city ID found for: {city}")
                return []

            # Now search for hotels in this city
            hotel_search_url = f"{self.base_url}/v3/reference-data/locations/hotel"
            hotel_params = {
                "cityCode": city_id,
            }

            hotel_response = self.session.get(hotel_search_url, params=hotel_params, headers=headers, timeout=10)
            hotel_response.raise_for_status()

            hotels = hotel_response.json().get("data", [])
            logger.info(f"Found {len(hotels)} hotels in {city}")

            return hotels

        except requests.exceptions.RequestException as e:
            logger.error(f"Hotel search failed for city '{city}': {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing hotel search response: {e}")
            return []

    def get_hotel_offers(self, hotel_id: str, adults: int = 1, check_in: Optional[str] = None, check_out: Optional[str] = None) -> List[Dict]:
        """
        Get hotel offers (pricing and availability).

        Args:
            hotel_id: Amadeus hotel ID
            adults: Number of adults
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)

        Returns:
            List of hotel offer dictionaries with pricing details
        """
        if check_in is None:
            check_in = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if check_out is None:
            check_out = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        try:
            offers_url = f"{self.base_url}/v3/shopping/hotel-offers"
            params = {
                "hotelIds": hotel_id,
                "adults": adults,
                "checkInDate": check_in,
                "checkOutDate": check_out,
            }

            headers = self._get_headers()
            response = self.session.get(offers_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            offers = response.json().get("data", [])
            logger.info(f"Found {len(offers)} offers for hotel {hotel_id}")

            return offers

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get hotel offers for '{hotel_id}': {e}")
            return []
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing hotel offers response: {e}")
            return []
