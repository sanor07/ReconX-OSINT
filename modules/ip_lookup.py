"""
ReconX – IP Intelligence Module
Geolocates an IP address and retrieves ISP, ASN, and network details.
"""

import socket
import concurrent.futures
from utils.api_clients import get_ip_geolocation, http_get
from utils.logger import get_logger

logger = get_logger("ip_lookup")

# Reverse DNS lookup helper
def _reverse_dns(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "No reverse DNS"


def _get_abuse_info(ip: str) -> dict:
    """Query AbuseIPDB public info (no key needed for basic check)."""
    # We do a lightweight check via ipinfo.io (free tier)
    resp = http_get(f"https://ipinfo.io/{ip}/json", timeout=8)
    if resp and resp.status_code == 200:
        try:
            return resp.json()
        except Exception:
            pass
    return {}


def analyze_ip(ip: str) -> dict:
    """
    Perform full IP intelligence gathering.

    Args:
        ip: IPv4 or IPv6 address string.

    Returns:
        A structured dict with geolocation, ISP, ASN, and network info.
    """
    ip = ip.strip()
    logger.info(f"Starting IP analysis: {ip}")

    result = {
        "ip": ip,
        "geolocation": {},
        "network": {},
        "reverse_dns": "",
        "map_url": "",
        "risk_notes": [],
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        geo_future = ex.submit(get_ip_geolocation, ip)
        rdns_future = ex.submit(_reverse_dns, ip)
        ipinfo_future = ex.submit(_get_abuse_info, ip)

        geo = geo_future.result()
        rdns = rdns_future.result()
        ipinfo = ipinfo_future.result()

    # Populate geolocation
    if geo.get("status") == "success":
        result["geolocation"] = {
            "country": geo.get("country", ""),
            "country_code": geo.get("countryCode", ""),
            "region": geo.get("regionName", ""),
            "city": geo.get("city", ""),
            "zip": geo.get("zip", ""),
            "latitude": geo.get("lat", ""),
            "longitude": geo.get("lon", ""),
            "timezone": geo.get("timezone", ""),
        }
        lat = geo.get("lat", "")
        lon = geo.get("lon", "")
        if lat and lon:
            result["map_url"] = f"https://www.google.com/maps?q={lat},{lon}"
    else:
        result["geolocation"]["error"] = geo.get("message", "Lookup failed")

    # Network info
    result["network"] = {
        "isp": geo.get("isp", ipinfo.get("org", "Unknown")),
        "organization": geo.get("org", ""),
        "asn": geo.get("as", ipinfo.get("org", "")),
        "hostname": ipinfo.get("hostname", rdns),
    }
    result["reverse_dns"] = rdns

    # Risk indicators
    if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172."):
        result["risk_notes"].append("ℹ Private/internal IP address")
    if ip in ("127.0.0.1", "::1"):
        result["risk_notes"].append("ℹ Loopback address")

    # Check if it's a known datacenter ASN (crude heuristic)
    asn_str = result["network"]["asn"].lower()
    dc_keywords = ["amazon", "google", "microsoft", "digitalocean", "linode", "vultr",
                   "ovh", "cloudflare", "fastly", "akamai", "hetzner"]
    for kw in dc_keywords:
        if kw in asn_str:
            result["risk_notes"].append(f"⚠ Cloud/Datacenter IP detected ({kw.title()})")
            break

    logger.info(f"IP analysis complete for {ip}.")
    return result
