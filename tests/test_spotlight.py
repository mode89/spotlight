"""Tests for spotlight.py module."""

import pytest
from unittest.mock import Mock, patch
import requests
import spotlight
from spotlight import get_total_pages, get_page, get_image_info


@patch("spotlight.requests.get")
def test_get_total_pages_success(mock_get):
    """Test successful parsing of pagination with multiple pages."""
    # Mock HTML response with pagination
    html_content = """
    <html>
        <nav class="navigation pagination">
            <a class="page-numbers" href="/page/1">1</a>
            <a class="page-numbers" href="/page/2">2</a>
            <a class="page-numbers" href="/page/3">3</a>
            <a class="page-numbers" href="/page/50">50</a>
        </nav>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_total_pages()

    assert result == 50
    mock_get.assert_called_once()


@patch("spotlight.requests.get")
def test_get_total_pages_with_commas(mock_get):
    """Test parsing of page numbers with comma formatting."""
    # Mock HTML with comma-formatted numbers
    html_content = """
    <html>
        <nav class="navigation pagination">
            <a class="page-numbers" href="/page/1">1</a>
            <a class="page-numbers" href="/page/100">100</a>
            <a class="page-numbers" href="/page/1263">1,263</a>
        </nav>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_total_pages()

    assert result == 1263
    mock_get.assert_called_once()


@patch("spotlight.requests.get")
def test_get_total_pages_no_pagination(mock_get):
    """Test when no pagination links are found (returns 1)."""
    # Mock HTML without pagination
    html_content = """
    <html>
        <div>No pagination here</div>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_total_pages()

    assert result == 1
    mock_get.assert_called_once()


@patch("spotlight.requests.get")
def test_get_total_pages_non_numeric_links(mock_get):
    """Test pagination with non-numeric links like 'Next', 'Prev'."""
    # Mock HTML with mixed numeric and non-numeric pagination
    html_content = """
    <html>
        <nav class="navigation pagination">
            <a class="page-numbers" href="/page/1">Previous</a>
            <a class="page-numbers" href="/page/1">1</a>
            <a class="page-numbers" href="/page/2">2</a>
            <a class="page-numbers" href="/page/3">3</a>
            <a class="page-numbers" href="/page/25">25</a>
            <a class="page-numbers" href="/page/26">Next</a>
        </nav>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_total_pages()

    assert result == 25
    mock_get.assert_called_once()


@patch("spotlight.requests.get")
def test_get_total_pages_single_page(mock_get):
    """Test when only page 1 exists."""
    # Mock HTML with only page 1
    html_content = """
    <html>
        <nav class="navigation pagination">
            <a class="page-numbers current" href="/">1</a>
        </nav>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_total_pages()

    assert result == 1
    mock_get.assert_called_once()


@patch("spotlight.requests.get")
def test_get_total_pages_http_error(mock_get):
    """Test that HTTP errors are raised."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("HTTP Error")
    mock_get.return_value = mock_response

    with pytest.raises(Exception, match="HTTP Error"):
        get_total_pages()

    mock_get.assert_called_once()


@patch("spotlight.requests.get")
def test_get_total_pages_empty_nav(mock_get):
    """Test when pagination nav exists but is empty."""
    # Mock HTML with empty pagination nav
    html_content = """
    <html>
        <nav class="navigation pagination">
        </nav>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_total_pages()

    assert result == 1
    mock_get.assert_called_once()


@patch("spotlight.requests.get")
def test_get_total_pages_uses_correct_headers(mock_get):
    """Test that function uses correct headers."""
    html_content = """
    <html>
        <nav class="navigation pagination">
            <a class="page-numbers" href="/page/1">1</a>
        </nav>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    get_total_pages()

    # Verify the call was made with headers
    call_args = mock_get.call_args
    assert "headers" in call_args.kwargs
    assert "User-Agent" in call_args.kwargs["headers"]


@patch("spotlight.requests.get")
def test_get_page_page_1_success(mock_get):
    """Test successful fetching of page 1 (uses base URL)."""
    html_content = """
    <html>
        <article class="post-1234 type-post">
            <a href="https://windows10spotlight.com/images/1234/">
                <img src="https://windows10spotlight.com/thumb1.jpg"
                     alt="abc123def456">
            </a>
        </article>
        <article class="post-5678 type-post">
            <a href="https://windows10spotlight.com/images/5678/">
                <img src="https://windows10spotlight.com/thumb2.jpg"
                     alt="def789ghi012">
            </a>
        </article>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_page(1)

    assert len(result) == 2
    assert result[0]["id"] == 1234
    assert result[0]["detail_url"] == (
        "https://windows10spotlight.com/images/1234/"
    )
    assert result[0]["thumbnail_url"] == (
        "https://windows10spotlight.com/thumb1.jpg"
    )
    assert result[0]["thumbnail_hash"] == "abc123def456"

    # Verify BASE_URL was used (not BASE_URL/page/1)
    mock_get.assert_called_once_with(
        "https://windows10spotlight.com",
        headers=spotlight.HEADERS
    )


@patch("spotlight.requests.get")
def test_get_page_page_greater_than_1_success(mock_get):
    """Test successful fetching of page > 1 (uses /page/{n} URL)."""
    html_content = """
    <html>
        <article class="post-9999 type-post">
            <a href="https://windows10spotlight.com/images/9999/">
                <img src="https://windows10spotlight.com/thumb999.jpg"
                     alt="hash999">
            </a>
        </article>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_page(5)

    assert len(result) == 1
    assert result[0]["id"] == 9999
    assert result[0]["detail_url"] == (
        "https://windows10spotlight.com/images/9999/"
    )
    assert result[0]["thumbnail_url"] == (
        "https://windows10spotlight.com/thumb999.jpg"
    )
    assert result[0]["thumbnail_hash"] == "hash999"

    # Verify /page/5 URL was used
    mock_get.assert_called_once_with(
        "https://windows10spotlight.com/page/5",
        headers=spotlight.HEADERS
    )


@patch("spotlight.requests.get")
def test_get_page_multiple_articles(mock_get):
    """Test parsing multiple articles on one page."""
    html_content = """
    <html>
        <article class="post-100 type-post">
            <a href="/images/100/">
                <img src="https://example.com/thumb100.jpg" alt="hash100">
            </a>
        </article>
        <article class="post-200 type-post">
            <a href="/images/200/">
                <img src="https://example.com/thumb200.jpg" alt="hash200">
            </a>
        </article>
        <article class="post-300 type-post">
            <a href="/images/300/">
                <img src="https://example.com/thumb300.jpg" alt="hash300">
            </a>
        </article>
        <article class="post-400 type-post">
            <a href="/images/400/">
                <img src="https://example.com/thumb400.jpg" alt="hash400">
            </a>
        </article>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_page(1)

    assert len(result) == 4
    assert result[0]["id"] == 100
    assert result[1]["id"] == 200
    assert result[2]["id"] == 300
    assert result[3]["id"] == 400


@patch("spotlight.requests.get")
def test_get_page_article_without_image_id(mock_get):
    """Test that articles without post- class are skipped."""
    html_content = """
    <html>
        <article class="post-111 type-post">
            <a href="/images/111/">
                <img src="https://example.com/thumb111.jpg" alt="hash111">
            </a>
        </article>
        <article class="some-other-class">
            <a href="/images/invalid/">
                <img src="https://example.com/thumb_invalid.jpg" alt="hash_invalid">
            </a>
        </article>
        <article class="post-222 type-post">
            <a href="/images/222/">
                <img src="https://example.com/thumb222.jpg" alt="hash222">
            </a>
        </article>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_page(1)

    # Only two articles should be parsed (invalid one skipped)
    assert len(result) == 2
    assert result[0]["id"] == 111
    assert result[1]["id"] == 222


@patch("spotlight.requests.get")
def test_get_page_article_with_missing_elements(mock_get):
    """Test handling of missing optional fields."""
    html_content = """
    <html>
        <article class="post-333 type-post">
            <!-- Missing detail link -->
            <img src="https://example.com/thumb333.jpg" alt="hash333">
        </article>
        <article class="post-444 type-post">
            <a href="/images/444/">
                <!-- Missing img element -->
            </a>
        </article>
        <article class="post-555 type-post">
            <!-- Article with all fields present -->
            <a href="/images/555/">
                <img src="https://example.com/thumb555.jpg" alt="hash555">
            </a>
        </article>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_page(1)

    assert len(result) == 3
    # Article 333: missing detail_url
    assert result[0]["id"] == 333
    assert result[0]["detail_url"] is None
    assert result[0]["thumbnail_url"] == "https://example.com/thumb333.jpg"
    assert result[0]["thumbnail_hash"] == "hash333"
    # Article 444: missing img element
    assert result[1]["id"] == 444
    assert result[1]["detail_url"] == "/images/444/"
    assert result[1]["thumbnail_url"] is None
    assert result[1]["thumbnail_hash"] is None
    # Article 555: all fields present
    assert result[2]["id"] == 555
    assert result[2]["detail_url"] == "/images/555/"
    assert result[2]["thumbnail_url"] == "https://example.com/thumb555.jpg"
    assert result[2]["thumbnail_hash"] == "hash555"


@patch("spotlight.requests.get")
def test_get_page_http_error(mock_get):
    """Test that HTTP errors are raised."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("HTTP Error")
    mock_get.return_value = mock_response

    with pytest.raises(Exception, match="HTTP Error"):
        get_page(1)

    mock_get.assert_called_once()


@patch("spotlight.requests.get")
def test_get_page_uses_correct_headers(mock_get):
    """Test that function uses correct headers."""
    html_content = """
    <html>
        <article class="post-777 type-post">
            <a href="/images/777/">
                <img src="https://example.com/thumb777.jpg" alt="hash777">
            </a>
        </article>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    get_page(3)

    # Verify the call was made with headers
    call_args = mock_get.call_args
    assert "headers" in call_args.kwargs
    assert "User-Agent" in call_args.kwargs["headers"]


@patch("spotlight.requests.get")
def test_get_page_empty_page(mock_get):
    """Test when no articles are on the page."""
    html_content = """
    <html>
        <div>No articles here</div>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_page(1)

    assert result == []
    mock_get.assert_called_once()


@patch("spotlight.requests.get")
def test_get_image_info_complete_valid_html(mock_get):
    """Test successful extraction of all fields from well-formed page."""
    html_content = """
    <html>
    <head>
        <meta property="og:title" content="Sunset over Mountains">
        <meta property="og:image" content="https://windows10spotlight.com/og.jpg">
        <meta property="og:description" content="Beautiful sunset">
    </head>
    <body>
        <article class="post-12345 type-post status-publish">
            <h1>Sunset over Mountains at Dusk</h1>
            <time datetime="2024-01-15T10:30:00Z">January 15, 2024</time>
            <a href="/tag/sunset" rel="tag">sunset</a>
            <a href="/tag/mountains" rel="tag">mountains</a>
            <img src="https://windows10spotlight.com/wp-content/uploads/sunset.jpg"
                 srcset="https://windows10spotlight.com/wp-content/uploads/sunset-1920x1080.jpg 1920w,
                         https://windows10spotlight.com/wp-content/uploads/sunset-1280x720.jpg 1280w"
                 alt="sunset-over-mountains">
        </article>
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_image_info(12345)

    assert result["id"] == 12345
    assert result["title"] == "Sunset over Mountains at Dusk"
    assert result["full_resolution_url"] == (
        "https://windows10spotlight.com/wp-content/uploads/sunset-1920x1080.jpg"
    )
    assert result["tags"] == ["sunset", "mountains"]
    assert result["date"] == "January 15, 2024"
    assert result["datetime"] == "2024-01-15T10:30:00Z"
    assert result["og_metadata"]["og:title"] == "Sunset over Mountains"
    assert result["og_metadata"]["og:image"] == (
        "https://windows10spotlight.com/og.jpg"
    )
    assert result["og_metadata"]["og:description"] == "Beautiful sunset"
    assert len(result["all_images"]) == 1
    assert result["all_images"][0]["width"] == 1920
    mock_get.assert_called_once_with(
        "https://windows10spotlight.com/images/12345",
        headers=spotlight.HEADERS
    )


@patch("spotlight.requests.get")
def test_get_image_info_multiple_images_with_srcset(mock_get):
    """Test multiple images with landscape and portrait variants."""
    html_content = """
    <html>
    <body>
        <article class="post-999 type-post">
            <h1>Nature Photography</h1>
            <time datetime="2024-02-20T14:00:00Z">February 20, 2024</time>
            <img src="https://windows10spotlight.com/wp-content/uploads/landscape.jpg"
                 srcset="https://windows10spotlight.com/wp-content/uploads/landscape-2560x1440.jpg 2560w,
                         https://windows10spotlight.com/wp-content/uploads/landscape-1920x1080.jpg 1920w"
                 alt="landscape-view">
            <img src="https://windows10spotlight.com/wp-content/uploads/portrait.jpg"
                 srcset="https://windows10spotlight.com/wp-content/uploads/portrait-1080x1920.jpg 1920w,
                         https://windows10spotlight.com/wp-content/uploads/portrait-720x1280.jpg 1280w"
                 alt="portrait-view">
        </article>
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_image_info(999)

    assert len(result["all_images"]) == 2
    assert result["all_images"][0]["url"] == (
        "https://windows10spotlight.com/wp-content/uploads/landscape-2560x1440.jpg"
    )
    assert result["all_images"][0]["width"] == 2560
    assert result["all_images"][0]["alt"] == "landscape-view"
    assert result["all_images"][1]["url"] == (
        "https://windows10spotlight.com/wp-content/uploads/portrait-1080x1920.jpg"
    )
    assert result["all_images"][1]["width"] == 1920
    assert result["all_images"][1]["alt"] == "portrait-view"
    assert result["full_resolution_url"] == result["all_images"][0]["url"]


@patch("spotlight.requests.get")
def test_get_image_info_fallbacks(mock_get):
    """Test fallback to h2 title and image without srcset."""
    html_content = """
    <html>
    <body>
        <article class="post-777 type-post">
            <h2>Fallback Title</h2>
            <span class="date" datetime="2024-03-10T09:00:00Z">
                March 10, 2024
            </span>
            <img src="https://windows10spotlight.com/wp-content/uploads/nosrcset.jpg"
                 alt="no-srcset-image">
        </article>
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_image_info(777)

    assert result["title"] == "Fallback Title"
    assert result["date"] == "March 10, 2024"
    assert result["datetime"] == "2024-03-10T09:00:00Z"
    assert len(result["all_images"]) == 1
    assert result["all_images"][0]["url"] == (
        "https://windows10spotlight.com/wp-content/uploads/nosrcset.jpg"
    )
    assert result["all_images"][0]["width"] is None
    assert result["full_resolution_url"] == (
        "https://windows10spotlight.com/wp-content/uploads/nosrcset.jpg"
    )


@patch("spotlight.requests.get")
def test_get_image_info_missing_fields(mock_get):
    """Test missing article, title, tags, and date all return None/empty."""
    html_content = """
    <html>
    <body>
        <div>No article element here</div>
        <h2>Orphaned Title</h2>
        <p>Some content without tags or dates</p>
        <img src="https://windows10spotlight.com/wp-content/uploads/test.jpg"
             alt="test">
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_image_info(9999)

    # Falls back to passed image_id when no article/post-id found
    assert result["id"] == 9999
    # h2 should be found as fallback title
    assert result["title"] == "Orphaned Title"
    assert result["tags"] == []
    assert result["date"] is None
    assert result["datetime"] is None
    assert result["og_metadata"] == {}


@patch("spotlight.requests.get")
def test_get_image_info_srcset_edge_cases(mock_get):
    """Test empty srcset, malformed entries, and whitespace handling."""
    html_content = """
    <html>
    <body>
        <article class="post-500 type-post">
            <h1>Srcset Edge Cases</h1>
            <img src="https://windows10spotlight.com/wp-content/uploads/empty.jpg"
                 srcset=""
                 alt="empty-srcset">
            <img src="https://windows10spotlight.com/wp-content/uploads/malformed.jpg"
                 srcset="https://windows10spotlight.com/wp-content/uploads/malformed.jpg invalidw,
                         https://windows10spotlight.com/wp-content/uploads/valid.jpg 1920w"
                 alt="malformed-srcset">
            <img src="https://windows10spotlight.com/wp-content/uploads/whitespace.jpg"
                 srcset="  https://windows10spotlight.com/wp-content/uploads/whitespace-1280x720.jpg   1280w  ,
                         https://windows10spotlight.com/wp-content/uploads/whitespace-1920x1080.jpg 1920w  "
                 alt="whitespace-srcset">
        </article>
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_image_info(500)

    # Empty srcset should fall back to src
    assert result["all_images"][0]["url"] == (
        "https://windows10spotlight.com/wp-content/uploads/empty.jpg"
    )
    assert result["all_images"][0]["width"] is None

    # Malformed entry should be skipped, only valid entry parsed
    assert result["all_images"][1]["url"] == (
        "https://windows10spotlight.com/wp-content/uploads/valid.jpg"
    )
    assert result["all_images"][1]["width"] == 1920

    # Whitespace should be handled correctly
    assert result["all_images"][2]["url"] == (
        "https://windows10spotlight.com/wp-content/uploads/whitespace-1920x1080.jpg"
    )
    assert result["all_images"][2]["width"] == 1920


@patch("spotlight.requests.get")
def test_get_image_info_image_filtering(mock_get):
    """Test filtering of wp-content images and mixed valid/invalid images."""
    html_content = """
    <html>
    <body>
        <article class="post-600 type-post">
            <h1>Image Filtering Test</h1>
            <img src="https://external-cdn.com/banner.jpg" alt="external">
            <img src="https://windows10spotlight.com/wp-content/uploads/valid1.jpg"
                 srcset="https://windows10spotlight.com/wp-content/uploads/valid1-1920x1080.jpg 1920w"
                 alt="valid1">
            <img src="/local/path/image.jpg" alt="local">
            <img src="https://windows10spotlight.com/wp-content/uploads/valid2.jpg"
                 srcset="https://windows10spotlight.com/wp-content/uploads/valid2-2560x1440.jpg 2560w"
                 alt="valid2">
        </article>
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_image_info(600)

    # Only wp-content images should be included
    assert len(result["all_images"]) == 2
    assert result["all_images"][0]["alt"] == "valid1"
    assert result["all_images"][1]["alt"] == "valid2"


@patch("spotlight.requests.get")
def test_get_image_info_post_id_extraction(mock_get):
    """Test invalid post class format and multiple article classes."""
    html_content = """
    <html>
    <body>
        <article class="post- type-post">
            <h1>Invalid Post ID</h1>
            <img src="https://windows10spotlight.com/wp-content/uploads/invalid.jpg"
                 alt="invalid">
        </article>
        <article class="post-abc type-post">
            <h1>Non-Numeric Post ID</h1>
            <img src="https://windows10spotlight.com/wp-content/uploads/nonnumeric.jpg"
                 alt="nonnumeric">
        </article>
        <article class="post-other-100 type-post">
            <h1>Multiple Dashes Post ID</h1>
            <img src="https://windows10spotlight.com/wp-content/uploads/multidash.jpg"
                 alt="multidash">
        </article>
        <article class="some-class post-200 another-class type-post">
            <h1>Valid Post With Multiple Classes</h1>
            <img src="https://windows10spotlight.com/wp-content/uploads/valid.jpg"
                 srcset="https://windows10spotlight.com/wp-content/uploads/valid-1920x1080.jpg 1920w"
                 alt="valid">
        </article>
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_image_info(999)

    # First article is selected, but post- has no numeric ID
    # so it falls back to the passed image_id
    assert result["id"] == 999
    assert result["title"] == "Invalid Post ID"


@pytest.mark.parametrize(
    "error_type,side_effect",
    [
        ("404", Mock(side_effect=requests.exceptions.HTTPError("404 Not Found"))),
        ("500", Mock(side_effect=requests.exceptions.HTTPError("500 Error"))),
        ("connection", Mock(side_effect=requests.exceptions.ConnectionError())),
        ("timeout", Mock(side_effect=requests.exceptions.Timeout())),
    ],
)
@patch("spotlight.requests.get")
def test_get_image_info_http_errors(mock_get, error_type, side_effect):
    """Test parameterized HTTP errors: 404, 500, connection, timeout."""
    mock_response = Mock()
    mock_response.raise_for_status = side_effect
    mock_get.return_value = mock_response

    with pytest.raises((requests.exceptions.HTTPError,
                       requests.exceptions.ConnectionError,
                       requests.exceptions.Timeout)):
        get_image_info(12345)

    mock_get.assert_called_once()


@patch("spotlight.requests.get")
def test_get_image_info_url_and_headers(mock_get):
    """Test URL construction and headers usage."""
    html_content = """
    <html>
    <body>
        <article class="post-111 type-post">
            <h1>URL Test</h1>
        </article>
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    get_image_info(111)

    # Verify URL construction
    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert call_args[0][0] == "https://windows10spotlight.com/images/111"

    # Verify headers
    assert "headers" in call_args.kwargs
    assert call_args.kwargs["headers"] == spotlight.HEADERS


@patch("spotlight.requests.get")
def test_get_image_info_og_metadata(mock_get):
    """Test multiple OG tags and partial OG tags with missing content."""
    html_content = """
    <html>
    <head>
        <meta property="og:title" content="OG Title">
        <meta property="og:image" content="https://example.com/og.jpg">
        <meta property="og:description" content="OG Description">
        <meta property="og:url">
        <meta property="og:type" content="article">
        <meta property="og:locale" content="en_US">
    </head>
    <body>
        <article class="post-300 type-post">
            <h1>OG Metadata Test</h1>
        </article>
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_image_info(300)

    # Should only include OG tags with content
    assert result["og_metadata"]["og:title"] == "OG Title"
    assert result["og_metadata"]["og:image"] == "https://example.com/og.jpg"
    assert result["og_metadata"]["og:description"] == "OG Description"
    assert result["og_metadata"]["og:type"] == "article"
    assert result["og_metadata"]["og:locale"] == "en_US"
    # og:url without content should not be included
    assert "og:url" not in result["og_metadata"]


@patch("spotlight.requests.get")
def test_get_image_info_mixed_scenarios(mock_get):
    """Test mixed srcset/non-srcset images and complex HTML."""
    html_content = """
    <html>
    <head>
        <meta property="og:title" content="Mixed Scenario">
    </head>
    <body>
        <article class="post-888 type-post">
            <h1>Complex Mixed Test</h1>
            <time datetime="2024-04-01T12:00:00Z">April 1, 2024</time>
            <a href="/tag/landscape" rel="tag">landscape</a>
            <a href="/tag/nature" rel="tag">nature</a>

            <!-- Image with srcset -->
            <img src="https://windows10spotlight.com/wp-content/uploads/img1.jpg"
                 srcset="https://windows10spotlight.com/wp-content/uploads/img1-1920x1080.jpg 1920w,
                         https://windows10spotlight.com/wp-content/uploads/img1-1280x720.jpg 1280w"
                 alt="with-srcset">

            <!-- Image without srcset -->
            <img src="https://windows10spotlight.com/wp-content/uploads/img2.jpg"
                 alt="without-srcset">

            <!-- Image with only one srcset entry -->
            <img src="https://windows10spotlight.com/wp-content/uploads/img3.jpg"
                 srcset="https://windows10spotlight.com/wp-content/uploads/img3-2560x1440.jpg 2560w"
                 alt="single-srcset">
        </article>
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_image_info(888)

    assert result["id"] == 888
    assert result["title"] == "Complex Mixed Test"
    assert result["tags"] == ["landscape", "nature"]
    assert result["date"] == "April 1, 2024"
    assert result["datetime"] == "2024-04-01T12:00:00Z"
    assert result["og_metadata"]["og:title"] == "Mixed Scenario"

    # Verify all three images are parsed correctly
    assert len(result["all_images"]) == 3
    assert result["all_images"][0]["width"] == 1920
    assert result["all_images"][0]["alt"] == "with-srcset"
    assert result["all_images"][1]["width"] is None
    assert result["all_images"][1]["alt"] == "without-srcset"
    assert result["all_images"][2]["width"] == 2560
    assert result["all_images"][2]["alt"] == "single-srcset"

    # Full resolution URL should be first image
    assert result["full_resolution_url"] == (
        "https://windows10spotlight.com/wp-content/uploads/img1-1920x1080.jpg"
    )
