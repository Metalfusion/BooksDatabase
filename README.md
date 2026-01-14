# Kirja.fi Books Database Scraper

A robust async Python scraper for collecting book data from kirja.fi.

## Features

- ✅ Async I/O for fast parallel downloads
- ✅ Automatic retry logic with exponential backoff
- ✅ Parallelism control to avoid overwhelming the server
- ✅ Downloads book cover images
- ✅ Saves raw JSON data with organized folder structure
- ✅ Progress tracking with tqdm
- ✅ Comprehensive error handling

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:
```bash
python scraper.py
```

The scraper will:
1. Fetch all books from kirja.fi collections API
2. Download cover images for each book
3. Save everything to the `data/` directory

## Output Structure

```
data/
├── books/
│   ├── prosessi-9789523522725.json
│   ├── hyvat-tyypit-9789510405666.json
│   └── ...
├── images/
│   ├── 9789523522725.jpg
│   ├── 9789510405666.jpg
│   └── ...
└── metadata.json
```

## Configuration

Edit `config.py` to adjust:
- Maximum concurrent requests
- Request delays
- Retry attempts
- Timeout values

## Legal Notice

This scraper is for educational purposes. Please:
- Respect kirja.fi's terms of service
- Use reasonable rate limits
- Do not republish copyrighted content
- Attribute data to kirja.fi
