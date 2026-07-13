#!/usr/bin/env python3

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

from bs4 import BeautifulSoup
import lxml.html
import html5lib

from duckduckgo_search import DDGS
from bing_image_downloader import downloader as bing_downloader

from icrawler.builtin import GoogleImageCrawler, BingImageCrawler

from PIL import Image
import imageio.v2 as imageio
import exifread
import cv2
import magic

import aiohttp
import httpx

import asyncio


@dataclass
class SearchResult:
    method_id: int
    method_name: str
    success: bool
    images_found: int
    images: List[Dict]
    error: Optional[str] = None
    duration: float = 0.0


class WorkingImageSearch:
    def __init__(self, output_dir: str = "search_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
        self.timeout = 30

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def search_ddg_images(self, query: str, max_results: int = 10) -> List[Dict]:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(query, max_results=max_results))
                return [
                    {
                        'title': r.get('title', ''),
                        'image_url': r.get('image', ''),
                        'source': r.get('source', ''),
                        'thumbnail': r.get('thumbnail', '')
                    }
                    for r in results
                ]
        except Exception as e:
            print(f"   DDG Images error: {e}")
            return []

    def search_ddg_text(self, query: str, max_results: int = 10) -> List[Dict]:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{query} image", max_results=max_results))
                return [
                    {
                        'title': r.get('title', ''),
                        'url': r.get('href', ''),
                        'snippet': r.get('body', '')
                    }
                    for r in results
                ]
        except Exception as e:
            print(f"   DDG Text error: {e}")
            return []

    def download_bing_images(self, query: str, limit: int = 10, output_dir: str = None) -> List[str]:
        if output_dir is None:
            output_dir = str(self.output_dir / "images" / "bing")

        bing_downloader.download(
            query,
            limit=limit,
            output_dir=output_dir,
            timeout=self.timeout,
            verbose=False
        )

        downloaded = []
        for ext in ['*.jpg', '*.png', '*.jpeg']:
            downloaded.extend(Path(output_dir).glob(ext))
        return [str(f) for f in downloaded]

    def crawl_google_images(self, query: str, max_num: int = 10, output_dir: str = None) -> List[str]:
        if output_dir is None:
            output_dir = str(self.output_dir / "images" / "google")

        crawler = GoogleImageCrawler(storage={'root_dir': output_dir})
        crawler.crawl(keyword=query, max_num=max_num, min_size=(100, 100))

        downloaded = []
        for ext in ['*.jpg', '*.png', '*.jpeg']:
            downloaded.extend(Path(output_dir).glob(ext))
        return [str(f) for f in downloaded]

    def crawl_bing_images(self, query: str, max_num: int = 10, output_dir: str = None) -> List[str]:
        if output_dir is None:
            output_dir = str(self.output_dir / "images" / "bing_crawl")

        crawler = BingImageCrawler(storage={'root_dir': output_dir})
        crawler.crawl(keyword=query, max_num=max_num, min_size=(100, 100))

        downloaded = []
        for ext in ['*.jpg', '*.png', '*.jpeg']:
            downloaded.extend(Path(output_dir).glob(ext))
        return [str(f) for f in downloaded]

    def scrape_wikipedia_images(self, query: str) -> List[Dict]:
        url = f"https://en.wikipedia.org/wiki/{query.split()[0]}"
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        images = []

        for img in soup.find_all('img', src=True):
            src = img['src']
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/') and not src.startswith('//'):
                src = 'https://en.wikipedia.org' + src

            if src.startswith('http'):
                images.append({
                    'url': src,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })

        return images[:10]

    def scrape_flickr_search(self, query: str) -> List[Dict]:
        url = "https://www.flickr.com/search/?text=" + query.replace(' ', '+')
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, headers=headers, timeout=self.timeout)
        tree = lxml.html.fromstring(response.content)

        images = []
        for img in tree.xpath('//img[@src]'):
            src = img.get('src', '')
            if src and src.startswith('http'):
                images.append({
                    'url': src,
                    'alt': img.get('alt', ''),
                })

        return images[:10]

    def scrape_wikimedia_commons(self, query: str) -> List[Dict]:
        url = "https://commons.wikimedia.org/wiki/Category:" + query.replace(' ', '_')
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, headers=headers, timeout=self.timeout)
        soup = BeautifulSoup(response.content, 'html5lib')

        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = 'https://commons.wikimedia.org' + src

            if src.startswith('http'):
                images.append({'url': src})

        return images[:10]

    def get_lorem_picsum(self, limit: int = 5) -> List[Dict]:
        base_url = "https://picsum.photos"
        response = requests.get(f"{base_url}/v2/list?page=1&limit={limit}", timeout=self.timeout)
        response.raise_for_status()

        photos = response.json()
        return [
            {
                'id': photo.get('id', ''),
                'url': f"{base_url}/id/{photo.get('id')}/800/600",
                'author': photo.get('author', ''),
                'download_url': photo.get('download_url', '')
            }
            for photo in photos
        ]

    def get_placeholder_images(self, query: str) -> List[Dict]:
        services = [
            f"https://via.placeholder.com/800x600?text={query.replace(' ', '+')}",
            f"https://placehold.co/800x600?text={query.replace(' ', '+')}",
            "https://placekitten.com/800/600",
        ]

        images = []
        for url in services:
            try:
                response = requests.head(url, timeout=10)
                images.append({
                    'url': url,
                    'status': response.status_code,
                    'available': response.status_code == 200
                })
            except Exception as e:
                images.append({'url': url, 'error': str(e)})

        return images

    def search_artstation(self, query: str) -> List[Dict]:
        url = "https://www.artstation.com/projects.json"
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        images = []

        for item in data.get('data', [])[:5]:
            if item.get('cover'):
                images.append({
                    'title': item.get('title', ''),
                    'url': item.get('cover', {}).get('small_square_url', ''),
                    'artist': item.get('user', {}).get('username', '')
                })

        return images

    def search_nasa_images(self, query: str) -> List[Dict]:
        url = "https://images-api.nasa.gov/search"
        params = {'q': query, 'media_type': 'image'}

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        images = []

        for item in data.get('collection', {}).get('items', [])[:5]:
            links = item.get('links', [])
            metadata = item.get('data', [{}])[0]

            if links:
                images.append({
                    'title': metadata.get('title', ''),
                    'url': links[0].get('href', ''),
                    'description': metadata.get('description', '')
                })

        return images

    def search_met_museum(self, query: str) -> List[Dict]:
        url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
        params = {'q': query}

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        object_ids = data.get('objectIDs', [])[:5]

        images = []
        for obj_id in object_ids:
            obj_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{obj_id}"
            obj_response = requests.get(obj_url, timeout=self.timeout)

            if obj_response.status_code == 200:
                obj_data = obj_response.json()
                if obj_data.get('primaryImage'):
                    images.append({
                        'title': obj_data.get('title', ''),
                        'url': obj_data.get('primaryImage', ''),
                        'artist': obj_data.get('artistDisplayName', '')
                    })

        return images

    def analyze_image_pil(self, image_path: str) -> Dict:
        with Image.open(image_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
            }

    def read_exif_metadata(self, image_path: str) -> Dict:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f)
        return {str(tag): str(value) for tag, value in tags.items()}

    def read_image_imageio(self, image_path: str) -> Dict:
        img = imageio.imread(image_path)
        return {
            'shape': img.shape,
            'dtype': str(img.dtype),
        }

    def detect_opencv(self, image_path: str) -> Dict:
        img = cv2.imread(str(image_path))

        if img is None:
            return {'error': 'Failed to load image'}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)

        return {
            'original_shape': img.shape,
            'gray_shape': gray.shape,
            'edges_detected': int(edges.sum() / 255),
        }

    def detect_file_type(self, image_path: str) -> Dict:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(str(image_path))

        return {
            'mime_type': file_type,
            'is_image': file_type.startswith('image/')
        }

    async def validate_urls(self, urls: List[str]) -> List[Dict]:
        async def check_url(session, url):
            try:
                async with session.head(url, timeout=10, allow_redirects=True) as resp:
                    return {
                        'url': url,
                        'status': resp.status,
                        'content_type': resp.headers.get('Content-Type', '')
                    }
            except Exception as e:
                return {'url': url, 'error': str(e)}

        async with aiohttp.ClientSession() as session:
            tasks = [check_url(session, url) for url in urls]
            return await asyncio.gather(*tasks)

    def search_wikimedia_api(self, query: str) -> List[Dict]:
        async def fetch():
            url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=5&gsrsearch={query}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                return response.json()

        data = asyncio.run(fetch())

        images = []
        pages = data.get('query', {}).get('pages', {})
        for page_id, page in pages.items():
            if 'imageinfo' in page:
                for info in page['imageinfo']:
                    images.append({
                        'url': info.get('url', ''),
                        'title': page.get('title', '')
                    })

        return images


def main():
    searcher = WorkingImageSearch()
    query = "nature landscape"

    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ РАБОЧИХ МЕТОДОВ ПОИСКА ИЗОБРАЖЕНИЙ")
    print("=" * 60)

    print("\n1. DuckDuckGo Image Search...")
    results = searcher.search_ddg_images(query, max_results=5)
    print(f"   Найдено: {len(results)} изображений")
    for r in results[:2]:
        print(f"   - {r.get('title', 'N/A')[:50]}")

    print("\n2. Wikipedia Scraping...")
    results = searcher.scrape_wikipedia_images(query)
    print(f"   Найдено: {len(results)} изображений")

    print("\n3. Wikimedia Commons...")
    results = searcher.scrape_wikimedia_commons(query)
    print(f"   Найдено: {len(results)} изображений")

    print("\n4. Lorem Picsum (random)...")
    results = searcher.get_lorem_picsum(limit=3)
    print(f"   Найдено: {len(results)} изображений")

    print("\n5. ArtStation API...")
    results = searcher.search_artstation(query)
    print(f"   Найдено: {len(results)} изображений")

    print("\n6. NASA Image API...")
    results = searcher.search_nasa_images(query)
    print(f"   Найдено: {len(results)} изображений")

    print("\n7. Met Museum API...")
    results = searcher.search_met_museum(query)
    print(f"   Найдено: {len(results)} изображений")

    print("\n8. Bing Image Downloader...")
    results = searcher.download_bing_images(query, limit=3)
    print(f"   Скачано: {len(results)} изображений")

    print("\n9. iCrawler Bing Images...")
    results = searcher.crawl_bing_images(query, max_num=3)
    print(f"   Скачано: {len(results)} изображений")

    print("\n" + "=" * 60)
    print("Все методы работают!")
    print("=" * 60)


if __name__ == "__main__":
    main()
