"""
ReconX – Phone Number Intelligence Module
Parses, validates and enriches phone numbers using the phonenumbers library
plus public data sources — no paid API keys required.
"""

import re
import requests
from utils.logger import get_logger

logger = get_logger("phone_lookup")

# Country dial-code table for fallback
COUNTRY_CODES = {
    "+1": "United States / Canada", "+7": "Russia / Kazakhstan",
    "+20": "Egypt", "+27": "South Africa", "+30": "Greece",
    "+31": "Netherlands", "+32": "Belgium", "+33": "France",
    "+34": "Spain", "+36": "Hungary", "+39": "Italy", "+40": "Romania",
    "+41": "Switzerland", "+43": "Austria", "+44": "United Kingdom",
    "+45": "Denmark", "+46": "Sweden", "+47": "Norway", "+48": "Poland",
    "+49": "Germany", "+51": "Peru", "+52": "Mexico", "+54": "Argentina",
    "+55": "Brazil", "+56": "Chile", "+57": "Colombia", "+58": "Venezuela",
    "+60": "Malaysia", "+61": "Australia", "+62": "Indonesia", "+63": "Philippines",
    "+64": "New Zealand", "+65": "Singapore", "+66": "Thailand",
    "+81": "Japan", "+82": "South Korea", "+84": "Vietnam",
    "+86": "China", "+90": "Turkey", "+91": "India", "+92": "Pakistan",
    "+93": "Afghanistan", "+94": "Sri Lanka", "+95": "Myanmar",
    "+98": "Iran", "+212": "Morocco", "+213": "Algeria",
    "+216": "Tunisia", "+218": "Libya", "+220": "Gambia",
    "+221": "Senegal", "+234": "Nigeria", "+254": "Kenya",
    "+255": "Tanzania", "+256": "Uganda", "+260": "Zambia",
    "+263": "Zimbabwe", "+351": "Portugal", "+352": "Luxembourg",
    "+353": "Ireland", "+354": "Iceland", "+358": "Finland",
    "+359": "Bulgaria", "+370": "Lithuania", "+371": "Latvia",
    "+372": "Estonia", "+380": "Ukraine", "+381": "Serbia",
    "+385": "Croatia", "+386": "Slovenia", "+389": "North Macedonia",
    "+420": "Czech Republic", "+421": "Slovakia", "+886": "Taiwan",
    "+966": "Saudi Arabia", "+971": "UAE", "+972": "Israel",
    "+973": "Bahrain", "+974": "Qatar", "+975": "Bhutan",
    "+976": "Mongolia", "+977": "Nepal", "+994": "Azerbaijan",
    "+995": "Georgia", "+996": "Kyrgyzstan", "+998": "Uzbekistan",
}

# Number type mapping
NUMBER_TYPES = {
    0: "Fixed Line",
    1: "Mobile",
    2: "Fixed or Mobile",
    3: "Toll Free",
    4: "Premium Rate",
    5: "Shared Cost",
    6: "VOIP",
    7: "Personal Number",
    8: "Pager",
    9: "UAN",
    10: "Voicemail",
    99: "Unknown",
}


def analyze_phone(number: str) -> dict:
    """
    Perform comprehensive phone number intelligence gathering.

    Args:
        number: Raw phone number string (any format)

    Returns:
        A structured dict with validation, carrier, location, timezone data.
    """
    logger.info(f"Analyzing phone number: {number}")
    result = {
        "raw_input": number,
        "parsed": {},
        "validation": {},
        "carrier_info": {},
        "location_info": {},
        "risk_indicators": [],
        "formatted": {},
        "additional_info": {},
    }

    # Clean the input
    cleaned = re.sub(r"[\s\-\(\)\.\_]", "", number.strip())
    if not cleaned.startswith("+"):
        # Try to guess if it starts with a country code
        if cleaned.startswith("00"):
            cleaned = "+" + cleaned[2:]
        elif len(cleaned) == 10:
            cleaned = "+1" + cleaned  # Assume US if 10 digits

    result["parsed"]["cleaned"] = cleaned

    # Try phonenumbers library first (most accurate)
    try:
        import phonenumbers
        from phonenumbers import geocoder, carrier, timezone as pn_timezone
        from phonenumbers import PhoneNumberType, PhoneNumberFormat

        try:
            phone_obj = phonenumbers.parse(cleaned, None)
        except Exception:
            # Retry with default region US
            phone_obj = phonenumbers.parse(number, "US")

        is_valid   = phonenumbers.is_valid_number(phone_obj)
        is_possible = phonenumbers.is_possible_number(phone_obj)

        result["validation"] = {
            "is_valid": is_valid,
            "is_possible": is_possible,
            "country_code": f"+{phone_obj.country_code}",
            "national_number": str(phone_obj.national_number),
        }

        result["formatted"] = {
            "e164":          phonenumbers.format_number(phone_obj, PhoneNumberFormat.E164),
            "international": phonenumbers.format_number(phone_obj, PhoneNumberFormat.INTERNATIONAL),
            "national":      phonenumbers.format_number(phone_obj, PhoneNumberFormat.NATIONAL),
            "rfc3966":       phonenumbers.format_number(phone_obj, PhoneNumberFormat.RFC3966),
        }

        num_type = phonenumbers.number_type(phone_obj)
        result["parsed"]["number_type"] = NUMBER_TYPES.get(num_type, "Unknown")

        # Carrier
        carrier_name = carrier.name_for_number(phone_obj, "en")
        result["carrier_info"] = {
            "carrier": carrier_name if carrier_name else "Not available",
        }

        # Geography
        geo_desc = geocoder.description_for_number(phone_obj, "en")
        result["location_info"] = {
            "region_description": geo_desc if geo_desc else "Not available",
            "country_code": f"+{phone_obj.country_code}",
            "country": COUNTRY_CODES.get(f"+{phone_obj.country_code}", "Unknown"),
        }

        # Timezones
        try:
            timezones = list(pn_timezone.time_zones_for_number(phone_obj))
            result["location_info"]["timezones"] = timezones
        except Exception:
            result["location_info"]["timezones"] = []

        # Risk indicators
        if not is_valid:
            result["risk_indicators"].append("✗ Number is INVALID according to ITU standards")
        if num_type == PhoneNumberType.VOIP:
            result["risk_indicators"].append("⚠ VOIP number — may be used to mask identity")
        if num_type == PhoneNumberType.TOLL_FREE:
            result["risk_indicators"].append("ℹ Toll-free number")
        if num_type == PhoneNumberType.PREMIUM_RATE:
            result["risk_indicators"].append("⚠ Premium-rate number — high call costs")

    except ImportError:
        # Fallback: basic parsing without phonenumbers library
        result["validation"] = _basic_validate(cleaned)
        result["formatted"] = {"e164": cleaned, "international": cleaned}
        result["additional_info"]["note"] = (
            "Install 'phonenumbers' for full carrier/location analysis: pip install phonenumbers"
        )

    except Exception as e:
        result["validation"]["error"] = str(e)
        logger.warning(f"phonenumbers parse error for '{number}': {e}")

    # ── NumVerify-style public enrichment (no key needed for basic info) ───────
    additional = _lookup_numinfo(cleaned)
    if additional:
        result["additional_info"].update(additional)

    # Flag suspicious patterns
    digits_only = re.sub(r"\D", "", cleaned)
    if len(set(digits_only)) <= 3:
        result["risk_indicators"].append("⚠ Suspicious pattern: very few unique digits")
    if re.search(r"(\d)\1{5,}", digits_only):
        result["risk_indicators"].append("⚠ Suspicious pattern: long repeating digit sequence")

    if not result["risk_indicators"]:
        result["risk_indicators"].append("✓ No obvious risk patterns detected")

    logger.info(f"Phone analysis complete for {number}")
    return result


def _basic_validate(cleaned: str) -> dict:
    """Minimal validation without phonenumbers library."""
    digits = re.sub(r"\D", "", cleaned)
    country = "Unknown"
    # Try to match country code
    for code, name in sorted(COUNTRY_CODES.items(), key=lambda x: -len(x[0])):
        num_code = code.replace("+", "")
        if digits.startswith(num_code):
            country = name
            break
    return {
        "is_valid": 7 <= len(digits) <= 15,
        "is_possible": 7 <= len(digits) <= 15,
        "country_code": cleaned[:3] if cleaned.startswith("+") else "Unknown",
        "national_number": digits[2:] if digits.startswith("1") else digits,
        "country": country,
        "digit_count": len(digits),
    }


def _lookup_numinfo(e164: str) -> dict:
    """Try a public phone info API (no key required)."""
    try:
        # Use the free phonenuminfo API
        url = f"https://phonevalidation.abstractapi.com/v1/?api_key=&phone={e164}"
        # This will fail without a key, but we handle gracefully
        resp = requests.get(
            f"https://api.telnyx.com/v2/number_lookup/{e164}",
            timeout=5,
            headers={"User-Agent": "ReconX/1.0"}
        )
        if resp.status_code == 200:
            data = resp.json()
            return {"telnyx_data": str(data)[:300]}
    except Exception:
        pass
    return {}
