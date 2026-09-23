"""
ReconX – Website Technology Detector
Fingerprints CMS, frameworks, CDNs, analytics, security headers,
and web server technology from HTTP responses and page content.
"""

import re
import concurrent.futures
from utils.api_clients import http_get
from utils.logger import get_logger

logger = get_logger("tech_detector")

# ── Signature Database ─────────────────────────────────────────────────────────
# Format: category -> {tech_name: {detection_method: pattern}}
SIGNATURES = {
    "CMS": {
        "WordPress":        {"header": None, "body": r'wp-content|wp-includes|wordpress', "meta": r'WordPress'},
        "Joomla":           {"header": None, "body": r'/media/jui/|Joomla!', "meta": None},
        "Drupal":           {"header": "X-Generator:Drupal", "body": r'sites/default/files|Drupal\.settings', "meta": None},
        "Magento":          {"header": None, "body": r'Mage\.Cookies|/skin/frontend/|Magento', "meta": None},
        "Shopify":          {"header": None, "body": r'Shopify\.theme|cdn\.shopify\.com', "meta": None},
        "Wix":              {"header": None, "body": r'wix\.com|wixsite\.com|X-Wix-', "meta": None},
        "Squarespace":      {"header": None, "body": r'squarespace\.com|squarespace-cdn', "meta": None},
        "Ghost":            {"header": "X-Ghost-Cache-Status", "body": r'ghost\.io|content/themes/casper', "meta": None},
        "TYPO3":            {"header": None, "body": r'typo3|TYPO3', "meta": None},
        "PrestaShop":       {"header": None, "body": r'prestashop|PrestaShop', "meta": None},
        "OpenCart":         {"header": None, "body": r'route=common|OpenCart', "meta": None},
        "HubSpot CMS":      {"header": None, "body": r'hs-scripts\.com|hubspot\.com/hs', "meta": None},
        "Webflow":          {"header": None, "body": r'webflow\.com|Webflow', "meta": None},
    },
    "JavaScript Frameworks": {
        "React":            {"header": None, "body": r'react\.development\.js|react\.production|__react|data-reactroot', "meta": None},
        "Vue.js":           {"header": None, "body": r'vue\.js|vue\.min\.js|__vue__|Vue\.config', "meta": None},
        "Angular":          {"header": None, "body": r'ng-version|angular\.js|angular\.min|ng-app', "meta": None},
        "Next.js":          {"header": "X-Powered-By:Next.js", "body": r'__NEXT_DATA__|/_next/static', "meta": None},
        "Nuxt.js":          {"header": None, "body": r'__nuxt|_nuxt/|nuxtjs', "meta": None},
        "jQuery":           {"header": None, "body": r'jquery[\.\-]\d|jquery\.min\.js|jQuery v', "meta": None},
        "Bootstrap":        {"header": None, "body": r'bootstrap\.min\.css|bootstrap\.css|Bootstrap v', "meta": None},
        "Tailwind CSS":     {"header": None, "body": r'tailwindcss|tailwind\.min\.css', "meta": None},
        "Svelte":           {"header": None, "body": r'svelte-|\.svelte\.css', "meta": None},
        "Ember.js":         {"header": None, "body": r'ember\.js|ember\.min\.js|Ember\.VERSION', "meta": None},
        "Backbone.js":      {"header": None, "body": r'backbone\.js|backbone\.min\.js', "meta": None},
        "Alpine.js":        {"header": None, "body": r'alpinejs|x-data=|x-bind=', "meta": None},
    },
    "Backend / Server": {
        "PHP":              {"header": "X-Powered-By:PHP", "body": r'\.php\?|\.php$', "meta": None},
        "ASP.NET":          {"header": "X-Powered-By:ASP.NET", "body": r'__VIEWSTATE|WebResource\.axd', "meta": None},
        "Ruby on Rails":    {"header": "X-Powered-By:Phusion Passenger", "body": r'rails|Ruby on Rails', "meta": None},
        "Django":           {"header": None, "body": r'csrfmiddlewaretoken|Django', "meta": None},
        "Laravel":          {"header": None, "body": r'laravel|XSRF-TOKEN=', "meta": None},
        "Flask":            {"header": None, "body": r'Werkzeug|flask', "meta": None},
        "Node.js / Express":{"header": "X-Powered-By:Express", "body": None, "meta": None},
        "Spring Boot":      {"header": None, "body": r'Spring|Whitelabel Error Page', "meta": None},
        "FastAPI":          {"header": None, "body": r'fastapi|/docs#/|/redoc', "meta": None},
    },
    "CDN / Hosting": {
        "Cloudflare":       {"header": "Server:cloudflare", "body": None, "meta": None},
        "AWS CloudFront":   {"header": "X-Cache:Hit from cloudfront", "body": None, "meta": None},
        "AWS S3":           {"header": "Server:AmazonS3", "body": r'AmazonS3|s3\.amazonaws\.com', "meta": None},
        "Google Cloud CDN": {"header": "Via:1.1 google", "body": None, "meta": None},
        "Fastly":           {"header": "Via:1.1 varnish", "body": None, "meta": None},
        "Azure CDN":        {"header": "X-MSEdge-Ref", "body": None, "meta": None},
        "Netlify":          {"header": "X-Nf-Request-Id", "body": None, "meta": None},
        "Vercel":           {"header": "X-Vercel-Id", "body": None, "meta": None},
        "GitHub Pages":     {"header": None, "body": r'github\.io', "meta": None},
    },
    "Analytics / Marketing": {
        "Google Analytics": {"header": None, "body": r'google-analytics\.com|gtag\(|UA-\d{6,}|G-[A-Z0-9]+', "meta": None},
        "Google Tag Manager":{"header":None, "body": r'googletagmanager\.com|GTM-[A-Z0-9]+', "meta": None},
        "Facebook Pixel":   {"header": None, "body": r'connect\.facebook\.net/en_US/fbevents|fbq\(', "meta": None},
        "HubSpot":          {"header": None, "body": r'js\.hs-scripts\.com|hbspt\.', "meta": None},
        "Hotjar":           {"header": None, "body": r'static\.hotjar\.com|hotjar\.identify', "meta": None},
        "Mixpanel":         {"header": None, "body": r'mixpanel\.com/lib|mixpanel\.init', "meta": None},
        "Intercom":         {"header": None, "body": r'widget\.intercom\.io|Intercom\(', "meta": None},
        "Crisp Chat":       {"header": None, "body": r'client\.crisp\.chat|CRISP_WEBSITE_ID', "meta": None},
        "Segment":          {"header": None, "body": r'cdn\.segment\.com|analytics\.load\(', "meta": None},
    },
    "Security": {
        "reCAPTCHA":        {"header": None, "body": r'google\.com/recaptcha|g-recaptcha', "meta": None},
        "hCaptcha":         {"header": None, "body": r'hcaptcha\.com', "meta": None},
        "Cloudflare WAF":   {"header": "Server:cloudflare", "body": r'cf-ray|__cfduid|cf_clearance', "meta": None},
        "Sucuri WAF":       {"header": "X-Sucuri-ID", "body": None, "meta": None},
        "Imperva/Incapsula": {"header": "X-Iinfo", "body": r'incapsula|visid_incap_', "meta": None},
        "HSTS Enabled":     {"header": "Strict-Transport-Security", "body": None, "meta": None},
        "CSP Enabled":      {"header": "Content-Security-Policy", "body": None, "meta": None},
    },
    "E-commerce": {
        "WooCommerce":      {"header": None, "body": r'woocommerce|wc-block|is-cart|is-checkout', "meta": None},
        "Stripe":           {"header": None, "body": r'js\.stripe\.com|Stripe\(', "meta": None},
        "PayPal":           {"header": None, "body": r'paypal\.com/sdk|paypal-checkout', "meta": None},
    },
}


def detect_technologies(domain: str) -> dict:
    """
    Fingerprint web technologies on a domain.

    Returns a structured dict with detected techs grouped by category,
    header analysis, and security posture summary.
    """
    for prefix in ("https://", "http://", "www."):
        if domain.lower().startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.strip().rstrip("/")

    logger.info(f"Starting technology detection for: {domain}")

    result = {
        "domain": domain,
        "url_scanned": "",
        "http_status": None,
        "server": "",
        "detected": {},      # category -> [tech_name, ...]
        "headers": {},
        "security_posture": {},
        "meta_tags": {},
        "raw_tech_list": [],
        "scan_errors": [],
    }

    # Try HTTPS first, then HTTP
    resp = None
    for scheme in ("https", "http"):
        url = f"{scheme}://{domain}"
        resp = http_get(url, timeout=12)
        if resp is not None:
            result["url_scanned"] = url
            result["http_status"] = resp.status_code
            break

    if resp is None:
        result["scan_errors"].append("Could not connect to the domain.")
        return result

    headers = dict(resp.headers)
    body = ""
    try:
        body = resp.text[:300_000]  # cap at 300KB to avoid memory issues
    except Exception:
        pass

    result["server"] = headers.get("Server", "Not disclosed")
    result["headers"] = _extract_key_headers(headers)
    result["meta_tags"] = _extract_meta_tags(body)
    result["security_posture"] = _assess_security(headers)

    # ── Run all signature checks ───────────────────────────────────────────────
    detected = {}
    for category, techs in SIGNATURES.items():
        found = []
        for tech_name, sigs in techs.items():
            if _matches(sigs, headers, body):
                found.append(tech_name)
        if found:
            detected[category] = found

    result["detected"] = detected
    result["raw_tech_list"] = [t for cats in detected.values() for t in cats]

    logger.info(f"Tech detection done for {domain}: {len(result['raw_tech_list'])} technologies found.")
    return result


def _matches(sigs: dict, headers: dict, body: str) -> bool:
    """Return True if any signature pattern matches."""
    # Header check
    if sigs.get("header"):
        hdr_key, _, hdr_val = sigs["header"].partition(":")
        hdr_key = hdr_key.strip()
        hdr_val = hdr_val.strip().lower()
        actual = headers.get(hdr_key, "").lower()
        if hdr_val:
            if hdr_val in actual:
                return True
        else:
            if actual:
                return True

    # Body regex check
    if sigs.get("body") and body:
        if re.search(sigs["body"], body, re.IGNORECASE):
            return True

    return False


def _extract_key_headers(headers: dict) -> dict:
    """Extract security and informational headers for display."""
    keys = [
        "Server", "X-Powered-By", "X-Generator", "X-Frame-Options",
        "Content-Security-Policy", "Strict-Transport-Security",
        "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy",
        "Set-Cookie", "Via", "X-Cache", "CF-Ray", "X-Vercel-Id",
        "X-Nf-Request-Id", "X-Amz-Cf-Id",
    ]
    out = {}
    for k in keys:
        v = headers.get(k, "")
        if v:
            out[k] = v[:200]
    return out


def _extract_meta_tags(body: str) -> dict:
    """Pull key <meta> tag values from the page."""
    out = {}
    patterns = {
        "generator":    r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)',
        "description":  r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{0,200})',
        "og:title":     r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
        "og:site_name": r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)',
        "viewport":     r'<meta[^>]+name=["\']viewport["\'][^>]+content=["\']([^"\']+)',
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, body, re.IGNORECASE)
        if m:
            out[key] = m.group(1).strip()
    return out


def _assess_security(headers: dict) -> dict:
    """Evaluate the security posture based on response headers."""
    checks = {
        "HTTPS":                        True,  # we already connected via HTTPS
        "HSTS":                         bool(headers.get("Strict-Transport-Security")),
        "CSP":                          bool(headers.get("Content-Security-Policy")),
        "X-Frame-Options":              bool(headers.get("X-Frame-Options")),
        "X-Content-Type-Options":       bool(headers.get("X-Content-Type-Options")),
        "Referrer-Policy":              bool(headers.get("Referrer-Policy")),
        "Permissions-Policy":           bool(headers.get("Permissions-Policy")),
        "Server Header Hidden":         not bool(headers.get("Server")),
        "X-Powered-By Hidden":          not bool(headers.get("X-Powered-By")),
    }
    score = sum(1 for v in checks.values() if v)
    checks["security_score"] = f"{score}/{len(checks)-1}"
    checks["rating"] = ("Excellent" if score >= 7 else
                        "Good"      if score >= 5 else
                        "Fair"      if score >= 3 else "Poor")
    return checks
