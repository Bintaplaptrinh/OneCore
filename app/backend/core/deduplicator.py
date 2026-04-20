"""Fuzzy matching to prevent duplicate entities."""
from rapidfuzz import fuzz, process
from core.database import get_db


async def find_duplicate_project(name: str, province: str = "", threshold: int = 85) -> dict | None:
    """
    Fuzzy match against existing projects by name+province.
    Returns existing project dict if duplicate found, else None.
    Uses rapidfuzz token_sort_ratio.
    """
    if not name or not name.strip():
        return None

    db = await get_db()

    # Build query for candidates
    query = {}
    if province and province.strip():
        query["province"] = {"$regex": province, "$options": "i"}

    try:
        candidates = await db["projects"].find(query, {"name": 1, "_id": 1, "entity_key": 1}).limit(500).to_list(500)

        if not candidates:
            return None

        names = [c.get("name", "") for c in candidates]
        if not names:
            return None

        match, score, idx = process.extractOne(name, names, scorer=fuzz.token_sort_ratio)

        if score >= threshold:
            return candidates[idx]

        return None

    except Exception as e:
        print(f"[find_duplicate_project] Error: {e}")
        return None


async def find_duplicate_contact(
    phone: str = "",
    email: str = "",
    full_name: str = "",
    company: str = "",
    threshold: int = 90
) -> dict | None:
    """Exact match on phone/email, fuzzy on name+company."""
    db = await get_db()

    # Exact match on phone
    if phone and phone.strip():
        try:
            result = await db["contacts"].find_one({"phone": phone.strip()})
            if result:
                return result
        except Exception as e:
            print(f"[find_duplicate_contact] Phone lookup error: {e}")

    # Exact match on email
    if email and email.strip():
        try:
            email_lower = email.strip().lower()
            result = await db["contacts"].find_one({"email": {"$regex": f"^{email_lower}$", "$options": "i"}})
            if result:
                return result
        except Exception as e:
            print(f"[find_duplicate_contact] Email lookup error: {e}")

    # Fuzzy match on name + company
    if full_name and full_name.strip():
        try:
            query = {}
            if company and company.strip():
                query["company"] = {"$regex": company, "$options": "i"}

            candidates = await db["contacts"].find(query, {"full_name": 1, "_id": 1, "entity_key": 1}).limit(200).to_list(200)

            if not candidates:
                return None

            names = [c.get("full_name", "") for c in candidates]
            if not names:
                return None

            match, score, idx = process.extractOne(full_name, names, scorer=fuzz.token_sort_ratio)

            if score >= threshold:
                return candidates[idx]

        except Exception as e:
            print(f"[find_duplicate_contact] Fuzzy match error: {e}")

    return None


async def find_duplicate_company(name: str, threshold: int = 88) -> dict | None:
    """Fuzzy match on company name."""
    if not name or not name.strip():
        return None

    db = await get_db()

    try:
        candidates = await db["companies"].find({}, {"name": 1, "_id": 1, "entity_key": 1}).limit(300).to_list(300)

        if not candidates:
            return None

        names = [c.get("name", "") for c in candidates]
        if not names:
            return None

        match, score, idx = process.extractOne(name, names, scorer=fuzz.token_sort_ratio)

        if score >= threshold:
            return candidates[idx]

        return None

    except Exception as e:
        print(f"[find_duplicate_company] Error: {e}")
        return None
