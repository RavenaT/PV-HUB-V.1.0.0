from pathlib import Path


# ============================================================
# APPLICATION
# ============================================================

APP_NAME = "PV HUB"
VERSION = "1.0.0"


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(exist_ok=True)
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# FILES
# ============================================================

INPUT_FILE = INPUT_DIR / "alamat.xlsx"

OUTPUT_FILE = OUTPUT_DIR / "hasil_geocoding.xlsx"

WILAYAH_FILE = DATA_DIR / "wilayah.json"

GEOCODE_CACHE_FILE = DATA_DIR / "geocode_cache.json"

LOG_FILE = DATA_DIR / "geocoder.log"


# ============================================================
# WILAYAH API
# ============================================================

WILAYAH_API = "https://wilayah.id/api"


# ============================================================
# NOMINATIM
# ============================================================

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

USER_AGENT = (
    "PV HUB/1.0 "
    "(local-office-address-geocoder)"
)

REQUEST_TIMEOUT = 30

MAX_RETRIES = 3

# Public Nominatim meminta maksimum 1 request/detik.
REQUEST_DELAY = 1.1


# ============================================================
# MATCHING
# ============================================================

FUZZY_THRESHOLD = 85

MIN_GEOCODE_SCORE = 0.45


# ============================================================
# SECURITY LIMITS
# ============================================================

MAX_EXCEL_SIZE_MB = 50

MAX_ADDRESS_LENGTH = 500


# ============================================================
# EXCEL FORMULA PROTECTION
# ============================================================

DANGEROUS_EXCEL_PREFIXES = (
    "=",
    "+",
    "-",
    "@"
)