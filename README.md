# Kirja.fi book database scraper

Async Python scraper for collecting book metadata from kirja.fi and storing it locally as JSON, with optional cover image downloads and optional metadata extraction from product pages.

For searching and reporting on downloaded data, see [search-tools/README.md](search-tools/README.md).

## Requirements

- Python 3.8+
- pip

## Installation

Create and activate a virtual environment:

```bash
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# Linux/macOS
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional convenience scripts:

- `start.ps1` activates `venv` and prints common commands (PowerShell)
- `start.bat` activates `venv` and opens an interactive CMD session

## Usage

Run the scraper:

```bash
python scraper.py
```

The scraper writes:

- `data/books/` one JSON file per book
- `data/images/` cover images (if enabled)
- `data/metadata.json` summary metadata
- `scraper.log` log output

Basic local text search:

```bash
python utils.py "search term"
```

## Output layout

```
data/
	books/          # one JSON file per book
	images/         # cover images (when enabled)
	metadata.json   # scraping summary
```

## Configuration

Adjust settings in `config.py`:

- `MAX_CONCURRENT_REQUESTS` / `SEMAPHORE_LIMIT`: concurrency
- `REQUEST_DELAY`: delay between collection page requests
- `HTML_REQUEST_DELAY`: delay between HTML page requests
- `MAX_RETRIES`, `REQUEST_TIMEOUT`: reliability/timeouts
- `DOWNLOAD_IMAGES`: enable/disable cover downloads
- `FETCH_HTML_METADATA`: enable/disable extra metadata extraction from product pages

## Documentation

- Search tooling: [search-tools/README.md](search-tools/README.md)
- Background notes and API investigation: [kirja_fi_investigation_report.md](kirja_fi_investigation_report.md)

## Legal notice

Use responsibly:

- Follow kirja.fi terms of service and robots guidelines
- Use reasonable rate limits
- Do not republish copyrighted content
