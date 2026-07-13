from __future__ import annotations

from typing import Sequence

from .artstation import ArtStationSearch
from .base import BaseImageMethod
from .bing import BingImageDownloader
from .duckduckgo import DuckDuckGoImages, DuckDuckGoText
from .exif import ExifReader
from .flickr import FlickrScraper
from .icrawler_bing import ICrawlerBing
from .icrawler_google import ICrawlerGoogle
from .imageio_ops import ImageIOOperations
from .lorem_picsum import LoremPicsum
from .met_museum import MetMuseumSearch
from .nasa import NASASearch
from .opencv import OpenCVDetection
from .pil_analysis import PILAnalysis
from .placeholder import PlaceholderImages
from .python_magic import PythonMagic
from .url_validator import AIOHTTPUrlValidator
from .wikimedia_api import WikimediaAPI
from .wikimedia_commons import WikimediaCommonsScraper
from .wikipedia import WikipediaScraper

__all__ = [
    "METHODS",
    "BaseImageMethod",
    "ArtStationSearch",
    "BingImageDownloader",
    "DuckDuckGoImages",
    "DuckDuckGoText",
    "ExifReader",
    "FlickrScraper",
    "ICrawlerBing",
    "ICrawlerGoogle",
    "ImageIOOperations",
    "LoremPicsum",
    "MetMuseumSearch",
    "NASASearch",
    "OpenCVDetection",
    "PILAnalysis",
    "PlaceholderImages",
    "PythonMagic",
    "AIOHTTPUrlValidator",
    "WikimediaAPI",
    "WikimediaCommonsScraper",
    "WikipediaScraper",
]

METHODS: Sequence[BaseImageMethod] = (
    DuckDuckGoImages(),
    DuckDuckGoText(),
    BingImageDownloader(),
    ICrawlerGoogle(),
    ICrawlerBing(),
    WikipediaScraper(),
    FlickrScraper(),
    WikimediaCommonsScraper(),
    LoremPicsum(),
    PlaceholderImages(),
    ArtStationSearch(),
    NASASearch(),
    MetMuseumSearch(),
    PILAnalysis(),
    ExifReader(),
    ImageIOOperations(),
    OpenCVDetection(),
    PythonMagic(),
    AIOHTTPUrlValidator(),
    WikimediaAPI(),
)
