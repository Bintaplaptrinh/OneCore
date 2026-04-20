"""Entity normalizer: Parse raw OCR text -> clean structured entities."""
import re
from unidecode import unidecode


# Noise patterns to remove from titles
NOISE_PATTERNS = [
    r'\b\d+\s*tầng\b',       # "16 tầng" -> extract to floors
    r'\bxây mới\b',           # -> status = "xây mới"
    r'\bhoàn thiện\b',        # -> status = "hoàn thiện"
    r'\bthô\b',               # -> status = "thô"
    r'\bxây dựng\b',
    r'\bđang xây\b',
    r'\bchưa xây\b',
    r'\bsắp xây\b',
]

TYPE_MAP = {
    'khách sạn': 'Khách sạn',
    'căn hộ': 'Căn hộ',
    'biệt thự': 'Biệt thự',
    'nhà phố': 'Nhà phố',
    'văn phòng': 'Văn phòng',
    'shophouse': 'Shophouse',
    'resort': 'Resort',
    'condotel': 'Condotel',
    'tòa nhà': 'Tòa nhà',
    'trung tâm thương mại': 'TTTM',
    'khu đô thị': 'KĐT',
    'khu công nghiệp': 'KCN',
}

PROVINCE_MAP = {
    'tp.hcm': 'Hồ Chí Minh',
    'tphcm': 'Hồ Chí Minh',
    'hcm': 'Hồ Chí Minh',
    'hn': 'Hà Nội',
    'hanoi': 'Hà Nội',
    'hà nội': 'Hà Nội',
    'dn': 'Đà Nẵng',
    'đà nẵng': 'Đà Nẵng',
    'hải phòng': 'Hải Phòng',
    'hp': 'Hải Phòng',
}


def clean_name(text: str) -> str:
    """Proper-case Vietnamese name, remove noise words."""
    if not text:
        return ""

    text = text.strip()

    # Remove noise patterns
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove parentheses content (already extracted)
    text = re.sub(r'\([^)]*\)', '', text)

    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Capitalize first letter of each word
    words = text.split()
    text = ' '.join(word[0].upper() + word[1:].lower() if word else '' for word in words)

    return text


def standardize_province(text: str) -> str:
    """Normalize province names."""
    if not text:
        return ""

    text = text.strip().lower()

    # Check direct mapping
    if text in PROVINCE_MAP:
        return PROVINCE_MAP[text]

    # Return original if no mapping found
    return text.title()


def slugify(text: str, prefix: str = "", separator: str = "-") -> str:
    """Generate slug: unidecode -> lowercase -> clean."""
    if not text:
        return prefix or "unknown"

    # Convert to ASCII
    text = unidecode(text).lower().strip()

    # Replace non-alphanumeric with separator
    text = re.sub(r'[^a-z0-9]+', separator, text)

    # Remove multiple separators
    text = re.sub(f'{re.escape(separator)}+', separator, text)

    # Strip separators from ends
    text = text.strip(separator)

    if prefix:
        text = f"{prefix}{separator}{text}" if text else prefix

    return text or "unknown"


def normalize_phone(phone: str) -> str:
    """Standardize VN phone numbers to 10-digit format."""
    if not phone:
        return ""

    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)

    # Handle 11-digit (leading 84)
    if len(digits) == 11 and digits.startswith('84'):
        digits = digits[2:]

    # Handle 10-digit VN numbers
    if len(digits) == 10:
        return digits

    # Return original if not standard
    return phone.strip()


def normalize_project_name(raw: str) -> dict:
    """
    Parse raw project text and return structured data.

    Returns: {name: str, attributes: {type, floors, status, ...}}

    Algorithm:
    1. Find parenthetical content: (NAME - PROVINCE) -> extract as clean name candidate
    2. Detect type from prefix (before first dash/bracket)
    3. Extract numeric floors: (\d+)\s*tầng
    4. Extract status keywords
    5. Clean the name: proper case, remove noise
    6. Return structured result
    """
    if not raw:
        return {"name": "", "attributes": {}}

    raw = raw.strip()
    attributes = {}

    # Step 1: Extract parenthetical content for name
    paren_match = re.search(r'\(([^)]+)\)', raw)
    parenthetical = paren_match.group(1) if paren_match else ""

    # Step 2: Detect project type from prefix
    project_type = None
    raw_lower = raw.lower()
    for key, val in TYPE_MAP.items():
        if raw_lower.startswith(key):
            project_type = val
            attributes['type'] = val
            break

    # Step 3: Extract floors
    floors_match = re.search(r'(\d+)\s*tầng', raw, re.IGNORECASE)
    if floors_match:
        attributes['floors'] = int(floors_match.group(1))

    # Step 4: Extract status
    status_keywords = ['xây mới', 'hoàn thiện', 'thô', 'đang xây', 'chưa xây', 'sắp xây']
    for keyword in status_keywords:
        if keyword.lower() in raw_lower:
            attributes['status'] = keyword
            break

    # Step 5: Determine clean name
    name = ""
    if parenthetical:
        # Use parenthetical as name base
        parts = [p.strip() for p in parenthetical.split('-')]
        if len(parts) >= 2:
            name = f"{parts[0]} - {parts[1]}"  # "Name - Province"
        else:
            name = parenthetical

    if not name:
        # Use prefix before first dash
        prefix = re.split(r'[-\(]', raw)[0].strip()
        name = clean_name(prefix)

    name = clean_name(name)

    return {
        "name": name,
        "attributes": attributes
    }


def normalize_entity_for_upsert(entity_type: str, data: dict) -> dict:
    """
    Clean and normalize any entity dict before upsert.
    - Projects: normalize name, province, standardize fields
    - Contacts: normalize phone, name casing
    - Companies: normalize name, generate entity_key

    Returns dict with entity_key and normalized fields.
    """
    data = dict(data)  # Make a copy

    if entity_type == "project":
        # Normalize name
        if "name" in data and data["name"]:
            data["name"] = clean_name(data["name"])

        # Normalize province
        if "province" in data and data["province"]:
            data["province"] = standardize_province(data["province"])

        # Normalize district
        if "district" in data and data["district"]:
            data["district"] = data["district"].strip()

        # Normalize address
        if "address" in data and data["address"]:
            data["address"] = data["address"].strip()

        # Ensure developer is a list
        if "developer" in data:
            dev = data["developer"]
            if isinstance(dev, str):
                data["developer"] = [dev.strip()] if dev.strip() else []
            elif isinstance(dev, list):
                data["developer"] = [str(d).strip() for d in dev if str(d).strip()]
            else:
                data["developer"] = []

        # Generate entity_key
        code = str(data.get("code") or "").strip()
        if code:
            data["entity_key"] = code
        else:
            name = str(data.get("name") or "")
            data["entity_key"] = slugify(name) if name else "unknown"

    elif entity_type == "contact":
        # Normalize name
        if "full_name" in data and data["full_name"]:
            data["full_name"] = clean_name(data["full_name"])
        elif "name" in data and data["name"]:
            data["full_name"] = clean_name(data["name"])
            data.pop("name", None)

        # Normalize phone
        if "phone" in data and data["phone"]:
            data["phone"] = normalize_phone(data["phone"])

        # Normalize email
        if "email" in data and data["email"]:
            data["email"] = data["email"].strip().lower()

        # Normalize company
        if "company" in data and data["company"]:
            data["company"] = clean_name(data["company"])

        # Normalize role
        if "role" in data and data["role"]:
            data["role"] = data["role"].strip()

        # Generate entity_key
        phone = str(data.get("phone") or "").strip()
        email = str(data.get("email") or "").strip()
        full_name = str(data.get("full_name") or "").strip()
        company = str(data.get("company") or "").strip()

        if phone:
            data["entity_key"] = phone
        elif email:
            data["entity_key"] = email
        else:
            combined = f"{full_name}-{company}" if company else full_name
            data["entity_key"] = slugify(combined) if combined else "unknown"

    elif entity_type == "company":
        # Normalize name
        if "name" in data and data["name"]:
            data["name"] = clean_name(data["name"])

        # Generate entity_key
        name = str(data.get("name") or "").strip()
        data["entity_key"] = slugify(name) if name else "unknown"

    return data
