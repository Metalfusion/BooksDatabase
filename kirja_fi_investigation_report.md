# Kirja.fi Website Investigation Report
**Date:** January 14, 2026  
**Purpose:** Determine methods for collecting book data from kirja.fi for local database

## Executive Summary

Kirja.fi is a Shopify-powered online bookstore with **6,591+ products**. The site provides multiple API endpoints for data collection, making it possible to build a comprehensive local database without heavy web scraping.

## Key Findings

### 1. **Platform & Technology Stack**
- **Platform:** Shopify (identified from API endpoints and structure)
- **Storefront Access Token:** `689855d8c96298705f0a694d6416529d`
- **Shop ID:** `60556214531`
- **Primary API:** Shopify GraphQL API (unstable version)
- **CDN:** Cloudflare

### 2. **Available APIs**

#### A. Shopify Products API (JSON Format) ✅ **RECOMMENDED**
- **Endpoint:** `https://kirja.fi/products/{handle}.json`
- **Example:** `https://kirja.fi/products/prosessi-9789523522725.json`
- **Features:**
  - Complete product information
  - No authentication required
  - Clean JSON format
  - Easy to parse

**Sample Data Structure:**
```json
{
  "product": {
    "id": 8643252945229,
    "title": "Prosessi",
    "body_html": "<description>",
    "vendor": "Kosmos",
    "product_type": "Pehmeäkantinen",
    "created_at": "2023-08-31T16:17:57+03:00",
    "handle": "prosessi-9789523522725",
    "tags": ["2024 / 1", "Kaunokirjallisuus", ...],
    "variants": [{
      "sku": "9789523522725",
      "price": "18.54",
      "compare_at_price": "30.90",
      "barcode": "9789523522725",
      "weight": 302.0,
      "weight_unit": "g"
    }],
    "images": [{
      "src": "https://cdn.shopify.com/...",
      "width": 1095,
      "height": 1600
    }]
  }
}
```

#### B. Collections API ✅ **RECOMMENDED**
- **Endpoint:** `https://kirja.fi/collections/{collection}/products.json`
- **Example:** `https://kirja.fi/collections/all/products.json`
- **Features:**
  - Returns up to 50 products per page
  - Pagination supported
  - Contains full product details
  - Includes multiple products in one request

**Pagination:** Add `?page=2`, `?page=3`, etc.

#### C. Shopify GraphQL API (Advanced)
- **Endpoint:** `https://kirja.fi/api/unstable/graphql.json`
- **Method:** POST
- **Headers Required:**
  - `Content-Type: application/json`
  - `x-shopify-storefront-access-token: 689855d8c96298705f0a694d6416529d`
- **Features:**
  - More flexible queries
  - Can request specific fields only
  - Supports complex filtering
  - Rate limits apply

### 3. **Data Fields Available**

Each book/product contains:

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique product ID | 8643252945229 |
| `title` | Book title | "Prosessi" |
| `body_html` | HTML description | `<p>Pyörremäinen sukellus...</p>` |
| `vendor` | Publisher | "Kosmos" |
| `product_type` | Book format | "Pehmeäkantinen", "Kovakantinen", "Pokkari" |
| `handle` | URL slug | "prosessi-9789523522725" |
| `tags` | Categories & metadata | ["Kaunokirjallisuus", "Klaus Maunuksela", ...] |
| `created_at` | Date added | "2023-08-31T16:17:57+03:00" |
| `updated_at` | Last modified | "2026-01-14T21:38:34+02:00" |
| `published_at` | Publication date | "2023-08-31T03:00:00+03:00" |
| `variants` | Pricing & SKU info | Contains price, ISBN, weight |
| `images` | Cover images | URLs to book covers |
| `options` | Variant options | Usually "Default Title" |

**Variant Fields (Critical):**
- `sku` - ISBN number (9789523522725)
- `price` - Current price in EUR
- `compare_at_price` - Original price (for discounts)
- `weight` - Weight in grams
- `barcode` - Usually same as SKU/ISBN

### 4. **Collections & Categories**

The site is organized into collections accessible via:
`https://kirja.fi/collections/{collection-name}/products.json`

**Main Collections Found:**
- `all` - All products (6,591 items)
- `kaunokirjallisuus` - Fiction
- `tietokirjat` - Non-fiction
- `lasten-ja-nuortenkirjat` - Children's books
- `jannityskirjallisuus` - Thrillers
- `keltainen-kirjasto` - Yellow Library series
- `pokkarit` - Pocket books
- `uutuuskirjat` - New releases

### 5. **Rate Limiting & Best Practices**

Based on network analysis:
- **No API key required** for public JSON endpoints
- **Cloudflare protection** in place (may block aggressive scraping)
- **Recommended approach:**
  - Use 1-2 second delays between requests
  - Use proper User-Agent headers
  - Respect robots.txt
  - Scrape during off-peak hours
  - Cache responses locally

### 6. **Network Observations**

Chrome DevTools revealed:
- 187+ network requests on collection pages
- Third-party services: Klevu (search), Cookiebot, Judge.me (reviews)
- No visible anti-bot measures beyond standard Cloudflare
- Images served via Shopify CDN

## Recommended Data Collection Strategy

### **Option 1: Simple JSON API Scraping (EASIEST)** ⭐

```python
import requests
import time
import json

# Step 1: Get all products from collections API
def fetch_all_products():
    all_products = []
    page = 1
    
    while True:
        url = f"https://kirja.fi/collections/all/products.json?page={page}"
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            break
            
        data = response.json()
        products = data.get('products', [])
        
        if not products:
            break
            
        all_products.extend(products)
        print(f"Fetched page {page}: {len(products)} products")
        
        page += 1
        time.sleep(2)  # Be polite
    
    return all_products

# Step 2: Extract book data
def extract_book_data(product):
    variant = product['variants'][0] if product['variants'] else {}
    
    return {
        'isbn': variant.get('sku', ''),
        'title': product['title'],
        'description': product['body_html'],
        'publisher': product['vendor'],
        'format': product['product_type'],
        'price': variant.get('price', ''),
        'original_price': variant.get('compare_at_price', ''),
        'weight': variant.get('weight', 0),
        'cover_image': product['images'][0]['src'] if product['images'] else '',
        'tags': product['tags'],
        'url': f"https://kirja.fi/products/{product['handle']}",
        'added_date': product['created_at'],
        'updated_date': product['updated_at']
    }

# Usage
products = fetch_all_products()
books = [extract_book_data(p) for p in products]

# Save to JSON
with open('kirja_fi_database.json', 'w', encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=2)
```

### **Option 2: Individual Product Fetching (DETAILED)**

If you need more control or want to fetch specific books:

```python
def fetch_product(handle):
    url = f"https://kirja.fi/products/{handle}.json"
    response = requests.get(url)
    return response.json()['product']
```

### **Option 3: GraphQL API (ADVANCED)**

For complex queries or specific field selection:

```python
def graphql_query():
    url = "https://kirja.fi/api/unstable/graphql.json"
    headers = {
        'Content-Type': 'application/json',
        'x-shopify-storefront-access-token': '689855d8c96298705f0a694d6416529d'
    }
    
    query = """
    query {
        products(first: 50) {
            edges {
                node {
                    title
                    description
                    variants(first: 1) {
                        edges {
                            node {
                                sku
                                price {
                                    amount
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    response = requests.post(url, json={'query': query}, headers=headers)
    return response.json()
```

## Database Schema Recommendations

### SQLite Database Structure

```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    publisher TEXT,
    format TEXT,
    current_price REAL,
    original_price REAL,
    discount_percentage REAL,
    weight_grams INTEGER,
    cover_image_url TEXT,
    product_url TEXT,
    date_added TEXT,
    last_updated TEXT,
    shopify_id INTEGER
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_isbn TEXT,
    tag TEXT,
    FOREIGN KEY (book_isbn) REFERENCES books(isbn)
);

CREATE TABLE authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_isbn TEXT,
    author_name TEXT,
    FOREIGN KEY (book_isbn) REFERENCES books(isbn)
);

-- Indexes for faster searches
CREATE INDEX idx_title ON books(title);
CREATE INDEX idx_isbn ON books(isbn);
CREATE INDEX idx_publisher ON books(publisher);
CREATE INDEX idx_tag ON tags(tag);
CREATE INDEX idx_author ON authors(author_name);
```

## Python Implementation Requirements

### Required Libraries
```bash
pip install requests beautifulsoup4 sqlite3
```

### Complete Implementation Outline

```python
import requests
import sqlite3
import time
from datetime import datetime
import json
import re

class KirjaFiScraper:
    def __init__(self, db_path='kirja_fi.db'):
        self.base_url = 'https://kirja.fi'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.db = sqlite3.connect(db_path)
        self.init_database()
    
    def init_database(self):
        # Create tables as shown above
        pass
    
    def fetch_all_books(self):
        # Implement collection pagination
        pass
    
    def parse_authors_from_tags(self, tags):
        # Extract author names from tags
        # Tags often contain author names
        pass
    
    def save_book(self, book_data):
        # Insert into database
        pass
    
    def update_existing_books(self):
        # Check for price changes, etc.
        pass
```

## Legal & Ethical Considerations

1. **Terms of Service:** Review kirja.fi's Terms of Service before scraping
2. **robots.txt:** Check `https://kirja.fi/robots.txt` for restrictions
3. **Rate Limiting:** Implement delays (1-2 seconds minimum)
4. **User-Agent:** Always identify your bot properly
5. **Data Usage:** Personal use only unless you have permission
6. **Copyright:** Book descriptions and images are copyrighted
7. **Attribution:** If publishing data, attribute to kirja.fi

## Potential Challenges

1. **Pagination Limits:** Collections API may have limits (typically 250 pages × 50 products)
2. **Dynamic Content:** Some content may load via JavaScript
3. **Cloudflare:** May block if requests are too frequent
4. **Data Quality:** Author names need to be extracted from tags
5. **ISBN Extraction:** SKU field contains ISBN but may need validation

## Next Steps

1. **Test API Access:** Verify JSON endpoints still work
2. **Prototype Scraper:** Build small-scale test (100 books)
3. **Database Design:** Finalize schema based on needs
4. **Error Handling:** Handle network errors, missing data
5. **Scheduling:** Set up daily/weekly updates for new books
6. **Search Implementation:** Build search functionality over local DB

## Alternative Approaches

If API access becomes restricted:

1. **HTML Parsing:** Use BeautifulSoup to scrape HTML pages
2. **Selenium/Playwright:** For JavaScript-heavy pages
3. **Archive.org:** Check if site is archived
4. **RSS Feeds:** Look for RSS feeds for new releases
5. **Official API Request:** Contact kirja.fi for official API access

## Estimated Effort

- **Setup:** 2-4 hours
- **Initial Scrape (6,591 books):** 3-4 hours (with delays)
- **Database Design:** 1-2 hours
- **Search Interface:** 4-8 hours
- **Total:** 10-18 hours

## Conclusion

Kirja.fi provides excellent API access through Shopify's JSON endpoints. The **Collections API** approach is recommended for building a comprehensive local database. The data is well-structured, includes ISBNs, pricing, and metadata. With proper rate limiting and error handling, a robust book database can be built efficiently.

---

**Report Prepared By:** AI Assistant  
**Tools Used:** Chrome DevTools, Network Analysis, fetch_webpage  
**Status:** Ready for Implementation ✅
