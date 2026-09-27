import json
import logging
import time

import requests

from config import (
    WILAYAH_API,
    WILAYAH_FILE,
    REQUEST_TIMEOUT,
)


HEADERS = {
    "User-Agent": "PV HUB/1.0"
}


class WilayahDatabase:

    def __init__(self):

        self.data = {
            "provinces": [],
            "regencies": [],
            "districts": [],
            "villages": []
        }

        self.province_by_code = {}
        self.regency_by_code = {}
        self.district_by_code = {}
        self.village_by_code = {}

    # ========================================================
    # HTTP
    # ========================================================

    def request_json(self, url):

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # LOAD
    # ========================================================

    def load(self):

        if WILAYAH_FILE.exists():

            logging.info(
                "Memuat database wilayah lokal."
            )

            try:

                with open(
                    WILAYAH_FILE,
                    "r",
                    encoding="utf-8"
                ) as file:

                    self.data = json.load(file)

            except Exception as error:

                logging.error(
                    "Database wilayah rusak: %s",
                    error
                )

                self.download()

        else:

            self.download()

        self.build_indexes()

    # ========================================================
    # DOWNLOAD
    # ========================================================

    def download(self):

        print()
        print("=" * 60)
        print("DOWNLOAD DATABASE WILAYAH INDONESIA")
        print("=" * 60)

        logging.info(
            "Memulai download database wilayah."
        )

        provinces = self.request_json(
            f"{WILAYAH_API}/provinces.json"
        )["data"]

        regencies = []
        districts = []
        villages = []

        for province in provinces:

            province_code = province["code"]

            print(
                f"Provinsi: {province['name']}"
            )

            try:

                result = self.request_json(
                    f"{WILAYAH_API}/regencies/"
                    f"{province_code}.json"
                )

                province_regencies = result["data"]

                regencies.extend(
                    province_regencies
                )

            except Exception as error:

                logging.error(
                    "Gagal mengambil regency %s: %s",
                    province_code,
                    error
                )

                continue

            for regency in province_regencies:

                regency_code = regency["code"]

                try:

                    result = self.request_json(
                        f"{WILAYAH_API}/districts/"
                        f"{regency_code}.json"
                    )

                    regency_districts = result["data"]

                    districts.extend(
                        regency_districts
                    )

                except Exception as error:

                    logging.error(
                        "Gagal district %s: %s",
                        regency_code,
                        error
                    )

                    continue

                for district in regency_districts:

                    district_code = district["code"]

                    try:

                        result = self.request_json(
                            f"{WILAYAH_API}/villages/"
                            f"{district_code}.json"
                        )

                        district_villages = result["data"]

                        villages.extend(
                            district_villages
                        )

                    except Exception as error:

                        logging.error(
                            "Gagal village %s: %s",
                            district_code,
                            error
                        )

                    time.sleep(0.02)

        self.data = {
            "provinces": provinces,
            "regencies": regencies,
            "districts": districts,
            "villages": villages
        }

        with open(
            WILAYAH_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.data,
                file,
                ensure_ascii=False,
                indent=2
            )

        logging.info(
            "Database wilayah selesai."
        )

        print()
        print("Database wilayah selesai disimpan.")

    # ========================================================
    # INDEX
    # ========================================================

    def build_indexes(self):

        self.province_by_code = {
            item["code"]: item
            for item in self.data["provinces"]
        }

        self.regency_by_code = {
            item["code"]: item
            for item in self.data["regencies"]
        }

        self.district_by_code = {
            item["code"]: item
            for item in self.data["districts"]
        }

        self.village_by_code = {
            item["code"]: item
            for item in self.data["villages"]
        }

    # ========================================================
    # FIND
    # ========================================================

    def find_exact(self, name):

        target = str(name).strip().lower()

        results = []

        for collection in self.data.values():

            for item in collection:

                if item["name"].strip().lower() == target:

                    results.append(item)

        return results

    # ========================================================
    # HIERARCHY
    # ========================================================

    def get_hierarchy(self, code):

        result = {
            "provinsi": "",
            "kabupaten_kota": "",
            "kecamatan": "",
            "kelurahan_desa": "",
            "kode_wilayah": code or ""
        }

        if not code:

            return result

        parts = code.split(".")

        # ----------------------------------------------------
        # PROVINCE
        # ----------------------------------------------------

        if len(parts) >= 1:

            province_code = parts[0]

            province = self.province_by_code.get(
                province_code
            )

            if province:

                result["provinsi"] = province["name"]

        # ----------------------------------------------------
        # REGENCY
        # ----------------------------------------------------

        if len(parts) >= 2:

            regency_code = ".".join(parts[:2])

            regency = self.regency_by_code.get(
                regency_code
            )

            if regency:

                result["kabupaten_kota"] = (
                    regency["name"]
                )

        # ----------------------------------------------------
        # DISTRICT
        # ----------------------------------------------------

        if len(parts) >= 3:

            district_code = ".".join(parts[:3])

            district = self.district_by_code.get(
                district_code
            )

            if district:

                result["kecamatan"] = (
                    district["name"]
                )

        # ----------------------------------------------------
        # VILLAGE
        # ----------------------------------------------------

        if len(parts) >= 4:

            village = self.village_by_code.get(
                code
            )

            if village:

                result["kelurahan_desa"] = (
                    village["name"]
                )

        return result