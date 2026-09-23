"""
ReconX – Image Metadata Extractor Module
Extracts EXIF and file metadata from uploaded images.
"""

import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("metadata_extractor")

# Tag name translations for readability
FRIENDLY_TAGS = {
    "GPSInfo":                  "GPS Information",
    "DateTimeOriginal":         "Date/Time Original",
    "DateTimeDigitized":        "Date/Time Digitized",
    "Make":                     "Camera Make",
    "Model":                    "Camera Model",
    "Software":                 "Software",
    "Orientation":              "Orientation",
    "XResolution":              "X Resolution",
    "YResolution":              "Y Resolution",
    "Flash":                    "Flash",
    "FocalLength":              "Focal Length",
    "ExposureTime":             "Exposure Time",
    "FNumber":                  "F-Number",
    "ISOSpeedRatings":          "ISO Speed",
    "LightSource":              "Light Source",
    "MeteringMode":             "Metering Mode",
    "WhiteBalance":             "White Balance",
    "ExposureProgram":          "Exposure Program",
    "ExifImageWidth":           "Image Width (EXIF)",
    "ExifImageHeight":          "Image Height (EXIF)",
    "ExifVersion":              "EXIF Version",
    "ColorSpace":               "Color Space",
    "SubjectDistance":          "Subject Distance",
    "SceneCaptureType":         "Scene Capture Type",
    "Artist":                   "Artist/Author",
    "Copyright":                "Copyright",
    "ImageDescription":         "Image Description",
    "UserComment":              "User Comment",
    "HostComputer":             "Host Computer",
    "DocumentName":             "Document Name",
    "PageName":                 "Page Name",
    "ProcessingSoftware":       "Processing Software",
    "LensMake":                 "Lens Make",
    "LensModel":                "Lens Model",
}


def extract_metadata(filepath: str) -> dict:
    """
    Extract metadata from an image file.

    Args:
        filepath: Path to the image file.

    Returns:
        A structured dict containing file info, EXIF data, and GPS coordinates.
    """
    result = {
        "file_info": {},
        "exif_data": {},
        "gps_data": {},
        "risk_notes": [],
    }

    if not os.path.exists(filepath):
        result["error"] = "File not found."
        return result

    # Basic file info
    stat = os.stat(filepath)
    result["file_info"] = {
        "filename": os.path.basename(filepath),
        "full_path": filepath,
        "size_bytes": stat.st_size,
        "size_kb": round(stat.st_size / 1024, 2),
        "last_modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "extension": os.path.splitext(filepath)[1].lower(),
    }

    # EXIF extraction using Pillow
    try:
        from PIL import Image, ExifTags
        with Image.open(filepath) as img:
            result["file_info"]["format"] = img.format
            result["file_info"]["mode"] = img.mode
            result["file_info"]["width_px"] = img.width
            result["file_info"]["height_px"] = img.height

            raw_exif = img._getexif()
            if raw_exif:
                for tag_id, value in raw_exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    if tag_name == "GPSInfo":
                        gps = _parse_gps(value)
                        result["gps_data"] = gps
                    else:
                        # Convert IFDRational and bytes to readable strings
                        try:
                            if isinstance(value, bytes):
                                value = value.decode("utf-8", errors="ignore").strip()
                            else:
                                value = str(value)
                        except Exception:
                            value = repr(value)
                        friendly = FRIENDLY_TAGS.get(tag_name, tag_name)
                        result["exif_data"][friendly] = value
            else:
                result["exif_data"]["note"] = "No EXIF data found in this image."

    except ImportError:
        result["error"] = "Pillow library not installed. Run: pip install Pillow"
    except Exception as e:
        logger.error(f"EXIF extraction error: {e}")
        result["exif_error"] = str(e)

    # Risk analysis
    if result["gps_data"].get("latitude") and result["gps_data"].get("longitude"):
        result["risk_notes"].append(
            "⚠ GPS coordinates found! Location data is embedded in this image."
        )
        lat = result["gps_data"]["latitude"]
        lon = result["gps_data"]["longitude"]
        result["gps_data"]["google_maps_url"] = f"https://www.google.com/maps?q={lat},{lon}"

    camera = result["exif_data"].get("Camera Make", "")
    if camera:
        result["risk_notes"].append(f"ℹ Image was captured with: {camera} {result['exif_data'].get('Camera Model', '')}")

    dt_orig = result["exif_data"].get("Date/Time Original", "")
    if dt_orig:
        result["risk_notes"].append(f"ℹ Original capture time: {dt_orig}")

    if not result["risk_notes"]:
        result["risk_notes"].append("✓ No sensitive metadata detected.")

    logger.info(f"Metadata extraction complete: {os.path.basename(filepath)}")
    return result


def _parse_gps(gps_info: dict) -> dict:
    """Parse raw GPSInfo EXIF dict into decimal coordinates."""
    try:
        from PIL import ExifTags
        gps_tags = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_info.items()}

        def to_decimal(values, ref):
            d, m, s = float(values[0]), float(values[1]), float(values[2])
            decimal = d + m / 60.0 + s / 3600.0
            if ref in ("S", "W"):
                decimal = -decimal
            return round(decimal, 7)

        lat = to_decimal(gps_tags.get("GPSLatitude", (0, 0, 0)), gps_tags.get("GPSLatitudeRef", "N"))
        lon = to_decimal(gps_tags.get("GPSLongitude", (0, 0, 0)), gps_tags.get("GPSLongitudeRef", "E"))
        alt_raw = gps_tags.get("GPSAltitude")
        alt = round(float(alt_raw), 2) if alt_raw else None

        return {
            "latitude": lat,
            "longitude": lon,
            "altitude_m": alt,
            "lat_ref": gps_tags.get("GPSLatitudeRef", ""),
            "lon_ref": gps_tags.get("GPSLongitudeRef", ""),
        }
    except Exception as e:
        return {"parse_error": str(e)}
