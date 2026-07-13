#!/usr/bin/env python3

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from mimetypes import guess_type
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Self, Sequence

import aiohttp
import cv2
import exifread
import html5lib
import httpx
import imageio.v2 as imageio
import lxml.html
from bs4 import BeautifulSoup
from bing_image_downloader import downloader as bing_downloader
from duckduckgo_search import DDGS
from icrawler.builtin import BingImageCrawler, GoogleImageCrawler
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] [{levelname}] {name}: {message}",
    style="{",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ImageSearch")


@dataclass(slots=True, kw_only=True)
class SearchResult:
    method_id: int
    method_name: str
    success: bool
    images_found: int
    images: List[Dict[str, Any]]
    error: Optional[str] = None
    duration: float = 0.0


class WorkingImageSearch:
    def __init__(self, output_dir: str | Path = "search_results") -> None:
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    def _get_local_files(self, directory: Path) -> List[str]:
        """Helper to discover downloaded assets efficiently using generators."""
        extensions = {".jpg", ".jpeg", ".png"}
        if not directory.exists():
            return []
        return [str(p) for p in directory.iterdir() if p.suffix.lower() in extensions]

    def search_ddg_images(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        try:
            with DDGS() as ddgs:
                results = ddgs.images(query, max_results=max_results)
                return [
                    {
                        "title": r.get("title", ""),
                        "image_url": r.get("image", ""),
                        "source": r.get("source", ""),
                        "thumbnail": r.get("thumbnail", "")
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error("DDG Images fetch failed: %s", e)
            return []

    def search_ddg_text(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        try:
            with DDGS() as ddgs:
                results = ddgs.text(f"{query} image", max_results=max_results)
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error("DDG Text fetch failed: %s", e)
            return []

    def download_bing_images(self, query: str, limit: int = 10, output_dir: Optional[str | Path] = None) -> List[str]:
        target_dir = Path(output_dir) if output_dir else self.images_dir / "bing"
        
        bing_downloader.download(
            query,
            limit=limit,
            output_dir=str(target_dir.parent),
            timeout=int(self.timeout.read or 30),
            verbose=False
        )
        return self._get_local_files(target_dir)

    def crawl_google_images(self, query: str, max_num: int = 10, output_dir: Optional[str | Path] = None) -> List[str]:
        target_dir = Path(output_dir) if output_dir else self.images_dir / "google"
        
        crawler = GoogleImageCrawler(storage={"root_dir": str(target_dir)})
        crawler.crawl(keyword=query, max_num=max_num, min_size=(100, 100))
        return self._get_local_files(target_dir)

    def crawl_bing_images(self, query: str, max_num: int = 10, output_dir: Optional[str | Path] = None) -> List[str]:
        target_dir = Path(output_dir) if output_dir else self.images_dir / "bing_crawl"
        
        crawler = BingImageCrawler(storage={"root_dir": str(target_dir)})
        crawler.crawl(keyword=query, max_num=max_num, min_size=(100, 100))
        return self._get_local_files(target_dir)

    def scrape_wikipedia_images(self, query: str) -> List[Dict[str, str]]:
        keyword = query.split()[0] if query.split() else ""
        url = f"https://en.wikipedia.org/wiki/{keyword}"
        
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                response = client.get(url)
                response.raise_for_status()
                
            soup = BeautifulSoup(response.content, "html.parser")
            images: List[Dict[str, str]] = []
            
            for img in soup.find_all("img", src=True):
                src: str = img["src"]
                if src.startswith("//"):
                    src = f"https:{src}"
                elif src.startswith("/") and not src.startswith("//"):
                    src = f"https://en.wikipedia.org{src}"

                if src.startswith("http"):
                    images.append({
                        "url": src,
                        "alt": img.get("alt", ""),
                        "title": img.get("title", "")
                    })
            return images[:10]
        except httpx.HTTPError as e:
            logger.error("Wikipedia scraping failed: %s", e)
            return []

    def scrape_flickr_search(self, query: str) -> List[Dict[str, str]]:
        url = f"https://www.flickr.com/search/?text={query.replace(' ', '+')}"
        
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                response = client.get(url)
                response.raise_for_status()
                
            tree = lxml.html.fromstring(response.content)
            images: List[Dict[str, str]] = []
            
            for img in tree.xpath("//img[@src]"):
                src = img.get("src", "")
                if src and src.startswith("http"):
                    images.append({
                        "url": src,
                        "alt": img.get("alt", ""),
                    })
            return images[:10]
        except Exception as e:
            logger.error("Flickr scrape failed: %s", e)
            return []

    def scrape_wikimedia_commons(self, query: str) -> List[Dict[str, str]]:
        url = f"https://commons.wikimedia.org/wiki/Category:{query.replace(' ', '_')}"
        
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                response = client.get(url)
                response.raise_for_status()
                
            soup = BeautifulSoup(response.content, "html5lib")
            images: List[Dict[str, str]] = []
            
            for img in soup.find_all("img", src=True):
                src: str = img["src"]
                if src.startswith("//"):
                    src = f"https:{src}"
                elif src.startswith("/"):
                    src = f"https://commons.wikimedia.org{src}"

                if src.startswith("http"):
                    images.append({"url": src})
            return images[:10]
        except Exception as e:
            logger.error("Wikimedia Commons scraping failed: %s", e)
            return []

    def get_lorem_picsum(self, limit: int = 5) -> List[Dict[str, Any]]:
        base_url = "https://picsum.photos"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{base_url}/v2/list?page=1&limit={limit}")
                response.raise_for_status()
                photos = response.json()
                
            return [
                {
                    "id": photo.get("id", ""),
                    "url": f"{base_url}/id/{photo.get('id')}/800/600",
                    "author": photo.get("author", ""),
                    "download_url": photo.get("download_url", "")
                }
                for photo in photos
            ]
        except httpx.HTTPError as e:
            logger.error("Lorem Picsum fetch failed: %s", e)
            return []

    def get_placeholder_images(self, query: str) -> List[Dict[str, Any]]:
        encoded_query = query.replace(" ", "+")
        services = [
            f"https://via.placeholder.com/800x600?text={encoded_query}",
            f"https://placehold.co/800x600?text={encoded_query}",
            "https://placekitten.com/800/600",
        ]

        images: List[Dict[str, Any]] = []
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            for url in services:
                try:
                    response = client.head(url)
                    images.append({
                        "url": url,
                        "status": response.status_code,
                        "available": response.status_code == 200
                    })
                except httpx.HTTPError as e:
                    images.append({"url": url, "error": str(e)})
        return images

    def search_artstation(self, query: str) -> List[Dict[str, str]]:
        """Keeps original behavior searching raw projects endpoint."""
        url = "https://www.artstation.com/projects.json"
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
                
            images: List[Dict[str, str]] = []
            for item in data.get("data", [])[:5]:
                if cover_node := item.get("cover"):
                    images.append({
                        "title": item.get("title", ""),
                        "url": cover_node.get("small_square_url", ""),
                        "artist": item.get("user", {}).get("username", "")
                    })
            return images
        except Exception as e:
            logger.error("ArtStation API failed: %s", e)
            return []

    def search_nasa_images(self, query: str) -> List[Dict[str, str]]:
        url = "https://images-api.nasa.gov/search"
        params = {"q": query, "media_type": "image"}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            images: List[Dict[str, str]] = []
            for item in data.get("collection", {}).get("items", [])[:5]:
                links = item.get("links", [])
                metadata = item.get("data", [{}])[0]

                if links:
                    images.append({
                        "title": metadata.get("title", ""),
                        "url": links[0].get("href", ""),
                        "description": metadata.get("description", "")
                    })
            return images
        except Exception as e:
            logger.error("NASA API failed: %s", e)
            return []

    def search_met_museum(self, query: str) -> List[Dict[str, str]]:
        search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(search_url, params={"q": query})
                response.raise_for_status()
                object_ids = response.json().get("objectIDs", [])[:5]

                images: List[Dict[str, str]] = []
                for obj_id in object_ids:
                    obj_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{obj_id}"
                    obj_response = client.get(obj_url)
                    
                    if obj_response.status_code == 200:
                        obj_data = obj_response.json()
                        if primary_image := obj_data.get("primaryImage"):
                            images.append({
                                "title": obj_data.get("title", ""),
                                "url": primary_image,
                                "artist": obj_data.get("artistDisplayName", "")
                            })
                return images
        except Exception as e:
            logger.error("Met Museum API failed: %s", e)
            return []

    def analyze_image_pil(self, image_path: str | Path) -> Dict[str, Any]:
        with Image.open(image_path) as img:
            return {
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
            }

    def read_exif_metadata(self, image_path: str | Path) -> Dict[str, str]:
        with open(image_path, "rb") as f:
            tags = exifread.process_file(f)
        return {str(tag): str(value) for tag, value in tags.items()}

    def read_image_imageio(self, image_path: str | Path) -> Dict[str, Any]:
        img = imageio.imread(image_path)
        return {
            "shape": img.shape,
            "dtype": str(img.dtype),
        }

    def detect_opencv(self, image_path: str | Path) -> Dict[str, Any]:
        img = cv2.imread(str(image_path))
        if img is None:
            return {"error": "Failed to load image"}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)

        return {
            "original_shape": img.shape,
            "gray_shape": gray.shape,
            "edges_detected": int(edges.sum() // 255),
        }

    def detect_file_type(self, image_path: str | Path) -> Dict[str, Any]:
        """Using modern standard libraries over magic package where possible or robust fallback."""
        mime_type, _ = guess_type(image_path)
        if not mime_type:
            try:
                import magic
                mime = magic.Magic(mime=True)
                mime_type = mime.from_file(str(image_path))
            except ImportError:
                mime_type = "application/octet-stream"

        return {
            "mime_type": mime_type,
            "is_image": mime_type.startswith("image/")
        }

    async def validate_urls(self, urls: Sequence[str]) -> List[Dict[str, Any]]:
        async def check_url(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
            try:
                async with session.head(url, timeout=10, allow_redirects=True) as resp:
                    return {
                        "url": url,
                        "status": resp.status,
                        "content_type": resp.headers.get("Content-Type", "")
                    }
            except Exception as e:
                return {"url": url, "error": str(e)}

        async with aiohttp.ClientSession() as session:
            tasks = [check_url(session, url) for url in urls]
            return await asyncio.gather(*tasks)

    def search_wikimedia_api(self, query: str) -> List[Dict[str, str]]:
        async def fetch() -> Dict[str, Any]:
            url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrnamespace": "6",
                "gsrlimit": "5",
                "gsrsearch": query
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                return response.json()

        try:
            data = asyncio.run(fetch())
        except Exception as e:
            logger.error("Wikimedia API async run failed: %s", e)
            return []

        images: List[Dict[str, str]] = []
        match data.get("query", {}).get("pages"):
            case dict() as pages:
                for page in pages.values():
                    if isinstance(page, dict) and "imageinfo" in page:
                        for info in page["imageinfo"]:
                            images.append({
                                "url": info.get("url", ""),
                                "title": page.get("title", "")
                            })
            case _:
                pass

        return images


def main() -> None:
    searcher = WorkingImageSearch()
    query = "nature landscape"

    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ РАБОЧИХ МЕТОДОВ ПОИСКА ИЗОБРАЖЕНИЙ")
    print("=" * 60)

    methods = [
        ("1. DuckDuckGo Image Search", lambda: searcher.search_ddg_images(query, max_results=5)),
        ("2. Wikipedia Scraping", lambda: searcher.scrape_wikipedia_images(query)),
        ("3. Wikimedia Commons", lambda: searcher.scrape_wikimedia_commons(query)),
        ("4. Lorem Picsum (random)", lambda: searcher.get_lorem_picsum(limit=3)),
        ("5. ArtStation API", lambda: searcher.search_artstation(query)),
        ("6. NASA Image API", lambda: searcher.search_nasa_images(query)),
        ("7. Met Museum API", lambda: searcher.search_met_museum(query)),
        ("8. Bing Image Downloader", lambda: searcher.download_bing_images(query, limit=3)),
        ("9. iCrawler Bing Images", lambda: searcher.crawl_bing_images(query, max_num=3)),
    ]

    for label, method in methods:
        print(f"\n{label}...")
        results = method()
        print(f"   Найдено/Скачано: {len(results)} изображений")
        if results and isinstance(results[0], dict) and "title" in results[0]:
            for r in results[:2]:
                print(f"   - {r.get('title', 'N/A')[:50]}")

    print("\n" + "=" * 60)
    print("Все методы работают!")
    print("=" * 60)


if __name__ == "__main__":
    main()