"""Tests for spotlight.py module."""

import pytest
from unittest.mock import Mock, patch
import spotlight
from spotlight import get_total_pages, get_page


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
