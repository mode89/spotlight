"""
Windows 10 Spotlight wallpaper website scraper library.

Provides functions to fetch and parse wallpaper metadata from
windows10spotlight.com
"""

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://windows10spotlight.com"

# HTTP headers to avoid being blocked
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def get_total_pages():
    """
    Get the total number of pages available on the website.

    Returns:
        int: The total number of pages.
    """
    response = requests.get(BASE_URL, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all pagination links
    pagination_nav = soup.select("nav.navigation.pagination a.page-numbers")

    # Extract numeric values from pagination links
    page_numbers = []
    for link in pagination_nav:
        text = link.get_text(strip=True)
        # Remove commas from formatted numbers (e.g., "1,263" -> "1263")
        text_cleaned = text.replace(",", "")
        if text_cleaned.isdigit():
            page_numbers.append(int(text_cleaned))

    # Return the maximum page number
    return max(page_numbers) if page_numbers else 1


def get_page(n):
    """
    Get information available on page n.

    Args:
        n (int): Page number to fetch.

    Returns:
        list: List of dicts, each containing:
            - id: Image ID
            - detail_url: URL to image detail page
            - thumbnail_url: URL to thumbnail image
            - thumbnail_hash: MD5 hash identifier
    """
    # Page 1 is the base URL, other pages use /page/{n}
    if n == 1:
        url = BASE_URL
    else:
        url = f"{BASE_URL}/page/{n}"

    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all article elements
    articles = soup.select("article")

    images = []
    for article in articles:
        # Extract image ID from article class (pattern: post-{id})
        image_id = None
        classes = article.get("class", [])
        for cls in classes:
            if cls.startswith("post-"):
                try:
                    image_id = int(cls.split("-")[1])
                    break
                except (IndexError, ValueError):
                    continue

        if image_id is None:
            continue

        # Extract detail page URL
        detail_link = article.select_one("a[href*='/images/']")
        detail_url = detail_link.get("href") if detail_link else None

        # Extract thumbnail URL and alt text (MD5 hash)
        img = article.select_one("img")
        thumbnail_url = img.get("src") if img else None
        thumbnail_hash = img.get("alt") if img else None

        images.append({
            "id": image_id,
            "detail_url": detail_url,
            "thumbnail_url": thumbnail_url,
            "thumbnail_hash": thumbnail_hash
        })

    return images


def get_image_info(image_id):
    """
    Get detailed information about an image.

    Args:
        image_id (int): The image ID.

    Returns:
        dict: Detailed image information containing:
            - id: Image ID
            - title: Descriptive title with location
            - full_resolution_url: URL to full resolution image
            - tags: List of descriptive keywords
            - date: Publication date text
            - datetime: Structured timestamp
            - og_metadata: Open Graph metadata dict
            - all_images: List of all image URLs found
              (landscape/portrait variants)
    """
    url = f"{BASE_URL}/images/{image_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract post ID from article class
    article = soup.select_one("article")
    post_id = None
    if article:
        classes = article.get("class", [])
        for cls in classes:
            if cls.startswith("post-"):
                try:
                    post_id = int(cls.split("-")[1])
                    break
                except (IndexError, ValueError):
                    continue

    # Extract title from h1 or h2
    title_elem = soup.select_one("h1") or soup.select_one("h2")
    title = title_elem.get_text(strip=True) if title_elem else None

    # Extract tags
    tag_elements = soup.select("[rel='tag']")
    tags = [tag.get_text(strip=True) for tag in tag_elements]

    # Extract date
    time_elem = soup.select_one("time")
    if time_elem:
        date = time_elem.get_text(strip=True)
        datetime_attr = time_elem.get("datetime")
    else:
        # Fallback to span.date if time element not found
        date_elem = soup.select_one("span.date")
        date = date_elem.get_text(strip=True) if date_elem else None
        datetime_attr = date_elem.get("datetime") if date_elem else None

    # Extract Open Graph metadata
    og_metadata = {}
    og_meta_tags = soup.select("meta[property^='og:']")
    for meta in og_meta_tags:
        property_name = meta.get("property")
        content = meta.get("content")
        if property_name and content:
            og_metadata[property_name] = content

    # Extract all images with wp-content/uploads in src
    all_images = []
    img_elements = soup.select("img[src*='wp-content/uploads']")

    for img in img_elements:
        # Parse srcset to find highest resolution
        srcset = img.get("srcset", "")
        if srcset:
            # Parse srcset entries: "url width, url width, ..."
            entries = []
            for entry in srcset.split(","):
                entry = entry.strip()
                if not entry:
                    continue
                # Split from right to separate URL and width
                parts = entry.rsplit(None, 1)
                if len(parts) == 2:
                    img_url, width_str = parts
                    # Extract numeric width (e.g., "1920w" -> 1920)
                    try:
                        width = int(width_str.rstrip("w"))
                        entries.append((img_url, width))
                    except ValueError:
                        continue

            # Find entry with highest width
            if entries:
                highest_res = max(entries, key=lambda x: x[1])
                all_images.append({
                    "url": highest_res[0],
                    "width": highest_res[1],
                    "alt": img.get("alt", "")
                })
        else:
            # No srcset, just use src
            src = img.get("src")
            if src:
                all_images.append({
                    "url": src,
                    "width": None,
                    "alt": img.get("alt", "")
                })

    # Get the first (main) full resolution image URL
    full_resolution_url = all_images[0]["url"] if all_images else None

    return {
        "id": post_id or image_id,
        "title": title,
        "full_resolution_url": full_resolution_url,
        "tags": tags,
        "date": date,
        "datetime": datetime_attr,
        "og_metadata": og_metadata,
        "all_images": all_images
    }
