"""
Kirja.fi Books Scraper - Async implementation with retry logic and parallelism control.
"""

import asyncio
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime

import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from tqdm.asyncio import tqdm_asyncio

import config

# Fix unicode output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class KirjaFiScraper:
    """Async scraper for kirja.fi book data."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(config.SEMAPHORE_LIMIT)
        self.rate_limit_delay = config.HTML_REQUEST_DELAY  # Adaptive delay for HTML requests
        self.rate_limit_hits = 0  # Track consecutive 429 errors
        self.stats = {
            'books_fetched': 0,
            'images_downloaded': 0,
            'errors': 0,
            'rate_limit_429': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Create directories
        for directory in [config.DATA_DIR, config.BOOKS_DIR, config.IMAGES_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        
        # Browser-like headers to avoid aggressive rate limiting
        headers = {
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fi;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_json(self, url: str, with_delay: bool = True) -> Dict:
        """Fetch JSON data from URL with adaptive rate limiting."""
        max_retries = config.MAX_RETRIES + 2  # Extra retries for 429 errors
        
        for attempt in range(max_retries):
            try:
                async with self.semaphore:
                    if with_delay:
                        await asyncio.sleep(self.rate_limit_delay)
                    
                    logger.debug(f"Fetching JSON: {url} (delay: {self.rate_limit_delay:.2f}s)")
                    async with self.session.get(url) as response:
                        if response.status == 429:
                            # Rate limit hit - increase delay exponentially
                            self.rate_limit_hits += 1
                            self.rate_limit_delay = min(self.rate_limit_delay * 2, 10.0)
                            self.stats['rate_limit_429'] += 1
                            
                            retry_after = response.headers.get('Retry-After')
                            wait_time = float(retry_after) if retry_after else self.rate_limit_delay * (attempt + 1)
                            
                            logger.warning(
                                f"Rate limit hit (429) for {url}. "
                                f"Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}. "
                                f"New base delay: {self.rate_limit_delay:.2f}s"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        
                        response.raise_for_status()
                        
                        # Success - gradually reduce delay if we haven't hit limits recently
                        if self.rate_limit_hits > 0:
                            self.rate_limit_hits = max(0, self.rate_limit_hits - 1)
                            if self.rate_limit_hits == 0:
                                self.rate_limit_delay = max(config.HTML_REQUEST_DELAY, self.rate_limit_delay * 0.8)
                        
                        return await response.json()
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = config.RETRY_WAIT_MIN * (2 ** attempt)
                    logger.warning(f"Error fetching {url}: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        
        raise aiohttp.ClientError(f"Failed to fetch {url} after {max_retries} attempts")
    
    async def fetch_html(self, url: str, with_delay: bool = True) -> str:
        """Fetch HTML content from URL with adaptive rate limiting."""
        max_retries = config.MAX_RETRIES + 2  # Extra retries for 429 errors
        
        for attempt in range(max_retries):
            try:
                async with self.semaphore:
                    if with_delay:
                        # Use adaptive delay that increases with 429 hits
                        await asyncio.sleep(self.rate_limit_delay)
                    
                    logger.debug(f"Fetching HTML: {url} (delay: {self.rate_limit_delay:.2f}s)")
                    async with self.session.get(url) as response:
                        if response.status == 429:
                            # Rate limit hit - increase delay exponentially
                            self.rate_limit_hits += 1
                            self.rate_limit_delay = min(self.rate_limit_delay * 2, 10.0)
                            self.stats['rate_limit_429'] += 1
                            
                            retry_after = response.headers.get('Retry-After')
                            wait_time = float(retry_after) if retry_after else self.rate_limit_delay * (attempt + 1)
                            
                            logger.warning(
                                f"Rate limit hit (429) for {url}. "
                                f"Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}. "
                                f"New base delay: {self.rate_limit_delay:.2f}s"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        
                        response.raise_for_status()
                        
                        # Success - gradually reduce delay if we haven't hit limits recently
                        if self.rate_limit_hits > 0:
                            self.rate_limit_hits = max(0, self.rate_limit_hits - 1)
                            if self.rate_limit_hits == 0:
                                self.rate_limit_delay = max(config.HTML_REQUEST_DELAY, self.rate_limit_delay * 0.8)
                        
                        return await response.text()
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = config.RETRY_WAIT_MIN * (2 ** attempt)
                    logger.warning(f"Error fetching {url}: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        
        raise aiohttp.ClientError(f"Failed to fetch {url} after {max_retries} attempts")
    
    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(min=config.RETRY_WAIT_MIN, max=config.RETRY_WAIT_MAX),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def download_image(self, url: str, filepath: Path) -> bool:
        """Download image from URL with retry logic."""
        if filepath.exists():
            logger.debug(f"Image already exists: {filepath}")
            return True
        
        async with self.semaphore:
            logger.debug(f"Downloading image: {url}")
            async with self.session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(content)
                
                return True
    
    def parse_html_metadata(self, html: str) -> Dict[str, Any]:
        """Parse metadata from product page HTML.
        
        Extracts fields like avainsanat, kirjastoluokka, aiheet from the
        'Lisätiedot' (Additional Information) accordion section.
        """
        def clean_text(text: str) -> str:
            text = text.replace('\u00a0', ' ')
            text = re.sub(r"\s+", " ", text).strip()
            return text

        def split_items(text: str) -> List[str]:
            # Common separators seen on kirja.fi product pages
            text = clean_text(text)
            if not text:
                return []

            # Normalize separator variants
            text = text.replace('·', '•')

            # Prefer bullet separator when present
            if '•' in text:
                parts = [clean_text(p) for p in re.split(r"\s*•\s*", text) if clean_text(p)]
                return parts

            # If we used a custom separator in get_text
            if '|' in text:
                parts = [clean_text(p) for p in text.split('|') if clean_text(p)]
                return parts

            return [text]

        def extract_list(dd) -> List[str]:
            # Prefer explicit items if present
            li_items = [clean_text(li.get_text(" ", strip=True)) for li in dd.find_all('li')]
            li_items = [i for i in li_items if i]
            if len(li_items) > 1:
                return li_items

            a_items = [clean_text(a.get_text(" ", strip=True)) for a in dd.find_all('a')]
            a_items = [i for i in a_items if i]
            if len(a_items) > 1:
                return a_items

            # Fall back to text, but keep structural separators
            text = dd.get_text(separator=' | ', strip=True)
            return split_items(text)

        def parse_int(text: str) -> Optional[int]:
            m = re.search(r"(\d+)", text)
            if not m:
                return None
            try:
                return int(m.group(1))
            except ValueError:
                return None

        def parse_dimensions_mm(text: str) -> Optional[List[int]]:
            # Example: "147 mm × 222 mm × 35 mm" (line breaks possible)
            text = clean_text(text).replace('×', 'x')
            nums = re.findall(r"(\d+(?:[\.,]\d+)?)", text)
            if len(nums) < 2:
                return None
            values: List[int] = []
            for n in nums[:3]:
                n = n.replace(',', '.')
                try:
                    values.append(int(round(float(n))))
                except ValueError:
                    return None
            return values

        metadata: Dict[str, Any] = {}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all dt/dd pairs (definition lists)
            for dt in soup.find_all('dt'):
                dd = dt.find_next_sibling('dd')
                if dd:
                    key = dt.get_text(strip=True)

                    # Only store fields we're interested in
                    if key not in config.HTML_METADATA_FIELDS:
                        continue

                    if key in ('Avainsanat', 'Aiheet'):
                        value = extract_list(dd)
                    else:
                        value = clean_text(dd.get_text(separator=' ', strip=True))

                    if key == 'Sivumäärä':
                        parsed = parse_int(str(value))
                        value = parsed if parsed is not None else value
                    elif key == 'Paino':
                        parsed = parse_int(str(value))
                        value = parsed if parsed is not None else value
                    elif key == 'Mitat':
                        dims = parse_dimensions_mm(str(value))
                        value = dims if dims is not None else value

                    metadata[key] = value

                    preview = str(value)
                    logger.debug(f"Extracted metadata: {key} = {preview[:50]}...")
            
        except Exception as e:
            logger.error(f"Error parsing HTML metadata: {e}")
        
        return metadata
    
    async def fetch_product_metadata(self, handle: str) -> Dict[str, Any]:
        """Fetch and parse HTML metadata for a product."""
        if not config.FETCH_HTML_METADATA:
            return {}
        
        try:
            url = f"{config.BASE_URL}/products/{handle}"
            html = await self.fetch_html(url)
            metadata = self.parse_html_metadata(html)
            return metadata
        except Exception as e:
            logger.error(f"Error fetching HTML metadata for {handle}: {e}")
            return {}
    
    async def fetch_collection_page(self, page: int) -> List[Dict]:
        """Fetch a single page from the collections API."""
        url = f"{config.BASE_URL}{config.COLLECTIONS_ENDPOINT}?page={page}"
        
        try:
            data = await self.fetch_json(url)
            products = data.get('products', [])
            
            if products:
                logger.info(f"Page {page}: Fetched {len(products)} products")
            
            return products
        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            self.stats['errors'] += 1
            return []
    
    async def fetch_all_products(self, limit: int = None) -> List[Dict]:
        """Fetch all products from all pages."""
        logger.info("Starting to fetch all products...")
        all_products = []
        page = 1
        max_pages = 200  # Safety limit
        
        while page <= max_pages:
            products = await self.fetch_collection_page(page)
            
            if not products:
                logger.info(f"No more products found at page {page}")
                break
            
            all_products.extend(products)
            
            # Check if we've reached the limit
            if limit and len(all_products) >= limit:
                logger.info(f"Reached limit of {limit} products")
                all_products = all_products[:limit]
                break
            
            page += 1
        
        logger.info(f"Total products fetched: {len(all_products)}")
        return all_products
    
    async def save_book_data(self, product: Dict, html_metadata: Dict[str, Any] = None) -> bool:
        """Save book data to JSON file."""
        try:
            handle = product.get('handle', '')
            if not handle:
                logger.warning("Product missing handle, skipping")
                return False
            
            # Enrich product data with URLs and metadata
            product['_metadata'] = {
                'fetched_at': datetime.now().isoformat(),
                'product_url': f"{config.BASE_URL}/products/{handle}",
                'api_url': f"{config.BASE_URL}/products/{handle}.json"
            }
            
            # Add HTML metadata if available
            if html_metadata:
                # Store with cleaner keys (English, lowercase, underscored)
                metadata_mapping = {
                    'Avainsanat': 'keywords',
                    'Kirjastoluokka': 'library_classification',
                    'Aiheet': 'topics',
                    'Kustantaja': 'publisher_alt',
                    'Julkaisu': 'publication_date',
                    'Sidosasu': 'binding',
                    'Sivumäärä': 'page_count',
                    'Mitat': 'dimensions',
                    'Paino': 'weight'
                }
                
                product['_html_metadata'] = {}
                for finnish_key, english_key in metadata_mapping.items():
                    if finnish_key in html_metadata:
                        product['_html_metadata'][english_key] = html_metadata[finnish_key]
            
            filepath = Path(config.BOOKS_DIR) / f"{handle}.json"
            
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(product, ensure_ascii=False, indent=2))
            
            self.stats['books_fetched'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error saving book data for {product.get('handle', 'unknown')}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def download_book_images(self, product: Dict) -> int:
        """Download all images for a book."""
        if not config.DOWNLOAD_IMAGES:
            return 0
        
        images_downloaded = 0
        images = product.get('images', [])
        
        if not images:
            return 0
        
        # Get ISBN from variant SKU for filename
        variants = product.get('variants', [])
        isbn = variants[0].get('sku', '') if variants else ''
        
        if not isbn:
            # Fallback to product ID
            isbn = str(product.get('id', ''))
        
        for idx, image in enumerate(images):
            try:
                image_url = image.get('src', '')
                if not image_url:
                    continue
                
                # Parse URL to get extension
                parsed = urlparse(image_url)
                path_parts = parsed.path.split('.')
                ext = path_parts[-1].split('?')[0] if len(path_parts) > 1 else 'jpg'
                
                # Create filename
                if idx == 0:
                    filename = f"{isbn}.{ext}"
                else:
                    filename = f"{isbn}_{idx}.{ext}"
                
                filepath = Path(config.IMAGES_DIR) / filename
                
                if await self.download_image(image_url, filepath):
                    images_downloaded += 1
                    self.stats['images_downloaded'] += 1
                
            except Exception as e:
                logger.error(f"Error downloading image for {product.get('handle', 'unknown')}: {e}")
                self.stats['errors'] += 1
        
        return images_downloaded
    
    async def process_product(self, product: Dict) -> bool:
        """Process a single product: fetch HTML metadata, save data and download images."""
        try:
            handle = product.get('handle', '')
            
            # Fetch HTML metadata if enabled
            html_metadata = {}
            if config.FETCH_HTML_METADATA and handle:
                html_metadata = await self.fetch_product_metadata(handle)
            
            # Save book data with metadata
            await self.save_book_data(product, html_metadata)
            
            # Download images
            await self.download_book_images(product)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing product {product.get('handle', 'unknown')}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def save_metadata(self, products: List[Dict]):
        """Save metadata about the scraping session."""
        metadata = {
            'scraped_at': datetime.now().isoformat(),
            'total_products': len(products),
            'statistics': self.stats,
            'config': {
                'max_concurrent_requests': config.MAX_CONCURRENT_REQUESTS,
                'request_delay': config.REQUEST_DELAY,
                'download_images': config.DOWNLOAD_IMAGES
            },
            'products_summary': [
                {
                    'handle': p.get('handle', ''),
                    'title': p.get('title', ''),
                    'vendor': p.get('vendor', ''),
                    'product_type': p.get('product_type', ''),
                    'isbn': p.get('variants', [{}])[0].get('sku', '') if p.get('variants') else ''
                }
                for p in products
            ]
        }
        
        async with aiofiles.open(config.METADATA_FILE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, ensure_ascii=False, indent=2))
        
        logger.info(f"Metadata saved to {config.METADATA_FILE}")
    
    async def run(self):
        """Main scraper execution."""
        self.stats['start_time'] = datetime.now().isoformat()
        logger.info("=" * 60)
        logger.info("Starting Kirja.fi scraper")
        logger.info("=" * 60)
        
        try:
            # Fetch all products
            products = await self.fetch_all_products(limit=config.TEST_LIMIT)
            
            if not products:
                logger.warning("No products found!")
                return
            
            # Process all products with progress bar and batch processing
            logger.info(f"Processing {len(products)} products...")
            logger.info("This may take a while - progress will update every 100 products")
            
            # Process in batches to show progress
            batch_size = 100
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]
                tasks = [self.process_product(product) for product in batch]
                await asyncio.gather(*tasks)
                
                processed = min(i + batch_size, len(products))
                logger.info(f"Progress: {processed}/{len(products)} products processed ({processed*100//len(products)}%)")
            
            # Save metadata
            await self.save_metadata(products)
            
            self.stats['end_time'] = datetime.now().isoformat()
            
            # Print summary
            logger.info("=" * 60)
            logger.info("Scraping completed!")
            logger.info(f"Books fetched: {self.stats['books_fetched']}")
            logger.info(f"Images downloaded: {self.stats['images_downloaded']}")
            logger.info(f"HTML metadata extraction: {'Enabled' if config.FETCH_HTML_METADATA else 'Disabled'}")
            if config.FETCH_HTML_METADATA:
                logger.info(f"Rate limit hits (429): {self.stats['rate_limit_429']}")
                logger.info(f"Final request delay: {self.rate_limit_delay:.2f}s")
            logger.info(f"Errors: {self.stats['errors']}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Fatal error during scraping: {e}", exc_info=True)
            raise


async def main():
    """Main entry point."""
    async with KirjaFiScraper() as scraper:
        await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
