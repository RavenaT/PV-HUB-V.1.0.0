import re

from rapidfuzz import fuzz


class AddressParser:

    def __init__(self, database):

        self.db = database

    # ========================================================
    # NORMALIZE
    # ========================================================

    @staticmethod
    def normalize(text):

        if text is None:

            return ""

        text = str(text).lower().strip()

        replacements = {

            "jl.": "jalan ",
            "jln.": "jalan ",
            "jln ": "jalan ",

            "kel.": "kelurahan ",
            "kel ": "kelurahan ",

            "kec.": "kecamatan ",
            "kec ": "kecamatan ",

            "kab.": "kabupaten ",
            "kab ": "kabupaten ",

            "ds.": "desa ",
            "ds ": "desa ",

        }

        for old, new in replacements.items():

            text = text.replace(
                old,
                new
            )

        text = re.sub(
            r"[^a-z0-9\s.,/-]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # ========================================================
    # NAME IN ADDRESS
    # ========================================================

    def name_exists(
        self,
        name,
        address
    ):

        name = self.normalize(name)

        address = self.normalize(address)

        if not name or not address:

            return False

        return name in address

    # ========================================================
    # EXACT DETECTION
    # ========================================================

    def detect(self, address):

        normalized = self.normalize(
            address
        )

        result = {
            "province": [],
            "regency": [],
            "district": [],
            "village": []
        }

        # ----------------------------------------------------
        # PROVINCE
        # ----------------------------------------------------

        for item in self.db.data["provinces"]:

            if self.name_exists(
                item["name"],
                normalized
            ):

                result["province"].append(
                    item
                )

        # ----------------------------------------------------
        # REGENCY
        # ----------------------------------------------------

        for item in self.db.data["regencies"]:

            if self.name_exists(
                item["name"],
                normalized
            ):

                result["regency"].append(
                    item
                )

        # ----------------------------------------------------
        # DISTRICT
        # ----------------------------------------------------

        for item in self.db.data["districts"]:

            if self.name_exists(
                item["name"],
                normalized
            ):

                result["district"].append(
                    item
                )

        # ----------------------------------------------------
        # VILLAGE
        # ----------------------------------------------------

        for item in self.db.data["villages"]:

            if self.name_exists(
                item["name"],
                normalized
            ):

                result["village"].append(
                    item
                )

        return result

    # ========================================================
    # PARSE
    # ========================================================

    def parse(self, address):

        detected = self.detect(
            address
        )

        result = {
            "provinsi": "",
            "kabupaten_kota": "",
            "kecamatan": "",
            "kelurahan_desa": "",
            "kode_wilayah": "",
            "confidence": 0,
            "ambiguous": False,
            "matched_level": ""
        }

        # ====================================================
        # VILLAGE
        # ====================================================

        villages = detected["village"]

        if len(villages) == 1:

            village = villages[0]

            hierarchy = self.db.get_hierarchy(
                village["code"]
            )

            result.update(
                hierarchy
            )

            result["confidence"] = 95

            result["matched_level"] = (
                "KELURAHAN/DESA"
            )

            return result

        if len(villages) > 1:

            result["ambiguous"] = True

        # ====================================================
        # DISTRICT
        # ====================================================

        districts = detected["district"]

        if len(districts) == 1:

            district = districts[0]

            hierarchy = self.db.get_hierarchy(
                district["code"]
            )

            result.update(
                hierarchy
            )

            result["confidence"] = 85

            result["matched_level"] = (
                "KECAMATAN"
            )

            return result

        if len(districts) > 1:

            result["ambiguous"] = True

        # ====================================================
        # REGENCY
        # ====================================================

        regencies = detected["regency"]

        if len(regencies) == 1:

            regency = regencies[0]

            hierarchy = self.db.get_hierarchy(
                regency["code"]
            )

            result.update(
                hierarchy
            )

            result["confidence"] = 75

            result["matched_level"] = (
                "KABUPATEN/KOTA"
            )

            return result

        if len(regencies) > 1:

            result["ambiguous"] = True

        # ====================================================
        # PROVINCE
        # ====================================================

        provinces = detected["province"]

        if len(provinces) == 1:

            province = provinces[0]

            hierarchy = self.db.get_hierarchy(
                province["code"]
            )

            result.update(
                hierarchy
            )

            result["confidence"] = 65

            result["matched_level"] = (
                "PROVINSI"
            )

            return result

        if len(provinces) > 1:

            result["ambiguous"] = True

        return result

    # ========================================================
    # VALIDATE GEOCODE
    # ========================================================

    def compare_geocode(
        self,
        parsed,
        osm_address
    ):

        if not osm_address:

            return 0

        score = 0

        total = 0

        fields = [

            (
                parsed["provinsi"],
                osm_address.get(
                    "state",
                    ""
                )
            ),

            (
                parsed["kabupaten_kota"],
                (
                    osm_address.get(
                        "city",
                        ""
                    )
                    or
                    osm_address.get(
                        "town",
                        ""
                    )
                    or
                    osm_address.get(
                        "municipality",
                        ""
                    )
                )
            ),

            (
                parsed["kecamatan"],
                (
                    osm_address.get(
                        "suburb",
                        ""
                    )
                    or
                    osm_address.get(
                        "city_district",
                        ""
                    )
                    or
                    osm_address.get(
                        "district",
                        ""
                    )
                )
            ),

            (
                parsed["kelurahan_desa"],
                (
                    osm_address.get(
                        "village",
                        ""
                    )
                    or
                    osm_address.get(
                        "town",
                        ""
                    )
                )
            )
        ]

        for expected, actual in fields:

            if not expected:

                continue

            total += 1

            if not actual:

                continue

            similarity = fuzz.ratio(
                str(expected).lower(),
                str(actual).lower()
            )

            if similarity >= 80:

                score += 1

        if total == 0:

            return 0

        return round(
            score / total,
            2
        )