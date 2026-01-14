"""Configuration settings for the Kirja.fi scraper."""

# API Settings
BASE_URL = "https://kirja.fi"
COLLECTIONS_ENDPOINT = "/collections/all/products.json"
PRODUCT_ENDPOINT = "/products/{handle}.json"

# Concurrency Settings
MAX_CONCURRENT_REQUESTS = 5  # Number of parallel requests
REQUEST_DELAY = 0.05  # Delay between requests in seconds
SEMAPHORE_LIMIT = 10  # Maximum concurrent operations

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
IMAGE_MAX_WIDTH = 1200  # Resize images larger than this width
