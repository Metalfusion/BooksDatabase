"""
Kirja.fi Books Scraper - Async implementation with retry logic and parallelism control.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime

import aiohttp
import aiofiles
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
        self.stats = {
            'books_fetched': 0,
            'images_downloaded': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Create directories
        for directory in [config.DATA_DIR, config.BOOKS_DIR, config.IMAGES_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': config.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(min=config.RETRY_WAIT_MIN, max=config.RETRY_WAIT_MAX),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def fetch_json(self, url: str) -> Dict:
        """Fetch JSON data from URL with retry logic."""
        async with self.semaphore:
            await asyncio.sleep(config.REQUEST_DELAY)
            
            logger.debug(f"Fetching: {url}")
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.json()
    
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
            await asyncio.sleep(config.REQUEST_DELAY)
            
            logger.debug(f"Downloading image: {url}")
            async with self.session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(content)
                
                return True
    
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
    
    async def fetch_all_products(self) -> List[Dict]:
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
            page += 1
        
        logger.info(f"Total products fetched: {len(all_products)}")
        return all_products
    
    async def save_book_data(self, product: Dict) -> bool:
        """Save book data to JSON file."""
        try:
            handle = product.get('handle', '')
            if not handle:
                logger.warning("Product missing handle, skipping")
                return False
            
            # Enrich product data with URLs
            product['_metadata'] = {
                'fetched_at': datetime.now().isoformat(),
                'product_url': f"{config.BASE_URL}/products/{handle}",
                'api_url': f"{config.BASE_URL}/products/{handle}.json"
            }
            
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
        """Process a single product: save data and download images."""
        try:
            # Save book data
            await self.save_book_data(product)
            
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
            products = await self.fetch_all_products()
            
            if not products:
                logger.warning("No products found!")
                return
            
            # Process all products with progress bar and batch processing
            logger.info(f"Processing {len(products)} products...")
            logger.info("This may take a while - progress will update every 10 products")
            
            # Process in batches to show progress
            batch_size = 10
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
