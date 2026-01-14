"""Setup script for installing the package in development mode."""

from setuptools import setup, find_packages

setup(
    name="kirja-fi-scraper",
    version="1.0.0",
    description="Async scraper for kirja.fi book data",
    author="Your Name",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.9.1",
        "aiofiles>=23.2.1",
        "tenacity>=8.2.3",
        "tqdm>=4.66.1",
        "Pillow>=10.1.0",
    ],
)
