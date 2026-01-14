"""Configuration settings for the Kirja.fi scraper."""

# API Settings
BASE_URL = "https://kirja.fi"
COLLECTIONS_ENDPOINT = "/collections/all/products.json"
PRODUCT_ENDPOINT = "/products/{handle}.json"

# Concurrency Settings
MAX_CONCURRENT_REQUESTS = 20  # Number of parallel requests
REQUEST_DELAY = 0.05  # Delay between requests in seconds (only for collection pages)
HTML_REQUEST_DELAY = 0.1  # Delay between HTML requests (higher to avoid 429 errors)
SEMAPHORE_LIMIT = 20  # Maximum concurrent operations

# Testing Settings
TEST_LIMIT = None  # Limit number of products to fetch (None for no limit)

# Retry Settings
MAX_RETRIES = 3
RETRY_WAIT_MIN = 2  # Minimum wait time for retry (seconds)
RETRY_WAIT_MAX = 10  # Maximum wait time for retry (seconds)

# Timeout Settings
REQUEST_TIMEOUT = 30  # Timeout for HTTP requests (seconds)

# File Settings
DATA_DIR = "data"
BOOKS_DIR = "data/books"
IMAGES_DIR = "data/images"
METADATA_FILE = "data/metadata.json"

# User Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Image Settings
DOWNLOAD_IMAGES = True

# HTML Metadata Extraction Settings
FETCH_HTML_METADATA = True  # Extract avainsanat, kirjastoluokka, aiheet from product pages
HTML_METADATA_FIELDS = [
    'Avainsanat',       # Keywords
    'Kirjastoluokka',   # Library classification
    'Aiheet',           # Topics/subjects
    'Kustantaja',       # Publisher (alternative source)
    'Julkaisu',         # Publication date
    'Sidosasu',         # Binding type
    'Sivumäärä',        # Page count
    'Mitat',            # Dimensions
    'Paino'             # Weight
]
