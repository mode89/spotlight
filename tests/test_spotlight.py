"""Tests for spotlight.py module."""

import pytest
from unittest.mock import Mock, patch
from spotlight import get_total_pages


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
