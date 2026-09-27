import logging
import sys
from pathlib import Path
import pandas as pd 

from config import (
    APP_NAME,
    VERSION,
    INPUT_FILE,
    OUTPUT_FILE,
    LOG_FILE,
    MAX_ADDRESS_LENGTH,
)

from wilayah_database import (
    WilayahDatabase
)

from address_parser import (
    AddressParser
)

from geocoder import (
    Geocoder
)

from excel_handler import (
    ExcelHandler
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
    encoding="utf-8"
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):

    if value is None:

        return ""

    return str(
        value
    ).strip()


def build_queries(
    address,
    parsed
):

    queries = []

    address = clean_text(
        address
    )

    province = clean_text(
        parsed.get(
            "provinsi"
        )
    )

    regency = clean_text(
        parsed.get(
            "kabupaten_kota"
        )
    )

    district = clean_text(
        parsed.get(
            "kecamatan"
        )
    )

    village = clean_text(
        parsed.get(
            "kelurahan_desa"
        )
    )

    # ========================================================
    # QUERY 1
    # ========================================================

    parts = [
        address,
        village,
        district,
        regency,
        province,
        "Indonesia"
    ]

    query = ", ".join(
        x for x in parts
        if x
    )

    if query:

        queries.append(
            query
        )

    # ========================================================
    # QUERY 2
    # ========================================================

    parts = [
        address,
        district,
        regency,
        province,
        "Indonesia"
    ]

    query = ", ".join(
        x for x in parts
        if x
    )

    if query:

        queries.append(
            query
        )

    # ========================================================
    # QUERY 3
    # ========================================================

    parts = [
        address,
        regency,
        province,
        "Indonesia"
    ]

    query = ", ".join(
        x for x in parts
        if x
    )

    if query:

        queries.append(
            query
        )

    # ========================================================
    # QUERY 4
    # ========================================================

    parts = [
        address,
        province,
        "Indonesia"
    ]

    query = ", ".join(
        x for x in parts
        if x
    )

    if query:

        queries.append(
            query
        )

    # ========================================================
    # UNIQUE
    # ========================================================

    unique_queries = []

    for query in queries:

        if query not in unique_queries:

            unique_queries.append(
                query
            )

    return unique_queries


# ============================================================
# FILL FROM OSM
# ============================================================

def fill_missing_regions(
    dataframe,
    index,
    osm_address
):

    # --------------------------------------------------------
    # PROVINCE
    # --------------------------------------------------------

    if not clean_text(
        dataframe.at[
            index,
            "Provinsi"
        ]
    ):

        dataframe.at[
            index,
            "Provinsi"
        ] = osm_address.get(
            "state",
            ""
        )

    # --------------------------------------------------------
    # CITY
    # --------------------------------------------------------

    if not clean_text(
        dataframe.at[
            index,
            "Kabupaten/Kota"
        ]
    ):

        dataframe.at[
            index,
            "Kabupaten/Kota"
        ] = (

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

    # --------------------------------------------------------
    # DISTRICT
    # --------------------------------------------------------

    if not clean_text(
        dataframe.at[
            index,
            "Kecamatan"
        ]
    ):

        dataframe.at[
            index,
            "Kecamatan"
        ] = (

            osm_address.get(
                "city_district",
                ""
            )

            or

            osm_address.get(
                "district",
                ""
            )

            or

            osm_address.get(
                "suburb",
                ""
            )

        )

    # --------------------------------------------------------
    # VILLAGE
    # --------------------------------------------------------

    if not clean_text(
        dataframe.at[
            index,
            "Kelurahan/Desa"
        ]
    ):

        dataframe.at[
            index,
            "Kelurahan/Desa"
        ] = (

            osm_address.get(
                "village",
                ""
            )

            or

            osm_address.get(
                "neighbourhood",
                ""
            )

        )

    # --------------------------------------------------------
    # POSTCODE
    # --------------------------------------------------------

    if not clean_text(
        dataframe.at[
            index,
            "Kode Pos"
        ]
    ):

        dataframe.at[
            index,
            "Kode Pos"
        ] = osm_address.get(
            "postcode",
            ""
        )


# ============================================================
# INITIALIZE OUTPUT
# ============================================================

def prepare_output_columns(dataframe):

    columns = [
        "Provinsi",
        "Kabupaten/Kota",
        "Kecamatan",
        "Kelurahan/Desa",
        "Kode Wilayah",
        "Kode Pos",
        "Latitude",
        "Longitude",
        "Alamat Hasil Geocoding",
        "Confidence",
        "Confidence Geocoding",
        "Metode",
        "Status",
        "OSM Type",
        "OSM ID",
        "OSM Importance",
    ]

    for column in columns:

        # Kalau kolom belum ada, buat sebagai object
        # agar bisa menerima string, integer, float, maupun None.
        if column not in dataframe.columns:

            dataframe[column] = pd.Series(
                [None] * len(dataframe),
                index=dataframe.index,
                dtype="object"
            )

        else:

            # Kalau kolom sudah ada dari Excel,
            # ubah menjadi object supaya tidak terkunci
            # sebagai string-only / numeric-only.
            dataframe[column] = dataframe[column].astype(
                "object"
            )

    return dataframe


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        f"{APP_NAME} v{VERSION}"
    )
    print(
        "Indonesia Address → Region → Coordinate"
    )
    print("=" * 70)

    logging.info(
        "Program dimulai."
    )

    # ========================================================
    # CHECK INPUT
    # ========================================================

    if not Path(
        INPUT_FILE
    ).exists():

        print()
        print(
            "ERROR: File input tidak ditemukan."
        )

        print(
            f"Masukkan Excel ke:"
        )

        print(
            INPUT_FILE
        )

        logging.error(
            "Input tidak ditemukan."
        )

        sys.exit(1)

    # ========================================================
    # DATABASE
    # ========================================================

    print()
    print(
        "Memuat database wilayah..."
    )

    database = WilayahDatabase()

    database.load()

    parser = AddressParser(
        database
    )

    geocoder = Geocoder()

    excel = ExcelHandler()

    # ========================================================
    # READ EXCEL
    # ========================================================

    print()
    print(
        "Membaca Excel..."
    )

    try:

        dataframe = excel.read(
            INPUT_FILE
        )

    except Exception as error:

        print()
        print(
            f"ERROR Excel: {error}"
        )

        logging.exception(
            "Gagal membaca Excel."
        )

        sys.exit(1)

    dataframe = prepare_output_columns(
        dataframe
    )

    total = len(
        dataframe
    )

    print(
        f"Total alamat: {total}"
    )

    # ========================================================
    # PROCESS
    # ========================================================

    for index, row in dataframe.iterrows():

        number = index + 1

        print()
        print(
            "-" * 70
        )

        print(
            f"[{number}/{total}]"
        )

        address = clean_text(
            row.get(
                "Alamat",
                ""
            )
        )

        print(
            f"Alamat: {address}"
        )

        logging.info(
            "Memproses baris %s: %s",
            number,
            address
        )

        # ----------------------------------------------------
        # EMPTY
        # ----------------------------------------------------

        if not address:

            dataframe.at[
                index,
                "Status"
            ] = "EMPTY"

            continue

        # ----------------------------------------------------
        # LENGTH SECURITY
        # ----------------------------------------------------

        if len(address) > MAX_ADDRESS_LENGTH:

            dataframe.at[
                index,
                "Status"
            ] = "ADDRESS_TOO_LONG"

            logging.warning(
                "Alamat terlalu panjang baris %s",
                number
            )

            continue

        # ====================================================
        # REGION PARSER
        # ====================================================

        parsed = parser.parse(
            address
        )

        dataframe.at[
            index,
            "Provinsi"
        ] = parsed[
            "provinsi"
        ]

        dataframe.at[
            index,
            "Kabupaten/Kota"
        ] = parsed[
            "kabupaten_kota"
        ]

        dataframe.at[
            index,
            "Kecamatan"
        ] = parsed[
            "kecamatan"
        ]

        dataframe.at[
            index,
            "Kelurahan/Desa"
        ] = parsed[
            "kelurahan_desa"
        ]

        dataframe.at[
            index,
            "Kode Wilayah"
        ] = parsed[
            "kode_wilayah"
        ]

        dataframe.at[
            index,
            "Confidence"
        ] = parsed[
            "confidence"
        ]

        # ====================================================
        # QUERY
        # ====================================================

        queries = build_queries(
            address,
            parsed
        )

        found = None

        selected_query = ""

        # ====================================================
        # GEOCODING
        # ====================================================

        for query in queries:

            print(
                f"Mencari: {query}"
            )

            logging.info(
                "Query: %s",
                query
            )

            result = geocoder.search(
                query
            )

            if result:

                found = result

                selected_query = query

                break

        # ====================================================
        # NOT FOUND
        # ====================================================

        if not found:

            dataframe.at[
                index,
                "Status"
            ] = "NOT_FOUND"

            dataframe.at[
                index,
                "Metode"
            ] = (
                "REGION_DATABASE_ONLY"
            )

            print(
                "Tidak ditemukan koordinat."
            )

            continue

        # ====================================================
        # PARSE OSM
        # ====================================================

        geo = geocoder.parse_result(
            found
        )

        latitude = geo[
            "latitude"
        ]

        longitude = geo[
            "longitude"
        ]

        osm_address = geo[
            "address"
        ]

        # ====================================================
        # VALIDATE COORDINATE
        # ====================================================

        if not latitude or not longitude:

            dataframe.at[
                index,
                "Status"
            ] = "INVALID_COORDINATE"

            continue

        # ====================================================
        # FILL MISSING REGION
        # ====================================================

        fill_missing_regions(
            dataframe,
            index,
            osm_address
        )

        # ====================================================
        # GEOCODE CONFIDENCE
        # ====================================================

        geocode_confidence = (
            parser.compare_geocode(
                parsed,
                osm_address
            )
        )

        dataframe.at[
            index,
            "Confidence Geocoding"
        ] = geocode_confidence

        # ====================================================
        # SAVE COORDINATE
        # ====================================================

        dataframe.at[
            index,
            "Latitude"
        ] = latitude

        dataframe.at[
            index,
            "Longitude"
        ] = longitude

        dataframe.at[
            index,
            "Alamat Hasil Geocoding"
        ] = geo[
            "display_name"
        ]

        dataframe.at[
            index,
            "OSM Type"
        ] = geo[
            "osm_type"
        ]

        dataframe.at[
            index,
            "OSM ID"
        ] = geo[
            "osm_id"
        ]

        dataframe.at[
            index,
            "OSM Importance"
        ] = geo[
            "importance"
        ]

        # ====================================================
        # METHOD
        # ====================================================

        if parsed[
            "matched_level"
        ] == "KELURAHAN/DESA":

            method = (
                "WILAYAH_DATABASE + NOMINATIM"
            )

        elif parsed[
            "matched_level"
        ] == "KECAMATAN":

            method = (
                "KECAMATAN_DATABASE + NOMINATIM"
            )

        elif parsed[
            "matched_level"
        ] == "KABUPATEN/KOTA":

            method = (
                "KOTA_DATABASE + NOMINATIM"
            )

        elif parsed[
            "matched_level"
        ] == "PROVINSI":

            method = (
                "PROVINSI_DATABASE + NOMINATIM"
            )

        else:

            method = "NOMINATIM"

        dataframe.at[
            index,
            "Metode"
        ] = method

        # ====================================================
        # STATUS
        # ====================================================

        if parsed[
            "ambiguous"
        ]:

            status = "AMBIGUOUS"

        elif (
            parsed["confidence"] >= 85
            and geocode_confidence >= 0.5
        ):

            status = "FOUND"

        elif (
            parsed["confidence"] >= 65
        ):

            status = "REGION_MATCH"

        else:

            status = "FOUND_CHECK"

        dataframe.at[
            index,
            "Status"
        ] = status

        # ====================================================
        # DISPLAY
        # ====================================================

        print(
            f"Latitude  : {latitude}"
        )

        print(
            f"Longitude : {longitude}"
        )

        print(
            f"Provinsi  : "
            f"{dataframe.at[index, 'Provinsi']}"
        )

        print(
            f"Kota      : "
            f"{dataframe.at[index, 'Kabupaten/Kota']}"
        )

        print(
            f"Kecamatan : "
            f"{dataframe.at[index, 'Kecamatan']}"
        )

        print(
            f"Kelurahan: "
            f"{dataframe.at[index, 'Kelurahan/Desa']}"
        )

        print(
            f"Status    : {status}"
        )

        # ====================================================
        # PERIODIC SAVE
        # ====================================================

        if number % 10 == 0:

            try:

                excel.save(
                    dataframe,
                    OUTPUT_FILE
                )

                print(
                    "Progress tersimpan."
                )

            except Exception as error:

                logging.error(
                    "Gagal menyimpan progress: %s",
                    error
                )

    # ========================================================
    # FINAL SAVE
    # ========================================================

    print()
    print("=" * 70)
    print(
        "MENYIMPAN HASIL AKHIR..."
    )
    print("=" * 70)

    try:

        excel.save(
            dataframe,
            OUTPUT_FILE
        )

    except Exception as error:

        print(
            f"Gagal menyimpan: {error}"
        )

        logging.exception(
            "Gagal menyimpan output."
        )

        sys.exit(1)

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("SELESAI")
    print("=" * 70)

    print(
        f"Input : {INPUT_FILE}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print()

    if "Status" in dataframe.columns:

        print(
            dataframe[
                "Status"
            ].value_counts(
                dropna=False
            ).to_string()
        )

    print()
    print(
        "Log:"
    )

    print(
        LOG_FILE
    )

    logging.info(
        "Program selesai."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()