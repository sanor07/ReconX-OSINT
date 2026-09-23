"""
ReconX – Email Intelligence Module
Validates email addresses, checks MX records, and performs basic OSINT.
"""

import socket
from utils.api_clients import validate_email_mx, get_dns_records, http_get
from utils.logger import get_logger

logger = get_logger("email_lookup")


def analyze_email(email: str) -> dict:
    """
    Perform comprehensive email intelligence gathering.

    Returns a structured dict with validation, MX records, and domain intel.
    """
    logger.info(f"Analyzing email: {email}")
    result = {
        "email": email,
        "validation": {},
        "domain_info": {},
        "mx_records": [],
        "dns_txt_records": [],
        "breach_check_note": "",
        "provider_guess": "",
        "risk_indicators": [],
    }

    # Step 1: Format validation + MX lookup
    validation = validate_email_mx(email)
    result["validation"] = {
        "format_valid": validation.get("format_valid", False),
        "mx_found": validation.get("mx_found", False),
        "is_disposable": validation.get("disposable", False),
        "domain": validation.get("domain", ""),
    }
    result["mx_records"] = validation.get("mx_records", [])

    domain = validation.get("domain", "")
    if not domain:
        result["error"] = "Could not extract domain from email."
        return result

    # Step 2: DNS TXT records (SPF, DMARC, DKIM hints)
    try:
        dns_records = get_dns_records(domain)
        result["dns_txt_records"] = dns_records.get("TXT", [])
        result["dns_a_records"] = dns_records.get("A", [])
    except Exception as e:
        result["dns_error"] = str(e)

    # Step 3: Identify email provider
    mx_str = " ".join(result["mx_records"]).lower()
    if "google" in mx_str or "googlemail" in mx_str:
        result["provider_guess"] = "Google / Gmail"
    elif "outlook" in mx_str or "microsoft" in mx_str or "hotmail" in mx_str:
        result["provider_guess"] = "Microsoft / Outlook"
    elif "yahoo" in mx_str:
        result["provider_guess"] = "Yahoo Mail"
    elif "protonmail" in mx_str:
        result["provider_guess"] = "ProtonMail"
    elif "zoho" in mx_str:
        result["provider_guess"] = "Zoho Mail"
    elif result["mx_records"]:
        result["provider_guess"] = f"Custom ({result['mx_records'][0]})"
    else:
        result["provider_guess"] = "Unknown / No MX"

    # Step 4: Risk indicators
    if result["validation"]["is_disposable"]:
        result["risk_indicators"].append("⚠ Disposable email domain detected")
    if not result["validation"]["mx_found"]:
        result["risk_indicators"].append("⚠ No MX records – emails cannot be received")
    if not result["validation"]["format_valid"]:
        result["risk_indicators"].append("✗ Invalid email format")

    # Check for SPF record
    spf_found = any("v=spf1" in r.lower() for r in result["dns_txt_records"])
    if not spf_found:
        result["risk_indicators"].append("⚠ No SPF record found – spoofing risk")

    # Step 5: HaveIBeenPwned note (API key required for actual check)
    result["breach_check_note"] = (
        "Breach database check requires a HaveIBeenPwned API key. "
        "Visit https://haveibeenpwned.com/API/v3 to obtain one."
    )

    # Step 6: Try to resolve domain IP
    try:
        ip = socket.gethostbyname(domain)
        result["domain_info"]["resolved_ip"] = ip
    except Exception:
        result["domain_info"]["resolved_ip"] = "Could not resolve"

    logger.info(f"Email analysis complete for {email}. Provider: {result['provider_guess']}")
    return result
