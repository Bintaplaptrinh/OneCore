"""
LeadsMap Seed Script — Import toàn bộ dữ liệu từ Obsidian Vault vào MongoDB Atlas
Chạy: python seed_data.py

Nguồn dữ liệu: E:/PCDOC/bds/HaiVo LeadsMap/HaiVo LeadsMap/
  - 4_company/clients/   → 11 developer companies
  - 4_company/mc/        → 8 main contractors
  - 4_company/design/    → 8 design consultants
  - 1_project/           → 101 dự án
  - 2_contacts/          → 741 liên hệ
"""

import asyncio
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
VAULT_ROOT  = Path("E:/PCDOC/bds/HaiVo LeadsMap/HaiVo LeadsMap")
sys.path.insert(0, str(SCRIPT_DIR))

# Load .env
from dotenv import load_dotenv
load_dotenv(SCRIPT_DIR / ".env")

# ─── MongoDB ──────────────────────────────────────────────────────────────────
import motor.motor_asyncio
from pymongo import ASCENDING, TEXT
from pymongo.errors import DuplicateKeyError

MONGO_URI  = os.getenv("MONGO_URI", "")
MONGO_DB   = os.getenv("MONGO_DB_NAME", "leadsmap")

# ─── Helpers ──────────────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    """ASCII slug — dùng làm entity_key"""
    try:
        from unidecode import unidecode
        text = unidecode(str(text))
    except Exception:
        pass
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-") or "unknown"


def clean_phone(raw: str) -> str:
    """Chuẩn hóa số điện thoại VN → 10 chữ số"""
    digits = re.sub(r"[^\d+]", "", str(raw))
    if digits.startswith("+84"):
        digits = "0" + digits[3:]
    elif digits.startswith("84") and len(digits) >= 11:
        digits = "0" + digits[2:]
    return digits


def extract_inline(text: str, field: str) -> str:
    """Lấy giá trị từ 'Field:: value' (Obsidian inline format)"""
    m = re.search(rf"^{field}::\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ""
    val = m.group(1).strip()
    # Bỏ [[...]] wrapper
    val = re.sub(r"\[\[([^\]]*)\]\]", r"\1", val)
    return val.strip()


def extract_tags(text: str) -> list[str]:
    """Lấy tất cả #tag từ text"""
    return [t.lstrip("#") for t in re.findall(r"#([A-Za-z0-9_À-ỹ]+)", text)]


def extract_bullet_field(text: str, field: str) -> str:
    """Lấy giá trị từ '- field: value' trong project files"""
    m = re.search(rf"^-\s+{field}:\s+(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ""
    val = m.group(1).strip()
    val = re.sub(r"\[\[([^\]]*)\]\]", r"\1", val)
    return val.strip()


def extract_number(text: str) -> float | None:
    """Lấy số float từ chuỗi như '2899 m2', '21.847M USD', '43118 m2'"""
    m = re.search(r"([\d.,]+)\s*M?\s*(m2|USD|tỷ|billion)?", text, re.IGNORECASE)
    if not m:
        return None
    num_str = m.group(1).replace(",", ".")
    try:
        val = float(num_str)
        if "M" in text.upper() and "USD" in text.upper():
            val = val * 1_000_000  # M USD → USD
        return val
    except ValueError:
        return None


def clean_company_name(raw: str) -> str:
    """Bỏ prefix client-/mc-/consultant- từ company slug"""
    raw = re.sub(r"\[\[([^\]]*)\]\]", r"\1", raw)
    raw = raw.strip()
    # Tách sau dấu : nếu có (VD: client-TuVanGiamSat:MaceVietNam → MaceVietNam)
    if ":" in raw:
        raw = raw.split(":")[-1]
    # Bỏ prefix
    for prefix in ["client-", "mc-", "consultant-"]:
        if raw.lower().startswith(prefix):
            raw = raw[len(prefix):]
    # CamelCase → có khoảng trắng
    raw = re.sub(r"([a-z])([A-Z])", r"\1 \2", raw)
    return raw.strip()


# ─── Parsers ──────────────────────────────────────────────────────────────────

def parse_company_file(path: Path) -> dict | None:
    """Parse file company (client/mc/consultant)"""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    # Lấy tên từ heading # hoặc từ tên file
    name_m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if name_m:
        raw_name = name_m.group(1).strip()
    else:
        raw_name = path.stem.strip("[]")

    display_name = clean_company_name(raw_name)
    if not display_name or display_name == "unknown":
        return None

    company_type = extract_inline(text, "Type")
    segments     = extract_tags(extract_inline(text, "Segment") or text)

    # Xác định loại từ tên file + tags
    fname = path.stem.lower()
    if "client" in fname:
        cat = "developer"
    elif "mc-" in fname or "maincontractor" in company_type.lower():
        cat = "maincontractor"
    elif "consultant" in fname or "consultant" in company_type.lower():
        cat = "consultant"
    else:
        cat = company_type.lower() or "company"

    return {
        "name":       display_name,
        "entity_key": slugify(display_name),
        "type":       cat,
        "segments":   [s for s in segments if s not in ("company","developer","maincontractor","consultant","contacts")],
        "source_file": path.name,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def parse_project_file(path: Path) -> dict | None:
    """Parse file dự án từ 1_project/"""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    # Lấy code từ [[prj-Code]]
    code_m = re.search(r"\[\[prj-([^\]]+)\]\]", text)
    if not code_m:
        # Thử lấy từ tên file
        fname = re.sub(r"2026\s*-\s*", "", path.stem).strip("[]")
        code_m2 = re.match(r"prj-(.+)", fname)
        code = fname if not code_m2 else fname
    else:
        code = "prj-" + code_m.group(1)

    # Tên display: CamelCase → readable
    raw_code = code.replace("prj-", "")
    display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", raw_code)
    # Capitalize từng chữ
    display_name = display_name.title()

    # Type tags
    type_m = re.search(r"^type:\s*(.+)$", text, re.MULTILINE)
    types  = extract_tags(type_m.group(1)) if type_m else []

    # Location tags
    loc_m = re.search(r"^location:\s*(.+)$", text, re.MULTILINE)
    locations = extract_tags(loc_m.group(1)) if loc_m else []

    # Province từ location tags
    province_map = {
        "HoChiMinh": "Hồ Chí Minh", "Quan1": "Hồ Chí Minh", "BinhTan": "Hồ Chí Minh",
        "Quan2": "Hồ Chí Minh", "Quan7": "Hồ Chí Minh", "Quan9": "Hồ Chí Minh",
        "QuanBinhTan": "Hồ Chí Minh", "ThuDuc": "Hồ Chí Minh", "BinhChanh": "Hồ Chí Minh",
        "HaNoi": "Hà Nội", "HaNoiTuyenQuang": "Hà Nội", "LongBien": "Hà Nội",
        "CauGiay": "Hà Nội", "TrungVan": "Hà Nội",
        "Danang": "Đà Nẵng", "DaNang": "Đà Nẵng",
        "KhanhHoa": "Khánh Hòa", "TPNhaTrang": "Khánh Hòa",
        "HungYen": "Hưng Yên", "BinhDuong": "Bình Dương",
        "CanTho": "Cần Thơ", "HaiPhong": "Hải Phòng",
        "LongAn": "Long An", "QuyNhon": "Bình Định",
        "PhuYen": "Phú Yên", "VungTau": "Bà Rịa - Vũng Tàu",
    }
    province = ""
    for loc in locations:
        if loc in province_map:
            province = province_map[loc]
            break

    # Developers — lấy tất cả [[client-...]]
    dev_matches = re.findall(r"\[\[client-([^\]#]+)\]\]", text)
    developers = list(dict.fromkeys([  # unique, preserve order
        clean_company_name("client-" + d.split("#")[0].strip())
        for d in dev_matches
    ]))

    # Site info
    address     = extract_bullet_field(text, "address")
    land_area_s = extract_bullet_field(text, "land_area")
    floor_area_s= extract_bullet_field(text, "floor_area")
    floors_s    = extract_bullet_field(text, "floors")

    # Timeline
    groundbreaking    = extract_bullet_field(text, "groundbreaking")
    expected_handover = extract_bullet_field(text, "expected_handover")
    status            = extract_bullet_field(text, "status")
    phase             = extract_bullet_field(text, "phase")

    # Scale
    value_s   = extract_bullet_field(text, "value_usd")
    dev_type  = extract_bullet_field(text, "dev_type")
    owner_type= extract_bullet_field(text, "owner_type")

    # Notes
    notes_m = re.search(r"^notes:\n((?:- .+\n?)*)", text, re.MULTILINE)
    notes = ""
    if notes_m:
        notes = re.sub(r"^-\s+", "", notes_m.group(1)).strip()

    # Parse numbers
    land_area  = extract_number(land_area_s)
    floor_area = extract_number(floor_area_s)
    floors_n   = extract_number(floors_s)
    value_usd  = extract_number(value_s) if value_s else None

    # Tính value_billion_vnd ≈ value_usd / 1e6 * 25000 (rough)
    value_billion_vnd = None
    if value_usd:
        value_billion_vnd = round(value_usd * 25000 / 1e9, 3)

    return {
        "code":              code,
        "entity_key":        slugify(code),
        "name":              display_name,
        "province":          province,
        "district":          "",
        "address":           address,
        "developer":         developers,
        "category":          types[0] if types else "",
        "build_type":        ", ".join(types),
        "status":            status,
        "design_stage":      phase,
        "area_sqm":          land_area,
        "floor_area":        floor_area,
        "floors":            int(floors_n) if floors_n else None,
        "start_date":        groundbreaking,
        "end_date":          expected_handover,
        "value_billion_vnd": value_billion_vnd,
        "value_usd":         value_usd,
        "dev_type":          dev_type,
        "owner_type":        owner_type,
        "description":       notes[:2000] if notes else "",
        "type_tags":         types,
        "location_tags":     locations,
        "source_file":       path.name,
        "created_at":        datetime.utcnow(),
        "updated_at":        datetime.utcnow(),
    }


def parse_contact_file(path: Path) -> dict | None:
    """Parse file liên hệ từ 2_contacts/"""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    # Tên từ heading # Name
    name_m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if not name_m:
        # Lấy từ tên file: "Name_Company.md"
        stem = path.stem
        full_name = stem.split("_")[0].strip() if "_" in stem else stem
    else:
        full_name = name_m.group(1).strip()

    # Bỏ qua nếu tên rỗng hoặc là template
    if not full_name or full_name.lower() in ("contact", "template", "contacts"):
        return None

    company_raw = extract_inline(text, "Company")
    company     = clean_company_name(company_raw) if company_raw else ""

    role     = extract_inline(text, "Role")
    email    = extract_inline(text, "Email")
    phone_raw= extract_inline(text, "Phone")
    location = extract_inline(text, "Location")
    website  = extract_inline(text, "Website")

    # Xử lý nhiều số điện thoại (VD: "090 1234567\n091 7654321")
    phones = []
    for p in re.split(r"[\n,;|]", phone_raw):
        p = p.strip()
        if p:
            cleaned = clean_phone(p)
            if len(cleaned) >= 8:
                phones.append(cleaned)

    phone = phones[0] if phones else ""

    # entity_key ưu tiên: phone → email → slug(name+company)
    if phone and len(phone) >= 9:
        entity_key = phone
    elif email and "@" in email:
        entity_key = email.lower().strip()
    else:
        entity_key = slugify(full_name + ("-" + company if company else ""))

    return {
        "full_name":   full_name,
        "entity_key":  entity_key,
        "company":     company,
        "role":        role,
        "email":       email.lower().strip() if email else "",
        "phone":       phone,
        "phones":      phones,
        "address":     location,
        "website":     website,
        "source_file": path.name,
        "created_at":  datetime.utcnow(),
        "updated_at":  datetime.utcnow(),
    }


# ─── Main Seed ────────────────────────────────────────────────────────────────

async def seed():
    print("=" * 60)
    print("  LeadsMap Seed — Import dữ liệu từ Obsidian Vault")
    print("=" * 60)
    print(f"  MongoDB: {MONGO_DB}")
    print(f"  Vault:   {VAULT_ROOT}")
    print()

    if not MONGO_URI:
        print("LỖI: MONGO_URI chưa được cài đặt trong .env")
        return

    # Connect
    client = motor.motor_asyncio.AsyncIOMotorClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
    )
    db = client[MONGO_DB]

    try:
        await db.command("ping")
        print("  ✓ Kết nối MongoDB Atlas thành công")
    except Exception as e:
        print(f"  ✗ Không kết nối được MongoDB: {e}")
        print()
        print("  Kiểm tra:")
        print("  1. MONGO_URI trong file .env")
        print("  2. IP của máy bạn đã được thêm vào MongoDB Atlas Network Access")
        print("     → https://cloud.mongodb.com → Network Access → Add IP Address")
        client.close()
        return

    # Tạo indexes
    print("  Tạo indexes...")
    for coll, field in [("projects","entity_key"), ("contacts","entity_key"), ("companies","entity_key")]:
        try:
            await db[coll].create_index([(field, ASCENDING)], unique=True, sparse=True)
        except Exception:
            pass
    try:
        await db["relationships"].create_index([("unique_key", ASCENDING)], unique=True, sparse=True)
    except Exception:
        pass

    stats = {
        "companies": {"new": 0, "skip": 0, "err": 0},
        "projects":  {"new": 0, "skip": 0, "err": 0},
        "contacts":  {"new": 0, "skip": 0, "err": 0},
        "relationships": {"new": 0, "skip": 0},
    }

    # ── 1. COMPANIES ──────────────────────────────────────────────────────────
    print()
    print("── [1/3] Import Công ty ──────────────────────────────────")

    company_dirs = [
        VAULT_ROOT / "4_company" / "clients",
        VAULT_ROOT / "4_company" / "mc",
        VAULT_ROOT / "4_company" / "design",
    ]
    company_name_to_id: dict[str, str] = {}  # entity_key → _id str

    for cdir in company_dirs:
        for md_file in sorted(cdir.glob("*.md")):
            data = parse_company_file(md_file)
            if not data:
                continue
            try:
                result = await db.companies.update_one(
                    {"entity_key": data["entity_key"]},
                    {"$set": data},
                    upsert=True,
                )
                if result.upserted_id:
                    doc_id = str(result.upserted_id)
                    stats["companies"]["new"] += 1
                    print(f"  + {data['name']} ({data['type']})")
                else:
                    existing = await db.companies.find_one({"entity_key": data["entity_key"]}, {"_id": 1})
                    doc_id = str(existing["_id"]) if existing else data["entity_key"]
                    stats["companies"]["skip"] += 1
                company_name_to_id[data["entity_key"]] = doc_id
                # Alias: tên gốc để lookup từ contacts/projects
                company_name_to_id[data["name"].lower()] = doc_id
            except Exception as e:
                stats["companies"]["err"] += 1
                print(f"  ✗ {data.get('name', '?')}: {e}")

    print(f"  → {stats['companies']['new']} mới, {stats['companies']['skip']} đã có, {stats['companies']['err']} lỗi")

    # ── 2. PROJECTS ───────────────────────────────────────────────────────────
    print()
    print("── [2/3] Import Dự án ────────────────────────────────────")

    project_dir = VAULT_ROOT / "1_project"
    project_id_map: dict[str, str] = {}  # entity_key → _id str

    for md_file in sorted(project_dir.glob("*.md")):
        data = parse_project_file(md_file)
        if not data:
            continue
        try:
            result = await db.projects.update_one(
                {"entity_key": data["entity_key"]},
                {"$set": data},
                upsert=True,
            )
            if result.upserted_id:
                doc_id = str(result.upserted_id)
                stats["projects"]["new"] += 1
                print(f"  + {data['name']} ({data['province'] or '?'}) [{data['category']}]")
            else:
                existing = await db.projects.find_one({"entity_key": data["entity_key"]}, {"_id": 1})
                doc_id = str(existing["_id"]) if existing else data["entity_key"]
                stats["projects"]["skip"] += 1
            project_id_map[data["entity_key"]] = doc_id

            # Tạo quan hệ project → company (owner)
            for dev_name in data.get("developer", []):
                if not dev_name:
                    continue
                dev_key = slugify(dev_name)
                co_id = company_name_to_id.get(dev_key) or company_name_to_id.get(dev_name.lower())
                if not co_id:
                    # Tạo company mới nếu chưa có
                    co_data = {
                        "name": dev_name,
                        "entity_key": dev_key,
                        "type": "developer",
                        "segments": [],
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                    try:
                        co_res = await db.companies.update_one(
                            {"entity_key": dev_key},
                            {"$set": co_data},
                            upsert=True,
                        )
                        if co_res.upserted_id:
                            co_id = str(co_res.upserted_id)
                            stats["companies"]["new"] += 1
                        else:
                            co_doc = await db.companies.find_one({"entity_key": dev_key}, {"_id": 1})
                            co_id = str(co_doc["_id"]) if co_doc else None
                        if co_id:
                            company_name_to_id[dev_key] = co_id
                            company_name_to_id[dev_name.lower()] = co_id
                    except Exception:
                        pass

                if co_id:
                    ukey = f"{doc_id}_{co_id}_owner"
                    try:
                        rel_res = await db.relationships.update_one(
                            {"unique_key": ukey},
                            {"$setOnInsert": {
                                "source_id": doc_id, "source_type": "project",
                                "target_id": co_id,  "target_type": "company",
                                "role_type":  "owner",
                                "unique_key": ukey,
                                "created_at": datetime.utcnow(),
                            }},
                            upsert=True,
                        )
                        if rel_res.upserted_id:
                            stats["relationships"]["new"] += 1
                        else:
                            stats["relationships"]["skip"] += 1
                    except Exception:
                        pass

        except Exception as e:
            stats["projects"]["err"] += 1
            print(f"  ✗ {data.get('name', '?')}: {e}")

    print(f"  → {stats['projects']['new']} mới, {stats['projects']['skip']} đã có, {stats['projects']['err']} lỗi")

    # ── 3. CONTACTS ───────────────────────────────────────────────────────────
    print()
    print("── [3/3] Import Liên hệ ──────────────────────────────────")
    print("  (741 file — có thể mất 30-60 giây...)")

    contact_dir = VAULT_ROOT / "2_contacts"
    batch_size  = 50
    contact_files = sorted(contact_dir.glob("*.md"))
    total = len(contact_files)
    dot_every = max(1, total // 20)

    for i, md_file in enumerate(contact_files):
        data = parse_contact_file(md_file)
        if not data:
            stats["contacts"]["skip"] += 1
            continue

        try:
            result = await db.contacts.update_one(
                {"entity_key": data["entity_key"]},
                {"$set": data},
                upsert=True,
            )
            if result.upserted_id:
                con_id = str(result.upserted_id)
                stats["contacts"]["new"] += 1
            else:
                existing = await db.contacts.find_one({"entity_key": data["entity_key"]}, {"_id": 1})
                con_id = str(existing["_id"]) if existing else None
                stats["contacts"]["skip"] += 1

            # Quan hệ contact → company (works_at)
            if con_id and data.get("company"):
                co_key = slugify(data["company"])
                co_id  = company_name_to_id.get(co_key) or company_name_to_id.get(data["company"].lower())

                if not co_id:
                    # Tự động tạo company nếu chưa có
                    co_data = {
                        "name":       data["company"],
                        "entity_key": co_key,
                        "type":       "company",
                        "segments":   [],
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                    try:
                        co_res = await db.companies.update_one(
                            {"entity_key": co_key},
                            {"$set": co_data},
                            upsert=True,
                        )
                        if co_res.upserted_id:
                            co_id = str(co_res.upserted_id)
                            stats["companies"]["new"] += 1
                        else:
                            co_doc = await db.companies.find_one({"entity_key": co_key}, {"_id": 1})
                            co_id = str(co_doc["_id"]) if co_doc else None
                        if co_id:
                            company_name_to_id[co_key] = co_id
                            company_name_to_id[data["company"].lower()] = co_id
                    except Exception:
                        pass

                if co_id:
                    ukey = f"{con_id}_{co_id}_works_at"
                    try:
                        rel_res = await db.relationships.update_one(
                            {"unique_key": ukey},
                            {"$setOnInsert": {
                                "source_id": con_id, "source_type": "contact",
                                "target_id": co_id,  "target_type": "company",
                                "role_type":  "works_at",
                                "unique_key": ukey,
                                "created_at": datetime.utcnow(),
                            }},
                            upsert=True,
                        )
                        if rel_res.upserted_id:
                            stats["relationships"]["new"] += 1
                        else:
                            stats["relationships"]["skip"] += 1
                    except Exception:
                        pass

        except Exception as e:
            stats["contacts"]["err"] += 1

        # Progress dots
        if (i + 1) % dot_every == 0:
            pct = int((i + 1) / total * 100)
            done = stats["contacts"]["new"]
            print(f"  [{pct:3}%] {i+1}/{total} files — {done} liên hệ mới", end="\r", flush=True)

    print(f"  → {stats['contacts']['new']} mới, {stats['contacts']['skip']} đã có/trùng, {stats['contacts']['err']} lỗi         ")

    # ── Kết quả ───────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  KẾT QUẢ IMPORT")
    print("=" * 60)

    # Đếm thực tế trong DB
    n_proj  = await db.projects.count_documents({})
    n_con   = await db.contacts.count_documents({})
    n_co    = await db.companies.count_documents({})
    n_rel   = await db.relationships.count_documents({})

    print(f"  Dự án:    {stats['projects']['new']:4d} mới  (tổng trong DB: {n_proj})")
    print(f"  Liên hệ:  {stats['contacts']['new']:4d} mới  (tổng trong DB: {n_con})")
    print(f"  Công ty:  {stats['co_total'] if 'co_total' in stats else stats['companies']['new']:4d} mới  (tổng trong DB: {n_co})")
    print(f"  Quan hệ:  {stats['relationships']['new']:4d} mới  (tổng trong DB: {n_rel})")
    print()

    # Top provinces
    pipeline = [
        {"$group": {"_id": "$province", "count": {"$sum": 1}}},
        {"$sort":  {"count": -1}},
        {"$limit": 8},
    ]
    provinces = await db.projects.aggregate(pipeline).to_list(8)
    if provinces:
        print("  Dự án theo tỉnh/thành:")
        for p in provinces:
            if p["_id"]:
                print(f"    {p['_id']:25s}: {p['count']} dự án")

    print()
    print("  ✓ Import hoàn tất! Truy cập http://localhost:3000 để xem.")
    print()
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
