"""
ReconX API Clients Utility
Centralized HTTP client helpers with error handling, timeouts, and retries.
"""

import requests
import socket
import dns.resolver
import whois
import json
from utils.logger import get_logger

logger = get_logger("api_clients")

# Default request timeout in seconds
DEFAULT_TIMEOUT = 10
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def http_get(url: str, timeout: int = DEFAULT_TIMEOUT, headers: dict = None) -> requests.Response | None:
    """
    Perform a GET request with error handling.
    Returns the Response object or None on failure.
    """
    try:
        h = {**HEADERS, **(headers or {})}
        response = requests.get(url, headers=h, timeout=timeout, allow_redirects=True)
        return response
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connection error: {url}")
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout: {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed [{url}]: {e}")
    return None


def check_username_on_platform(platform_url: str, username: str) -> dict:
    """
    Check if a username exists on a platform by checking the profile URL.
    Returns a dict with 'found', 'url', and 'status_code'.
    """
    url = platform_url.format(username=username)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
        found = resp.status_code == 200
        return {"url": url, "found": found, "status_code": resp.status_code}
    except Exception as e:
        logger.debug(f"Error checking {url}: {e}")
        return {"url": url, "found": False, "status_code": None, "error": str(e)}


def get_ip_geolocation(ip: str) -> dict:
    """Query ip-api.com for geolocation data."""
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    resp = http_get(url)
    if resp and resp.status_code == 200:
        try:
            return resp.json()
        except Exception:
            pass
    return {"status": "fail", "message": "Could not retrieve geolocation data."}


def get_whois_data(domain: str) -> dict:
    """Perform a WHOIS lookup for a domain."""
    try:
        w = whois.whois(domain)
        return {
            "domain_name": str(w.domain_name),
            "registrar": str(w.registrar),
            "creation_date": str(w.creation_date),
            "expiration_date": str(w.expiration_date),
            "updated_date": str(w.updated_date),
            "name_servers": str(w.name_servers),
            "status": str(w.status),
            "emails": str(w.emails),
            "country": str(w.country),
            "org": str(w.org),
            "raw": str(w.text)[:2000] if w.text else "",
        }
    except Exception as e:
        logger.error(f"WHOIS lookup failed for {domain}: {e}")
        return {"error": str(e)}


def get_dns_records(domain: str) -> dict:
    """Retrieve common DNS records for a domain."""
    record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
    results = {}
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype, lifetime=5)
            results[rtype] = [r.to_text() for r in answers]
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            results[rtype] = []
        except Exception as e:
            results[rtype] = [f"Error: {e}"]
    return results


def validate_email_mx(email: str) -> dict:
    """Validate an email address and check its MX records."""
    import re
    result = {
        "email": email,
        "format_valid": False,
        "domain": None,
        "mx_records": [],
        "mx_found": False,
        "disposable": False,
    }
    # Basic format check
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        result["error"] = "Invalid email format"
        return result
    result["format_valid"] = True
    domain = email.split("@")[1]
    result["domain"] = domain

    # MX record lookup
    try:
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=5)
        result["mx_records"] = sorted(
            [str(r.exchange) for r in mx_records]
        )
        result["mx_found"] = bool(result["mx_records"])
    except Exception as e:
        result["mx_error"] = str(e)

    # Simple disposable domain check
    disposable_domains = {
        "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
        "throwaway.email", "yopmail.com", "sharklasers.com", "trashmail.com",
        "fakeinbox.com", "getnada.com", "maildrop.cc", "dispostable.com"
    }
    result["disposable"] = domain.lower() in disposable_domains
    return result
