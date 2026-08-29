"""Тесты сборки curl."""

from wayfire_sim.curl_builder import build_curl, is_get_available_jobs_url


def test_is_get_available_jobs_url_by_query_name() -> None:
    url = (
        "https://www.wayfair.com/wayhome/graphql"
        "?queryHash=7632b54fcfa7cd10bec94e6cda6236bf&queryName=GetAvailableJobs"
    )
    assert is_get_available_jobs_url(url)


def test_is_get_available_jobs_url_by_hash() -> None:
    url = "https://www.wayfair.com/wayhome/graphql?queryHash=7632b54fcfa7cd10bec94e6cda6236bf"
    assert is_get_available_jobs_url(url)


def test_build_curl_post_with_body() -> None:
    url = "https://www.wayfair.com/wayhome/graphql?queryName=GetAvailableJobs"
    headers = {
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
        "Content-Length": "99",
        "Host": "www.wayfair.com",
    }
    body = b'{"hash":"7632b54fcfa7cd10bec94e6cda6236bf","variables":{"startDate":"2026-08-29"}}'

    curl = build_curl("POST", url, headers, body)

    assert curl.startswith("curl ")
    assert "Authorization: Bearer token" in curl
    assert "Content-Type: application/json" in curl
    assert "Content-Length" not in curl
    assert "Host:" not in curl
    assert "--data-raw" in curl
    assert "GetAvailableJobs" in curl or "startDate" in curl


def test_build_curl_multiline() -> None:
    curl = build_curl("GET", "https://example.com", {}, None, multiline=True)
    assert " \\\n  " in curl
