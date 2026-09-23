"""
ReconX – Subdomain Finder Module
Discovers subdomains via wordlist brute-force and certificate transparency logs.
"""

import socket
import concurrent.futures
import urllib.request
import json
from utils.logger import get_logger

logger = get_logger("subdomain_finder")

WORDLIST = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "webmail", "email",
    "api", "dev", "staging", "stage", "beta", "alpha", "test", "qa",
    "admin", "dashboard", "panel", "cpanel", "whm", "plesk",
    "shop", "store", "pay", "checkout", "billing", "invoice",
    "blog", "news", "media", "static", "cdn", "assets", "img", "images",
    "upload", "files", "download", "docs", "wiki", "help", "support",
    "vpn", "ssh", "remote", "gateway", "proxy", "mx",
    "ns", "ns1", "ns2", "dns", "dns1", "dns2",
    "app", "apps", "mobile", "m", "wap",
    "secure", "portal", "intranet", "internal",
    "db", "sql", "mysql", "postgres", "mongo", "redis",
    "git", "gitlab", "svn", "jira", "confluence",
    "jenkins", "ci", "cd", "build", "deploy",
    "monitor", "status", "health", "metrics", "grafana",
    "kibana", "elastic", "logstash",
    "s3", "storage", "backup", "archive",
    "v1", "v2", "v3", "api2",
    "old", "new", "legacy", "demo",
    "chat", "meet", "video",
    "auth", "login", "sso", "oauth", "id",
    "search", "mail2", "smtp2", "mx1", "mx2",
]


def _resolve_subdomain(sub: str, domain: str) -> dict | None:
    fqdn = f"{sub}.{domain}"
    try:
        ip = socket.gethostbyname(fqdn)
        return {"subdomain": fqdn, "ip": ip, "source": "wordlist"}
    except Exception:
        return None


def _fetch_crt_sh(domain: str) -> list:
    found = []
    try:
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        req = urllib.request.Request(url, headers={"User-Agent": "ReconX/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
        seen = set()
        for entry in data:
            name = entry.get("name_value", "").lower()
            for sub in name.splitlines():
                sub = sub.strip().lstrip("*.")
                if sub.endswith(f".{domain}") and sub not in seen:
                    seen.add(sub)
                    try:
                        ip = socket.gethostbyname(sub)
                    except Exception:
                        ip = "Unresolved"
                    found.append({"subdomain": sub, "ip": ip, "source": "crt.sh"})
    except Exception as e:
        logger.warning(f"crt.sh lookup failed for {domain}: {e}")
    return found


def find_subdomains(domain: str, progress_callback=None) -> dict:
    for prefix in ("https://", "http://", "www."):
        if domain.lower().startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.strip().rstrip("/")

    logger.info(f"Starting subdomain enumeration for: {domain}")

    results = {
        "domain": domain,
        "subdomains": [],
        "total_checked": 0,
        "total_found": 0,
        "sources": {"wordlist": 0, "crt.sh": 0},
    }

    seen = set()
    found_list = []
    checked = [0]
    total = len(WORDLIST)

    # Phase 1: Certificate transparency
    crt_results = _fetch_crt_sh(domain)
    for item in crt_results:
        if item["subdomain"] not in seen:
            seen.add(item["subdomain"])
            found_list.append(item)
            results["sources"]["crt.sh"] += 1

    # Phase 2: Wordlist brute-force
    def check(sub):
        result = _resolve_subdomain(sub, domain)
        checked[0] += 1
        if progress_callback:
            progress_callback(checked[0], total, len(found_list))
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as ex:
        futures = [ex.submit(check, sub) for sub in WORDLIST]
        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                if res and res["subdomain"] not in seen:
                    seen.add(res["subdomain"])
                    found_list.append(res)
                    results["sources"]["wordlist"] += 1
            except Exception as e:
                logger.debug(f"Error: {e}")

    found_list.sort(key=lambda x: x["subdomain"])
    results["subdomains"] = found_list
    results["total_checked"] = total
    results["total_found"] = len(found_list)

    logger.info(f"Subdomain scan complete for {domain}: {results['total_found']} found")
    return results
