import socket

import pytest
from app.detection.url import InvalidURL, analyze_url


def codes(url):
    return {f["code"] for f in analyze_url(url)["findings"]}


def test_official_domain_has_no_indicators_not_a_safe_claim():
    result = analyze_url("https://www.paypal.com/login")
    assert result["verdict"] == "no_indicators"
    assert result["features"]["registered_domain"] == "paypal.com"


@pytest.mark.parametrize("url", ["https://paypa1.com", "https://paypol.com", "https://paypal-login.com", "https://paypal.com.attacker.com"])
def test_brand_lookalike_is_evidence_based_suspicious(url):
    assert analyze_url(url)["verdict"] == "suspicious"
    assert "brand_lookalike" in codes(url)


def test_public_suffix_and_private_tenant_boundaries():
    assert analyze_url("https://amazon.co.uk")["verdict"] == "no_indicators"
    result = analyze_url("https://paypal.github.io")
    assert result["features"]["registered_domain"] == "paypal.github.io"
    assert result["verdict"] == "suspicious"


def test_official_brand_exemption_is_not_global():
    assert analyze_url("https://paypal.google.com")["verdict"] == "suspicious"


def test_https_is_not_a_safety_guarantee():
    assert analyze_url("https://paypa1.com")["verdict"] == "suspicious"


def test_ip_and_unencrypted_http_require_review():
    assert analyze_url("http://127.0.0.1/login")["verdict"] == "review"
    assert {"ip_host", "unencrypted_http"} <= codes("http://127.0.0.1/login")


def test_ipv6_and_credentials_parse_without_contacting_host():
    assert analyze_url("https://[::1]:8443/")["features"]["is_ip"] is True
    assert "embedded_credentials" in codes("https://paypal.com@evil.example/login")


def test_idn_keeps_ascii_and_unicode_evidence():
    result = analyze_url("https://bücher.de")
    assert result["features"]["hostname"] == "xn--bcher-kva.de"
    assert result["features"]["unicode_hostname"] == "bücher.de"
    assert "internationalized_domain" in codes("https://bücher.de")


def test_trailing_dot_does_not_trigger_official_brand_match():
    assert analyze_url("https://PAYPAL.COM./login")["verdict"] == "no_indicators"


def test_lexical_features_are_measured():
    result = analyze_url("http://a.b.c.demo-one-two-three.xyz:8080/verify?account=1")
    assert result["features"]["hyphen_count"] == 3
    assert result["features"]["subdomain_count"] == 3
    assert result["features"]["sensitive_keywords"] == ["account", "verify"]
    assert {"deep_subdomains", "many_hyphens", "watchlist_suffix", "unusual_port"} <= {f["code"] for f in result["findings"]}


@pytest.mark.parametrize("url", ["", "paypal.com", "ftp://example.com", "https:///login", "https://x.com:abc", "https://x.com:99999", "https://[bad]/", "https://exa mple.com", "https://example.com\\@evil.com", "https://%65xample.com", "https://example.com/\nlogin"])
def test_invalid_urls_rejected(url):
    with pytest.raises(InvalidURL):
        analyze_url(url)


def test_detection_never_resolves_or_fetches(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network access forbidden")
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    import requests
    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    assert analyze_url("https://paypa1.com")["verdict"] == "suspicious"