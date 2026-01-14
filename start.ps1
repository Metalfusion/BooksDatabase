# Quick start script for PowerShell

Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kirja.fi Scraper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Yellow
Write-Host "  1. Run full scraper: python scraper.py" -ForegroundColor White
Write-Host "  2. Test scraper: python test_scraper.py" -ForegroundColor White
Write-Host "  3. View data: python utils.py" -ForegroundColor White
Write-Host "  4. Search books: python utils.py 'search term'" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
