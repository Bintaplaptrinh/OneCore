"""HaiVo LeadsMap — Conversational RAG Engine (MUTATE scope added)."""
from __future__ import annotations
import json as _json, re
from typing import Optional
from core.ai_client import get_ai_client
from core.graphrag_client import get_graphrag_client
from unidecode import unidecode

_IDENTITY = """BẠN LÀ Leadmap AI – trợ lý thông minh của hệ thống LeadsMap bất động sản.  
Tính cách: thân thiện, tự nhiên, thông minh.  
Ngôn ngữ: tiếng Việt là chính; dùng tiếng Anh nếu người dùng hỏi bằng tiếng Anh.  
ĐỊNH DẠNG: KHÔNG dùng ký hiệu LaTeX ($...$ → v.v.) — dùng Unicode thuần: ->, x, <=, >.
 ($...$ \\rightarrow v.v.) — dùng Unicode thuần: -> x <= >="""

_VN_GEO = """ĐỊA LÝ VIỆT NAM: 5 THÀNH PHỐ trực thuộc Trung ương (KHÔNG phải tỉnh): Hà Nội, TP.HCM, Đà Nẵng, Hải Phòng, Cần Thơ.  
Khi người dùng nói TP.HCM/Sài Gòn -> province = "Ho Chi Minh". KHÔNG gọi các thành phố này là tỉnh.
"""

CHAT_SYSTEM = f"""{_IDENTITY}\n\n{_VN_GEO}\n\nTro chuyen tu nhien, phan tich, lap luan. Nho lich su hoi thoai. Dung Markdown."""

DATA_SYSTEM = f"""{_IDENTITY}\n\n{_VN_GEO}\n\nUu tien du lieu he thong. Duoc suy luan, phan tich. \nDINH DANG: danh sach->table, quan he->Mermaid, so lieu->CHART_DATA."""

SEARCH_SYSTEM = f"""{_IDENTITY}\n\n{_VN_GEO}\n\nTong hop tu ket qua web. Suc tich, trong tam. Ghi nguon: > Nguon: [Ten](URL)"""

# === STYLE: "Chinh xac" — anti-hallucination, strict grounding ===
_PRECISE_RULES = """NGUYÊN TẮC TUYỆT ĐỐI (zero-hallucination):
- KHÔNG bịa đặt, KHÔNG suy đoán, KHÔNG sáng tác số liệu/tên riêng/ngày tháng.
- Chỉ trả lời dựa TRÊN dữ liệu/ngữ cảnh được cung cấp trong cuộc hội thoại này.
- Nếu dữ liệu không có hoặc không đủ → trả lời RÕ RÀNG: "Tôi không có dữ liệu về thông tin này" hoặc "Dữ liệu hệ thống chưa có thông tin để trả lời câu hỏi này."
- KHÔNG điền thông tin ngoài phạm vi dữ liệu. KHÔNG đưa ra phỏng đoán kiểu "có thể là", "có lẽ", "thường là".
- Nếu được yêu cầu so sánh/thống kê nhưng dữ liệu thiếu → chỉ nêu số liệu có thật, kèm chú thích "dữ liệu không đầy đủ".
- Khi trích dẫn: chỉ trích từ ngữ cảnh thật sự xuất hiện. KHÔNG chế thêm nguồn/URL giả.
"""

CHAT_SYSTEM_PRECISE = f"""{_IDENTITY}\n\n{_VN_GEO}\n\n{_PRECISE_RULES}\n\nTra loi ngan gon, chinh xac. Neu cau hoi can du lieu he thong ma ban khong co -> noi ro can chuyen sang truy van du lieu. Dung Markdown."""

DATA_SYSTEM_PRECISE = f"""{_IDENTITY}\n\n{_VN_GEO}\n\n{_PRECISE_RULES}\n\nCHI su dung du lieu trong [DU LIEU GRAPH]/[BAO CAO]. KHONG suy luan vuot du lieu. \nNeu truong/gia tri khong co trong du lieu -> ghi "khong co du lieu" thay vi doan. \nDINH DANG: danh sach->table, quan he->Mermaid, so lieu->CHART_DATA."""

SEARCH_SYSTEM_PRECISE = f"""{_IDENTITY}\n\n{_VN_GEO}\n\n{_PRECISE_RULES}\n\nCHI tong hop tu [KET QUA WEB] duoc cung cap. KHONG them thong tin ngoai ket qua tim kiem. \nMoi cau khang dinh phai trich tu mot ket qua cu the. Ghi nguon: > Nguon: [Ten](URL)"""


def _systems_for(style: str) -> tuple[str, str, str]:
    """Return (chat, data, search) system prompts for the requested style."""
    if str(style or "").strip().lower() in ("precise", "chinh xac", "chính xác"):
        return CHAT_SYSTEM_PRECISE, DATA_SYSTEM_PRECISE, SEARCH_SYSTEM_PRECISE
    return CHAT_SYSTEM, DATA_SYSTEM, SEARCH_SYSTEM

MUTATE_PARSE_SYSTEM = _IDENTITY + """\n\nNhiệm vụ: phân tích yêu cầu thêm/sửa/xóa dữ liệu. Chỉ trả về JSON thuần.\n
Schema: {"operation":"insert|update|delete","entity":"project|contact","display_name":"...","slug":"entity_key neu biet","data":{"field":"value"},"changes":{"field":{"old":"...","new":"..."}},"summary":"..."}\n
data cho project: name,province,district,address,developer(list),value_billion_vnd,status,phase,type_tags(list),site_area,floors,groundbreaking,handover,notes\n
data cho contact: name,company,role,phone,email,address,notes\n
insert: điền đầy đủ các trường, slug để trống. update: chỉ trường thay đổi. delete: chỉ display_name+slug."""

LOCAL_PROMPT = "[CAU HOI]\n{query}\n\n[DU LIEU GRAPH]\n{context}\n\nTra loi dua tren du lieu. Duoc suy luan. danh sach->table, quan he->Mermaid."
GLOBAL_PROMPT = "[CAU HOI]\n{query}\n\n[BAO CAO]\n{context}\n\nPhan tich va tra loi. thong ke->bang, so sanh->bang STT."
SEARCH_PROMPT = "[CAU HOI]\n{query}\n\n[KET QUA WEB]\n{context}\n\nTong hop va tra loi."

PROVINCE_MAP = {
    "ha noi":"Ha Noi","hn":"Ha Noi","thanh pho ha noi":"Ha Noi","tp ha noi":"Ha Noi",
    "ho chi minh":"Ho Chi Minh","tp.hcm":"Ho Chi Minh","tphcm":"Ho Chi Minh","hcm":"Ho Chi Minh",
    "sai gon":"Ho Chi Minh","thanh pho ho chi minh":"Ho Chi Minh","tp ho chi minh":"Ho Chi Minh",
    "da nang":"Da Nang","thanh pho da nang":"Da Nang",
    "hai phong":"Hai Phong","thanh pho hai phong":"Hai Phong",
    "can tho":"Can Tho","thanh pho can tho":"Can Tho",
    "binh duong":"Binh Duong","dong nai":"Dong Nai","khanh hoa":"Khanh Hoa","nha trang":"Khanh Hoa",
    "quang nam":"Quang Nam","hoi an":"Quang Nam","quang ninh":"Quang Ninh","ha long":"Quang Ninh",
    "thua thien hue":"Thua Thien Hue","hue":"Thua Thien Hue",
    "ba ria":"Ba Ria - Vung Tau","vung tau":"Ba Ria - Vung Tau","brvt":"Ba Ria - Vung Tau",
    "binh thuan":"Binh Thuan","mui ne":"Binh Thuan","phan thiet":"Binh Thuan",
    "lam dong":"Lam Dong","da lat":"Lam Dong",
    "nghe an":"Nghe An","thanh hoa":"Thanh Hoa","nam dinh":"Nam Dinh",
    "thai nguyen":"Thai Nguyen","hung yen":"Hung Yen","bac ninh":"Bac Ninh",
    "phu quoc":"Kien Giang","kien giang":"Kien Giang","long an":"Long An",
    "tien giang":"Tien Giang","ben tre":"Ben Tre","vinh long":"Vinh Long",
    "binh phuoc":"Binh Phuoc","tay ninh":"Tay Ninh",
}
# Vietnamese accented aliases
PROVINCE_MAP.update({
    "hà nội":"Hà Nội","thành phố hà nội":"Hà Nội","tp. hà nội":"Hà Nội",
    "hồ chí minh":"Hồ Chí Minh","thành phố hồ chí minh":"Hồ Chí Minh","tp. hồ chí minh":"Hồ Chí Minh",
    "sài gòn":"Hồ Chí Minh","tp.hồ chí minh":"Hồ Chí Minh",
    "đà nẵng":"Đà Nẵng","thành phố đà nẵng":"Đà Nẵng","tp đà nẵng":"Đà Nẵng",
    "hải phòng":"Hải Phòng","thành phố hải phòng":"Hải Phòng","tp hải phòng":"Hải Phòng",
    "cần thơ":"Cần Thơ","thành phố cần thơ":"Cần Thơ","tp cần thơ":"Cần Thơ",
    "bình dương":"Bình Dương","tỉnh bình dương":"Bình Dương",
    "đồng nai":"Đồng Nai","tỉnh đồng nai":"Đồng Nai",
    "khánh hòa":"Khánh Hòa","hội an":"Quảng Nam","quảng nam":"Quảng Nam",
    "quảng ninh":"Quảng Ninh","hạ long":"Quảng Ninh",
    "thừa thiên huế":"Thừa Thiên Huế","huế":"Thừa Thiên Huế",
    "bà rịa":"Bà Rịa - Vũng Tàu","vũng tàu":"Bà Rịa - Vũng Tàu",
    "bình thuận":"Bình Thuận","mũi né":"Bình Thuận","phan thiết":"Bình Thuận",
    "lâm đồng":"Lâm Đồng","đà lạt":"Lâm Đồng",
    "nghệ an":"Nghệ An","thanh hóa":"Thanh Hóa","nam định":"Nam Định",
    "thái nguyên":"Thái Nguyên","hưng yên":"Hưng Yên","bắc ninh":"Bắc Ninh",
    "phú quốc":"Kiên Giang","kiên giang":"Kiên Giang",
    "tiền giang":"Tiền Giang","bến tre":"Bến Tre","vĩnh long":"Vĩnh Long",
    "bình phước":"Bình Phước","tây ninh":"Tây Ninh",
})

_LOC_PREFIX = re.compile(r"^(?:thành phố|tỉnh|tp\.\s*|tp\s+|thanh pho|tinh)\s*", re.IGNORECASE|re.UNICODE)

_MUTATE_KW = [
    "thêm mới dự án","thêm dự án mới","thêm dự án","tạo dự án mới","tạo mới dự án",
    "thêm mới liên hệ","thêm liên hệ mới","thêm liên hệ","tạo liên hệ mới","tạo mới liên hệ",
    "thêm vào hệ thống","nhập mới vào hệ thống","tạo mới vào database",
    "cập nhật dự án","sửa thông tin dự án","chỉnh sửa dự án","đổi trạng thái dự án",
    "cập nhật liên hệ","sửa thông tin liên hệ","chỉnh sửa liên hệ",
    "xóa dự án","xóa bỏ dự án","loại bỏ dự án","xóa liên hệ","xóa bỏ liên hệ",
    "xóa khỏi hệ thống","xóa khỏi database",
]
_MUTATE_VERBS = [
    "thêm", "them", "tạo", "tao", "cập nhật", "cap nhat", "sửa", "sua",
    "chỉnh sửa", "chinh sua", "xóa", "xoá", "xoa", "delete", "update", "insert", "remove",
]
_MUTATE_ENTITY_HINTS = [
    "dự án", "du an", "project", "liên hệ", "lien he", "contact", "hệ thống", "he thong", "database", "db",
    "chủ đầu tư", "chu dau tu", "cdt", "developer", "trạng thái", "trang thai",
]
_SEARCH_KW = ["google","tìm trên mạng","tìm trên google","search online","tra cứu web","tìm online","tìm trên internet","tra google","search web"]
_GLOBAL_KW = ["tổng số","bao nhiêu","thống kê","tóm tắt","tổng quan","overview","so sánh","xếp hạng","top ","nhiều nhất","ít nhất","lớn nhất","phân bổ","phân loại","theo tỉnh","theo thành phố","tổng hợp","tình hình thị trường"]
_ENTITY_KW = ["dự án","project","liên hệ","contact","chủ đầu tư","cdt"]
_LOOKUP_KW = ["liệt kê","danh sách","tìm kiếm","cho biết","cung cấp","thông tin về","chi tiết","địa chỉ","số điện thoại","email","trạng thái","giá trị","ai là","là ai","ở đâu","tại đâu","tại thành phố","tại tỉnh","thuộc","của công ty","của cdt"]


class RAGEngine:
    def _looks_like_mutation_query(self, q_raw: str) -> bool:
        """Fallback mutation detection when exact keyword phrases are not matched."""
        q = str(q_raw or "").lower().strip()
        q_ascii = unidecode(q)

        has_verb = any(v in q for v in _MUTATE_VERBS) or any(v in q_ascii for v in [
            "them", "tao", "cap nhat", "sua", "chinh sua", "xoa", "delete", "update", "insert", "remove", "doi"
        ])
        has_hint = any(h in q for h in _MUTATE_ENTITY_HINTS) or any(h in q_ascii for h in [
            "du an", "project", "lien he", "contact", "he thong", "database", "db", "chu dau tu", "cdt", "developer", "trang thai"
        ])
        has_from_to_update = (
            any(v in q_ascii for v in ["sua", "cap nhat", "doi", "update"]) and
            " tu " in f" {q_ascii} " and
            any(k in f" {q_ascii} " for k in [" sang ", " thanh "])
        )

        return (has_verb and has_hint) or has_from_to_update

    def _detect_scope(self, q_raw: str) -> str:
        q = q_raw.lower().strip()
        if any(kw in q for kw in _MUTATE_KW) or self._looks_like_mutation_query(q_raw): return "MUTATE"
        if any(kw in q for kw in _SEARCH_KW): return "SEARCH"
        if any(kw in q for kw in _GLOBAL_KW):
            if any(ek in q for ek in _ENTITY_KW) or any(p in q for p in ["bất động sản","trong hệ thống","trong database"]):
                return "GLOBAL"
        if any(ek in q for ek in _ENTITY_KW) and any(lk in q for lk in _LOOKUP_KW):
            return "LOCAL"
        return "CHAT"

    @staticmethod
    def _extract_json(text: str) -> dict:
        text = re.sub(r"```(?:json)?\s*","",text).strip().rstrip("`").strip()
        s, e = text.find("{"), text.rfind("}")
        if s >= 0 and e > s:
            try: return _json.loads(text[s:e+1])
            except Exception: pass
        return {}

    @staticmethod
    def _name_candidates(display_name: str) -> list[str]:
        """Generate normalized candidate names for entity lookup."""
        raw = str(display_name or "").strip().strip('"\'').strip("_-")
        if not raw:
            return []

        candidates: list[str] = [raw]
        cleaned = re.sub(
            r"^(xóa|xoá|xoa|sửa|chỉnh sửa|cập nhật|thêm|tạo)\s+(dự án|du an|project|liên hệ|lien he|contact)\s+",
            "",
            raw,
            flags=re.IGNORECASE,
        ).strip(" .,;:!?-_")
        if cleaned:
            candidates.append(cleaned)

        polite_trim = re.sub(r"\b(đi|nha|nhé|giúp|giúp tôi|please)\b$", "", cleaned, flags=re.IGNORECASE).strip(" .,;:!?-_")
        if polite_trim:
            candidates.append(polite_trim)

        owner_split = re.split(r"\s+của\s+", polite_trim, maxsplit=1, flags=re.IGNORECASE)[0].strip(" .,;:!?-_")
        if owner_split:
            candidates.append(owner_split)

        no_prefix = re.sub(r"^(dự án|du an|project|liên hệ|lien he|contact)\s+", "", owner_split, flags=re.IGNORECASE).strip(" .,;:!?-_")
        if no_prefix:
            candidates.append(no_prefix)

        # Trim demonstratives / relation tails, e.g. "Demo này từ A sang B" -> "Demo"
        tail_split = re.split(
            r"\s+(?:này|nay|đó|do|kia|từ|tu|sang|với|voi|của|co|from|to)\b",
            no_prefix,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip(" .,;:!?-_")
        if tail_split:
            candidates.append(tail_split)

        out: list[str] = []
        for c in candidates:
            if c and c not in out:
                out.append(c)
        return out

    @staticmethod
    def _extract_from_to(query: str) -> tuple[str, str]:
        """Extract old/new values from phrases like 'từ A sang B'."""
        q = str(query or "")
        # Prefer field-anchored pattern for owner/developer updates.
        anchored = re.search(
            r"(?:chủ\s+đầu\s+t[ưừ]|chu\s+dau\s+tu|cdt|developer)[^\n,.;]*(?:từ|tu)\s+(.+?)\s+(?:sang|thành|thanh)\s+(.+?)(?:[\n,.;!?]|$)",
            q,
            flags=re.IGNORECASE,
        )
        if anchored:
            old_v = anchored.group(1).strip(" \"'.,;:!?-_")
            new_v = anchored.group(2).strip(" \"'.,;:!?-_")
            return old_v, new_v

        generic = re.search(
            r"(?:từ|tu)\s+(.+?)\s+(?:sang|thành|thanh)\s+(.+?)(?:[\n,.;!?]|$)",
            q,
            flags=re.IGNORECASE,
        )
        if generic:
            old_v = generic.group(1).strip(" \"'.,;:!?-_")
            new_v = generic.group(2).strip(" \"'.,;:!?-_")
            return old_v, new_v
        return "", ""

    def _build_fallback_mutation(self, query: str) -> dict:
        """Heuristic mutation parser when LLM JSON parsing is missing/invalid."""
        q = str(query or "").strip()
        ql = q.lower()
        q_ascii = unidecode(ql)

        op = ""
        if any(k in ql for k in ["xóa", "xoá", "xoa", "delete", "remove", "loại bỏ"]) or any(k in q_ascii for k in ["xoa", "delete", "remove", "loai bo"]):
            op = "delete"
        elif any(k in ql for k in ["cập nhật", "cap nhat", "chỉnh sửa", "chinh sua", "sửa", "sua", "update", "đổi"]) or any(k in q_ascii for k in ["cap nhat", "chinh sua", "sua", "update", "doi"]):
            op = "update"
        elif any(k in ql for k in ["thêm", "them", "tạo", "tao", "insert", "new"]) or any(k in q_ascii for k in ["them", "tao", "insert", "new"]):
            op = "insert"

        entity = ""
        if any(k in ql for k in ["dự án", "du an", "project"]) or any(k in q_ascii for k in ["du an", "project"]):
            entity = "project"
        elif any(k in ql for k in ["liên hệ", "lien he", "contact"]) or any(k in q_ascii for k in ["lien he", "contact"]):
            entity = "contact"
        elif any(k in q_ascii for k in ["chu dau tu", "cdt", "developer", "trang thai"]):
            entity = "project"

        if not op or not entity:
            return {}

        display_name = ""
        if entity == "project":
            m = re.search(
                r"(?:dự án|du an|project)\s+([^\n,.;]+?)(?:\s+(?:này|nay|đó|do|kia|từ|tu|sang|với|voi|của|co)\b|$)",
                q,
                re.IGNORECASE,
            )
            if m:
                display_name = m.group(1).strip()
        else:
            m = re.search(
                r"(?:liên hệ|lien he|contact)\s+([^\n,.;]+?)(?:\s+(?:này|nay|đó|do|kia|từ|tu|sang|với|voi|của|co)\b|$)",
                q,
                re.IGNORECASE,
            )
            if m:
                display_name = m.group(1).strip()

        if not display_name:
            m = re.search(
                r"(?:xóa|xoá|xoa|sửa|cập nhật|chỉnh sửa|thêm|tạo|delete|update|insert)\s+(?:dự án|du an|project|liên hệ|lien he|contact)?\s*([^\n,.;]+)",
                q,
                re.IGNORECASE,
            )
            if m:
                display_name = m.group(1).strip()

        display_name_candidates = self._name_candidates(display_name)
        display_name = (display_name_candidates[-1] if display_name_candidates else "đối tượng")

        data: dict = {}
        summary = ""
        if op == "update":
            old_v, new_v = self._extract_from_to(q)
            # Common project update: owner/developer replacement
            if entity == "project" and any(k in q_ascii for k in ["chu dau tu", "cdt", "developer"]) and new_v:
                data["developer"] = new_v
                if old_v:
                    summary = f"Cập nhật chủ đầu tư dự án {display_name} từ {old_v} sang {new_v}"
                else:
                    summary = f"Cập nhật chủ đầu tư dự án {display_name} thành {new_v}"

            # Common status update
            status_m = re.search(
                r"(?:trạng thái|trang thai|status)[^\n,.;]*(?:thành|thanh|sang)\s+(.+?)(?:[\n,.;!?]|$)",
                q,
                flags=re.IGNORECASE,
            )
            if status_m:
                next_status = status_m.group(1).strip(" \"'.,;:!?-_")
                if next_status:
                    data["status"] = next_status
                    if not summary:
                        summary = f"Cập nhật trạng thái dự án {display_name} thành {next_status}"

        return {
            "operation": op,
            "entity": entity,
            "display_name": display_name,
            "slug": "",
            "data": data,
            "changes": {},
            "summary": summary,
        }

    def _doc_field_value(self, entity: str, doc: dict, field: str):
        """Extract comparable value from DB document for mutation diff preview."""
        if entity == "contact":
            cmap = {
                "name": "full_name",
                "company": "company",
                "role": "role",
                "phone": "phone",
                "email": "email",
                "address": "address",
            }
            return doc.get(cmap.get(field, field))

        # project
        pmap = {
            "name": "name",
            "province": "province",
            "district": "district",
            "address": "address",
            "developer": "developer",
            "value_billion_vnd": "value_billion_vnd",
            "value_str": "value_str",
            "status": "status",
            "phase": ("design_stage", "phase"),
            "type_tags": "category",
            "site_area": ("site_area", "area_sqm"),
            "floors": "floors",
            "groundbreaking": "start_date",
            "handover": "end_date",
            "notes": ("description", "notes"),
        }
        mapped = pmap.get(field, field)
        if isinstance(mapped, tuple):
            for mk in mapped:
                if doc.get(mk) not in (None, ""):
                    return doc.get(mk)
            return ""
        if field == "type_tags":
            cat = doc.get(mapped)
            return [cat] if cat else []
        return doc.get(mapped)

    def _preview_from_doc(self, entity: str, doc: dict, resolved_slug: str) -> dict:
        """Build UI-friendly preview payload for confirmation card."""
        if entity == "contact":
            return {
                "name": str(doc.get("full_name") or doc.get("name") or ""),
                "company": str(doc.get("company") or ""),
                "role": str(doc.get("role") or ""),
                "phone": str(doc.get("phone") or ""),
                "email": str(doc.get("email") or ""),
                "address": str(doc.get("address") or ""),
                "entity_key": resolved_slug,
            }

        dev = doc.get("developer")
        if isinstance(dev, list):
            dev = ", ".join(str(x) for x in dev if str(x).strip())

        return {
            "name": str(doc.get("name") or ""),
            "province": str(doc.get("province") or ""),
            "district": str(doc.get("district") or ""),
            "developer": str(dev or ""),
            "status": str(doc.get("status") or ""),
            "value_billion_vnd": doc.get("value_billion_vnd") if doc.get("value_billion_vnd") is not None else str(doc.get("value_str") or ""),
            "entity_key": resolved_slug,
        }

    async def _resolve_target_doc(self, entity: str, slug: str, display_name: str, query: str):
        """Resolve target document for update/delete previews and safer mutation execution."""
        from core.database import (
            find_contact_by_name,
            find_project_by_name,
            get_contact_by_slug,
            get_project_by_slug,
        )

        if entity == "project":
            get_by_slug = get_project_by_slug
            find_by_name = find_project_by_name
        else:
            get_by_slug = get_contact_by_slug
            find_by_name = find_contact_by_name

        doc = None
        resolved_slug = str(slug or "").strip()

        if resolved_slug:
            doc = await get_by_slug(resolved_slug)
            if doc:
                final_slug = str(doc.get("entity_key") or doc.get("code") or doc.get("_id") or resolved_slug)
                return doc, final_slug

        name_candidates = self._name_candidates(display_name)
        if not name_candidates:
            fallback = self._build_fallback_mutation(query)
            name_candidates = self._name_candidates(str(fallback.get("display_name") or ""))

        for name in name_candidates:
            doc = await find_by_name(name)
            if doc:
                final_slug = str(doc.get("entity_key") or doc.get("code") or doc.get("_id") or "")
                return doc, final_slug

        return None, ""

    async def _enrich_mutation_preview(self, mutation: dict, query: str) -> dict:
        """Normalize mutation payload and enrich with DB-backed preview for safer confirmation."""
        op = str(mutation.get("operation") or "").strip().lower()
        entity = str(mutation.get("entity") or "").strip().lower()
        mutation["operation"] = op
        mutation["entity"] = entity

        # Prefer data payload; derive from changes.new when needed.
        data = mutation.get("data")
        if not isinstance(data, dict):
            data = {}
        if not data and isinstance(mutation.get("changes"), dict):
            extracted = {}
            for field, change in (mutation.get("changes") or {}).items():
                if isinstance(change, dict) and "new" in change:
                    extracted[field] = change.get("new")
            data = extracted
        mutation["data"] = data

        if op not in ("insert", "update", "delete") or entity not in ("project", "contact"):
            return mutation

        display_name = str(mutation.get("display_name") or "").strip()
        if not display_name:
            fallback = self._build_fallback_mutation(query)
            display_name = str(fallback.get("display_name") or "đối tượng")
            mutation["display_name"] = display_name

        if op == "insert":
            return mutation

        doc, resolved_slug = await self._resolve_target_doc(entity, str(mutation.get("slug") or ""), display_name, query)
        if not doc:
            if op in ("update", "delete") and not mutation.get("summary"):
                ev = "dự án" if entity == "project" else "liên hệ"
                mutation["summary"] = f"Chưa tìm thấy {ev} khớp chính xác. Vui lòng kiểm tra tên hoặc entity_key trước khi xác nhận."
            if op == "delete" and not mutation.get("data"):
                mutation["data"] = {"lookup": "Không tìm thấy mẫu dữ liệu để hiển thị."}
            return mutation

        mutation["slug"] = resolved_slug
        mutation["display_name"] = str(
            doc.get("name")
            or doc.get("full_name")
            or mutation.get("display_name")
            or "đối tượng"
        )

        preview = self._preview_from_doc(entity, doc, resolved_slug)
        if op == "delete":
            mutation["data"] = preview
            ev = "dự án" if entity == "project" else "liên hệ"
            mutation["summary"] = f"Xóa {ev} có tên {mutation['display_name']}"
            return mutation

        # update: build old->new diff for confirmation card
        changes = {}
        for field, new_val in (mutation.get("data") or {}).items():
            old_val = self._doc_field_value(entity, doc, field)
            old_norm = ", ".join(str(x) for x in old_val) if isinstance(old_val, list) else old_val
            new_norm = ", ".join(str(x) for x in new_val) if isinstance(new_val, list) else new_val
            if str(old_norm) != str(new_norm):
                changes[field] = {"old": "" if old_norm is None else old_norm, "new": new_val}

        if changes:
            mutation["changes"] = changes
        elif not mutation.get("changes"):
            mutation["changes"] = {}

        return mutation

    def _extract_graph_filter(self, query: str) -> dict:
        q = query.lower()
        result: dict = {"province":"","developer":"","types":[]}
        for kw,prov in PROVINCE_MAP.items():
            if kw in q:
                result["province"] = prov; break
        if not result["province"]:
            m = re.search(r"(?:tại|ở|tại thành phố|tại tỉnh|ở thành phố)\s+([^\s,\.?\!]{3,}(?:\s+[^\s,\.?\!]{2,})?)",q)
            if m:
                raw = _LOC_PREFIX.sub("",m.group(1)).strip()
                for kw,prov in PROVINCE_MAP.items():
                    nk = _LOC_PREFIX.sub("",kw).strip()
                    if nk == raw or nk in raw or raw in nk:
                        result["province"] = prov; break
        for pat in [r"(?:của|chủ đầu tư|cdt)\s+([A-ZẮĂÂĐÊÔƠƯ][^,\.]{2,30})(?:\s+(?:tại|ở)|$)",
                    r"\b(gamuda|vingroup|vinhomes|sun group|novaland|masterise|capitaland|hưng thịnh|him lam|ecopark)\b"]:
            m = re.search(pat,query,re.IGNORECASE)
            if m:
                result["developer"] = (m.group(1) if m.lastindex else m.group(0)).strip(); break
        if any(kw in q for kw in ["liên hệ","contact","nhân sự"]): result["types"] = ["person","project","company"]
        elif any(kw in q for kw in ["công ty","chủ đầu tư","cdt"]): result["types"] = ["company","project"]
        return result

    def _extract_search_query(self, query: str) -> str:
        for pat in [r"(?:tìm trên google|search google|tìm trên mạng|tra google|tìm online)\s+(?:về|thông tin về)?\s*(.+)",
                    r"(?:google|search)\s+(?:về|thông tin)?\s*(.+)"]:
            m = re.search(pat,query,re.IGNORECASE)
            if m: return m.group(1).strip().rstrip("?").strip()
        return re.sub(r"^(tìm|search|google|tra cứu)\s+","",query.strip(),flags=re.IGNORECASE)

    async def _call_llm(self,system,messages,temperature=0.3,max_tokens=2000):
        ai = get_ai_client()
        try: return await ai.chat([{"role":"system","content":system}]+messages, temperature=temperature, max_tokens=max_tokens)
        except Exception as e: return f"Lỗi AI: {e}"

    async def _handle_chat(self,query,history,chat_system=CHAT_SYSTEM,temperature=0.65):
        answer = await self._call_llm(chat_system, history+[{"role":"user","content":query}], temperature=temperature, max_tokens=1500)
        return answer,[],0

    async def _handle_local(self,query,history,data_system=DATA_SYSTEM,temperature=0.2):
        rag = get_graphrag_client()
        result = await rag.local_search(query)
        content = LOCAL_PROMPT.format(query=query, context=result.context)
        answer = await self._call_llm(data_system, history[-6:]+[{"role":"user","content":content}], temperature=temperature)
        cits = [{"name":e.name,"type":e.type,"slug":e.id} for e in result.entities[:5]]
        return answer, cits, len(result.entities)

    async def _handle_global(self,query,history,data_system=DATA_SYSTEM,temperature=0.2):
        rag = get_graphrag_client()
        result = await rag.global_search(query)
        content = GLOBAL_PROMPT.format(query=query, context=result.context)
        answer = await self._call_llm(data_system, history[-6:]+[{"role":"user","content":content}], temperature=temperature)
        return answer, [{"name":"GraphRAG Global","type":"graphrag","slug":"global"}], len(result.community_ids)

    async def _handle_mutate(self,query,history):
        raw = await self._call_llm(MUTATE_PARSE_SYSTEM,[{"role":"user","content":query}],temperature=0.05,max_tokens=800)
        mutation = self._extract_json(raw)
        op = str(mutation.get("operation") or "").strip().lower()
        entity = str(mutation.get("entity") or "").strip().lower()

        if op not in ("insert","update","delete") or entity not in ("project","contact"):
            mutation = self._build_fallback_mutation(query)
            op = str(mutation.get("operation") or "").strip().lower()
            entity = str(mutation.get("entity") or "").strip().lower()

        if op not in ("insert","update","delete") or entity not in ("project","contact"):
            answer = (
                "Mình nhận đây là yêu cầu **thay đổi dữ liệu** nhưng chưa tách được đủ thông tin để tạo phiếu xác nhận.\n\n"
                "Vui lòng ghi rõ theo mẫu: **Sửa dự án <Tên dự án>: <trường> từ <giá trị cũ> sang <giá trị mới>**."
            )
            return answer,[],0,None

        mutation = await self._enrich_mutation_preview(mutation, query)

        name = str(mutation.get("display_name") or "").strip() or "đối tượng"
        ev = {"project":"dự án","contact":"liên hệ"}.get(entity,entity)
        if op=="delete": answer=f"Tôi hiểu bạn muốn **xóa** {ev} **{name}**.\n\nThao tác này **không thể hoàn tác**. Vui lòng xác nhận bên dưới."
        elif op=="insert": answer=f"Tôi sẽ **thêm mới** {ev} **{name}** vào hệ thống.\n\nVui lòng kiểm tra thông tin và xác nhận."
        else: answer=f"Tôi sẽ **cập nhật** {ev} **{name}**.\n\nVui lòng xem lại thay đổi và xác nhận bên dưới."
        s = str(mutation.get("summary") or "").strip()
        if s: answer += f"\n\n_{s}_"
        return answer,[],0,mutation

    async def _handle_search(self,query,history,search_system=SEARCH_SYSTEM,temperature=0.3):
        from core.web_search import search_web, format_search_results
        sq = self._extract_search_query(query)
        results = await search_web(sq,max_results=6)
        content = SEARCH_PROMPT.format(query=query,context=format_search_results(results,sq))
        answer = await self._call_llm(search_system, history[-4:]+[{"role":"user","content":content}], temperature=temperature)
        cits = [{"name":r["title"][:50],"type":"web","slug":r["url"]} for r in results[:3] if r.get("url")]
        return answer, cits, len(results)

    async def answer(self,query,history=None,style="natural"):
        history = history or []
        scope = self._detect_scope(query)
        graph_filter = self._extract_graph_filter(query) if scope in ("LOCAL","GLOBAL") else {}
        pending_mutation = None

        chat_sys, data_sys, search_sys = _systems_for(style)
        is_precise = str(style or "").strip().lower() in ("precise", "chinh xac", "chính xác")
        # Precise mode -> much lower temperature to suppress improvisation.
        t_chat   = 0.25 if is_precise else 0.65
        t_data   = 0.05 if is_precise else 0.2
        t_search = 0.1  if is_precise else 0.3

        try:
            if scope=="MUTATE": answer,citations,ctx,pending_mutation = await self._handle_mutate(query,history)
            elif scope=="CHAT": answer,citations,ctx = await self._handle_chat(query,history,chat_sys,t_chat)
            elif scope=="LOCAL": answer,citations,ctx = await self._handle_local(query,history,data_sys,t_data)
            elif scope=="GLOBAL": answer,citations,ctx = await self._handle_global(query,history,data_sys,t_data)
            elif scope=="SEARCH": answer,citations,ctx = await self._handle_search(query,history,search_sys,t_search)
            else: answer,citations,ctx = await self._handle_chat(query,history,chat_sys,t_chat)
        except Exception as e:
            print(f"[RAGEngine.answer] scope={scope} error: {e}")
            answer,citations,ctx = f"Đã xảy ra lỗi: {e}",[],0
        return {"answer":answer,"citations":citations,"intent":scope,"graph_filter":graph_filter,"context_used":ctx,"pending_mutation":pending_mutation,"style":"precise" if is_precise else "natural"}


_engine: Optional[RAGEngine] = None

def get_rag_engine() -> RAGEngine:
    global _engine
    if _engine is None: _engine = RAGEngine()
    return _engine
