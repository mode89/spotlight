# Overview

Windows 10 Spotlight website hosts wallpaper images with metadata. Server-side pagination, no JavaScript required. Image IDs are sequential and descending (newest first).

**URL Patterns:**
- Main/listing pages: `https://windows10spotlight.com` and `https://windows10spotlight.com/page/{N}`
- Image detail pages: `https://windows10spotlight.com/images/{id}`

# Listing Pages

`https://windows10spotlight.com/page/{N}` (page 1 is just the base URL)

Lists multiple images (typically 5 per page) with basic metadata. Detailed information requires visiting individual image pages.

## Total Page Count

**Selector:** `nav.navigation.pagination a.page-numbers`

Parse all pagination links, extract numeric values from text, find maximum. This is the total page count. Ignore non-numeric text like "Next »" or "Previous".

**HTML pattern:**
```html
<nav class="navigation pagination">
  <a class="page-numbers" href="...">2</a>
  <a class="page-numbers" href="...">3</a>
  <a class="page-numbers" href="...">MAX_PAGE</a>
</nav>
```

## Image List

**Selector:** `article` elements

Each article represents one image entry.

**HTML pattern:**
```html
<article class="post-{id} ...">
  <a href="https://windows10spotlight.com/images/{id}">
    <img src="https://windows10spotlight.com/wp-content/uploads/..." alt="{hash}">
  </a>
</article>
```

## Image ID / Post ID

**Selector:** `article` element's `class` attribute

Extract from class name matching pattern `post-{id}`. The ID is numeric.

## Detail Page URL

**Selector:** `article a[href*="/images/"]`

Link href contains `/images/{id}` pointing to full detail page.

## Thumbnail URL

**Selector:** `article img`

The `src` attribute contains thumbnail image URL (typically 1024×576 resolution).

## Thumbnail Alt Text

**Selector:** `article img`

The `alt` attribute contains MD5 hash identifier.

# Image Detail Pages

`https://windows10spotlight.com/images/{id}`

Contains full metadata including title, tags, and full resolution image URLs.

## Post ID

**Selector:** `article` element's `class` attribute

Extract from class name matching pattern `post-{id}`.

## Title

**Selector:** `h1` or `h2` element

Contains full descriptive title with location information.

Example: "Aerial view of the twin-tower rocks at Timmappana Betta, Bangalore, Karnataka, India"

## Full Resolution Image URL

**Selector:** First `img` in content area with 'wp-content/uploads' in `src` attribute

**Method 1 (recommended):** Parse the `srcset` attribute. It contains comma-separated entries with format `{url} {width}`. Find the entry with the highest width value (e.g., `1920w` for landscape, `1080w` for portrait).

**Method 2:** Take any image URL and remove the dimension suffix. Pattern: `https://windows10spotlight.com/wp-content/uploads/{YYYY}/{MM}/{hash}-{WxH}.jpg` becomes `https://windows10spotlight.com/wp-content/uploads/{YYYY}/{MM}/{hash}.jpg`

**URL Structure:**
- Path: `wp-content/uploads/{YYYY}/{MM}/{hash}.jpg`
- Hash: 32-character MD5 hex string
- Full resolution URL has no dimension suffix

**Srcset example:**
```html
<img src=".../{hash}-1024x576.jpg"
     srcset=".../{hash}-300x169.jpg 300w,
             .../{hash}-1024x576.jpg 1024w,
             .../{hash}.jpg 1920w">
```

## Tags

**Selector:** Elements with attribute `rel="tag"`

Multiple descriptive keywords for the image. Extract text content from each element.

Examples: "aerial view", "clouds", "forest", "landscape", "nature"

## Date

**Selector:** `time` element

Text content contains publication date. The `datetime` attribute contains structured timestamp.

## Open Graph Metadata

**Selector:** `meta` elements with `property` starting with "og:"

Available fields:
- `og:title` - Full title with site suffix
- `og:description` - Title with MD5 hashes
- `og:image` - Image URL
- `og:url` - Canonical URL
- `og:type` - Always "article"
- `og:site_name` - "Windows 10 Spotlight Images"

Extract from `property` attribute (key) and `content` attribute (value).

## Image Alt Text

**Selector:** Same `img` element used for full resolution URL

The `alt` attribute contains the same text as the title.

# Notes

- Some detail pages contain multiple images (landscape and portrait variants)
- No rate limiting observed but implement delays as courtesy
- BeautifulSoup is sufficient for parsing (no Playwright needed)
