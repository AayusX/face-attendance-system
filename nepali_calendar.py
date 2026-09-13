from datetime import date, datetime

from nepali_datetime import date as _NepaliDate

NEPALI_MONTHS = (
    "Baisakh", "Jestha", "Asar", "Shrawan", "Bhadra", "Ashwin",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra",
)
NEPALI_WEEKDAYS = (
    "Aaitabar", "Sombar", "Mangalbar", "Budhbar", "Bihibar", "Shukrabar", "Sanibar",
)


def bs_date_from_ad(value):
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, str):
        value = _as_date(value)
    if value is None:
        return None
    try:
        return _NepaliDate.from_datetime_date(value)
    except Exception:
        return None


def to_bs_str(value):
    nd = bs_date_from_ad(value)
    return nd.isoformat() if nd is not None else (value.isoformat() if hasattr(value, "isoformat") else str(value))


def today_bs():
    return _NepaliDate.today().isoformat()


def today_bs_display():
    nd = _NepaliDate.today()
    month = NEPALI_MONTHS[nd.month - 1]
    weekday = NEPALI_WEEKDAYS[nd.weekday()]
    return f"{weekday}, {month} {nd.day}, {nd.year} BS"


def ad_from_bs(value):
    if value is None:
        return None
    text = str(value).strip()
    try:
        return _NepaliDate(*(int(part) for part in text.split("-")[:3])).to_datetime_date()
    except Exception:
        return None


def _as_date(text):
    text = str(text).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None