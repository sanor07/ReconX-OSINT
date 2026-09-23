"""
ReconX – Domain Intelligence Module
Performs WHOIS lookups, DNS record enumeration, and hosting discovery.
"""

import socket
import concurrent.futures
from utils.api_clients import get_whois_data, get_dns_records, get_ip_geolocation, http_get
from utils.logger import get_logger

logger = get_logger("domain_lookup")


def analyze_domain(domain: str) -> dict:
    """
    Perform comprehensive domain intelligence.

    Args:
        domain: The domain name (e.g. 'example.com').

    Returns:
        A structured dict containing WHOIS, DNS, hosting, and technology intel.
    """
    # Strip protocol prefixes if user pastes a URL
    for prefix in ("https://", "http://", "www."):
        if domain.lower().startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.strip().rstrip("/")

    logger.info(f"Starting domain analysis: {domain}")

    result = {
        "domain": domain,
        "whois": {},
        "dns": {},
        "hosting": {},
        "web_info": {},
        "subdomains_found": [],
    }

    # Run WHOIS and DNS in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        whois_future = ex.submit(get_whois_data, domain)
        dns_future = ex.submit(get_dns_records, domain)
        resolve_future = ex.submit(_safe_resolve, domain)
        http_future = ex.submit(_check_http_headers, domain)

        result["whois"] = whois_future.result()
        result["dns"] = dns_future.result()
        ip = resolve_future.result()
        result["web_info"] = http_future.result()

    # Geo-resolve the primary A record
    if ip:
        result["hosting"]["primary_ip"] = ip
        geo = get_ip_geolocation(ip)
        result["hosting"]["geolocation"] = {
            "country": geo.get("country", ""),
            "region": geo.get("regionName", ""),
            "city": geo.get("city", ""),
            "isp": geo.get("isp", ""),
            "org": geo.get("org", ""),
            "lat": geo.get("lat", ""),
            "lon": geo.get("lon", ""),
        }
    else:
        result["hosting"]["primary_ip"] = "Could not resolve"

    # Basic subdomain check
    common_subs = ["www", "mail", "ftp", "cpanel", "webmail", "admin", "api", "dev", "staging", "shop"]
    found_subs = []
    for sub in common_subs:
        try:
            socket.gethostbyname(f"{sub}.{domain}")
            found_subs.append(f"{sub}.{domain}")
        except Exception:
            pass
    result["subdomains_found"] = found_subs

    logger.info(f"Domain analysis complete for {domain}.")
    return result


def _safe_resolve(domain: str) -> str | None:
    """Resolve domain to its primary IP."""
    try:
        return socket.gethostbyname(domain)
    except Exception:
        return None


def _check_http_headers(domain: str) -> dict:
    """Fetch HTTP headers to identify the web server and technologies."""
    info = {}
    for scheme in ("https", "http"):
        resp = http_get(f"{scheme}://{domain}", timeout=8)
        if resp is not None:
            info["http_status"] = resp.status_code
            info["server"] = resp.headers.get("Server", "Not disclosed")
            info["x_powered_by"] = resp.headers.get("X-Powered-By", "Not disclosed")
            info["content_type"] = resp.headers.get("Content-Type", "")
            info["strict_transport_security"] = resp.headers.get("Strict-Transport-Security", "Not set")
            info["x_frame_options"] = resp.headers.get("X-Frame-Options", "Not set")
            info["content_security_policy"] = resp.headers.get("Content-Security-Policy", "Not set")[:120] if resp.headers.get("Content-Security-Policy") else "Not set"
            info["scheme_used"] = scheme
            break
    return info
