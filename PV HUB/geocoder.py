import json
import logging
import time

import requests

from config import (
    NOMINATIM_URL,
    USER_AGENT,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    REQUEST_DELAY,
    GEOCODE_CACHE_FILE,
)

class Geocoder:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json"
        })

        self.cache = self.load_cache()

        self.last_request = 0

    # ========================================================
    # CACHE
    # ========================================================

    def load_cache(self):

        if not GEOCODE_CACHE_FILE.exists():

            return {}

        try:

            with open(
                GEOCODE_CACHE_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

                if isinstance(data, dict):

                    return data

        except Exception as error:

            logging.error(
                "Cache rusak: %s",
                error
            )

        return {}

    def save_cache(self):

        temp_file = (
            GEOCODE_CACHE_FILE.with_suffix(
                ".tmp"
            )
        )

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.cache,
                file,
                ensure_ascii=False,
                indent=2
            )

        temp_file.replace(
            GEOCODE_CACHE_FILE
        )

    # ========================================================
    # RATE LIMIT
    # ========================================================

    def wait(self):

        elapsed = (
            time.time()
            - self.last_request
        )

        if elapsed < REQUEST_DELAY:

            time.sleep(
                REQUEST_DELAY - elapsed
            )

    # ========================================================
    # SEARCH
    # ========================================================

    def search(self, query):

        query = str(
            query or ""
        ).strip()

        if not query:

            return None

        cache_key = query.lower()

        # ----------------------------------------------------
        # CACHE
        # ----------------------------------------------------

        if cache_key in self.cache:

            logging.info(
                "Cache hit: %s",
                query
            )

            return self.cache[
                cache_key
            ]

        params = {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 1,
            "countrycodes": "id"
        }

        for attempt in range(
            MAX_RETRIES
        ):

            try:

                self.wait()

                response = self.session.get(
                    NOMINATIM_URL,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )

                self.last_request = (
                    time.time()
                )

                if response.status_code == 429:

                    logging.warning(
                        "Rate limit Nominatim."
                    )

                    time.sleep(
                        5 * (attempt + 1)
                    )

                    continue

                response.raise_for_status()

                results = response.json()

                result = (
                    results[0]
                    if results
                    else None
                )

                self.cache[
                    cache_key
                ] = result

                self.save_cache()

                return result

            except requests.RequestException as error:

                logging.error(
                    "Request error: %s",
                    error
                )

                time.sleep(
                    2 * (attempt + 1)
                )

            except Exception as error:

                logging.error(
                    "Unexpected geocoder error: %s",
                    error
                )

                break

        self.cache[
            cache_key
        ] = None

        self.save_cache()

        return None

    # ========================================================
    # PARSE
    # ========================================================

    @staticmethod
    def parse_result(result):

        if not result:

            return {
                "latitude": "",
                "longitude": "",
                "display_name": "",
                "address": {},
                "type": "",
                "osm_type": "",
                "osm_id": "",
                "importance": 0
            }

        try:

            importance = float(
                result.get(
                    "importance",
                    0
                )
            )

        except Exception:

            importance = 0

        return {
            "latitude": result.get(
                "lat",
                ""
            ),

            "longitude": result.get(
                "lon",
                ""
            ),

            "display_name": result.get(
                "display_name",
                ""
            ),

            "address": result.get(
                "address",
                {}
            ),

            "type": result.get(
                "type",
                ""
            ),

            "osm_type": result.get(
                "osm_type",
                ""
            ),

            "osm_id": result.get(
                "osm_id",
                ""
            ),

            "importance": importance
        }