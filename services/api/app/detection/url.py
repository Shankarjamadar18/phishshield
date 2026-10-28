"""URL lexical and brand lookalike checks; evidence is not proof of phishing."""
import ipaddress
import re
from urllib.parse import urlsplit

import idna
import tldextract
from rapidfuzz.distance import Levenshtein

# Bundled PSL only: never download a list or resolve/fetch a submitted URL.
EXTRACT = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None, include_psl_private_domains=True)
BRANDS = {
    "paypal": {"paypal.com"},
    "google": {"google.com"},
    "microsoft": {"microsoft.com", "microsoftonline.com", "live.com", "office.com"},
    "apple": {"apple.com", "icloud.com"},
    "amazon": {"amazon.com", "amazon.in", "amazon.co.uk"},
    "facebook": {"facebook.com", "fb.com"},
    "instagram": {"instagram.com"},
    "netflix": {"netflix.com"},
}
WATCH_TLDS = {"zip", "mov", "top", "xyz", "click", "work"}
SENSITIVE_WORDS = {"login", "signin", "verify", "password", "account", "secure", "update"}
LEET = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t"})


class InvalidURL(ValueError):
    pass


def analyze_url(value: str) -> dict:
    raw = value.strip()
    if re.search(r"[\x00-\x20\x7f\\]", raw):
        raise InvalidURL("URL must not contain spaces, control characters or backslashes.")
    try:
        parsed = urlsplit(raw)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            raise InvalidURL("Enter a complete http:// or https:// URL with a hostname.")
        port = parsed.port  # Validate syntax and range, including invalid IPv6 brackets.
        host = parsed.hostname.rstrip(".").lower()
        try:
            ipaddress.ip_address(host)
            is_ip = True
            ascii_host = host
            unicode_host = host
        except ValueError:
            is_ip = False
            ascii_host = idna.encode(host, uts46=True, std3_rules=True).decode("ascii")
            unicode_host = idna.decode(ascii_host)
            if "." not in ascii_host:
                raise InvalidURL("Enter a URL with a public domain name or an IP address.")
    except (ValueError, idna.IDNAError) as exc:
        raise InvalidURL(str(exc)) from exc

    extracted = EXTRACT(ascii_host) if not is_ip else None
    domain = extracted.top_domain_under_public_suffix if extracted else ""
    label = extracted.domain if extracted else ""
    subdomain = extracted.subdomain if extracted else ""
    suffix = extracted.suffix if extracted else ""
    findings: list[dict] = []

    def flag(code: str, severity: str, message: str, evidence: str):
        findings.append({"code": code, "severity": severity, "message": message, "evidence": evidence})

    if parsed.scheme.lower() == "http":
        flag("unencrypted_http", "warning", "The URL does not use HTTPS.", "http")
    if parsed.username is not None or parsed.password is not None:
        flag("embedded_credentials", "warning", "Text before @ can disguise the actual destination.", ascii_host)
    if is_ip:
        flag("ip_host", "warning", "An IP address is used instead of a domain name.", ascii_host)
    if not is_ip and not suffix:
        flag("unknown_suffix", "warning", "The suffix is absent from the bundled public suffix list.", ascii_host)
    if any(part.startswith("xn--") for part in ascii_host.split(".")):
        flag("internationalized_domain", "warning", "Internationalized domain: inspect its spelling carefully.", unicode_host)
    depth = len(subdomain.split(".")) if subdomain else 0
    if depth >= 3:
        flag("deep_subdomains", "warning", "Several subdomains can hide the registered domain.", subdomain)
    if suffix.split(".")[-1] in WATCH_TLDS:
        flag("watchlist_suffix", "warning", "This suffix is on the local review list; it alone does not prove phishing.", suffix)
    if len(raw) > 200:
        flag("long_url", "warning", "The URL is unusually long.", str(len(raw)))
    if label.count("-") >= 3:
        flag("many_hyphens", "warning", "The domain label contains several hyphens.", label)
    if port is not None and port not in {80, 443}:
        flag("unusual_port", "warning", "A nonstandard web port is specified.", str(port))

    tokens = set(re.findall(r"[a-z]+", f"{label} {subdomain} {parsed.path} {parsed.query}".lower()))
    sensitive = sorted(tokens & SENSITIVE_WORDS)
    for brand, official in BRANDS.items():
        if domain in official:
            continue  # Exemption applies to this brand only, not every other brand.
        distance = Levenshtein.distance(label, brand)
        leet_match = label != brand and label.translate(LEET) == brand
        typo = len(label) >= 5 and distance <= 1
        decorated = label.startswith(f"{brand}-") or label.endswith(f"-{brand}")
        subdomain_brand = brand in subdomain.split(".")
        if typo or leet_match or decorated or subdomain_brand:
            flag("brand_lookalike", "high", f"Possible {brand} impersonation outside the configured official domains.",
                 f"host={ascii_host}; registered_domain={domain or ascii_host}; brand={brand}; edit_distance={distance}")

    verdict = "suspicious" if any(f["severity"] == "high" for f in findings) else "review" if findings else "no_indicators"
    return {
        "detector": "url_rules", "version": "2.0.0", "verdict": verdict,
        "features": {
            "hostname": ascii_host, "unicode_hostname": unicode_host,
            "registered_domain": domain or None, "suffix": suffix or None,
            "is_ip": is_ip, "uses_https": parsed.scheme.lower() == "https",
            "url_length": len(raw), "hyphen_count": label.count("-"),
            "subdomain_count": depth, "has_credentials": parsed.username is not None or parsed.password is not None,
            "port": port, "sensitive_keywords": sensitive,
        },
        "findings": findings,
        "limitations": "Offline rules only. No website, DNS, reputation or trained-model checks. No indicators does not mean safe. Brand coverage is limited to configured domains.",
    }