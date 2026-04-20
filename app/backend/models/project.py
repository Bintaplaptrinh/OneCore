from pydantic import BaseModel
from typing import Optional, List

class Project(BaseModel):
    slug: str
    name: Optional[str] = ""
    province: Optional[str] = ""
    district: Optional[str] = ""
    address: Optional[str] = ""
    developer: Optional[List[str]] = []
    value_billion_vnd: Optional[float] = None
    value_str: Optional[str] = ""
    status: Optional[str] = ""
    phase: Optional[str] = ""
    dev_type: Optional[str] = ""
    owner_type: Optional[str] = ""
    site_area: Optional[str] = ""
    floor_area: Optional[str] = ""
    floors: Optional[str] = ""
    groundbreaking: Optional[str] = ""
    handover: Optional[str] = ""
    type_tags: Optional[List[str]] = []
    notes: Optional[str] = ""
    source_file: Optional[str] = ""

class ProjectsResponse(BaseModel):
    data: List[Project]
    total: int
    page: int
    limit: int

class Contact(BaseModel):
    slug: str
    name: Optional[str] = ""
    company: Optional[str] = ""
    role: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""
    image_path: Optional[str] = ""

class ContactsResponse(BaseModel):
    data: List[Contact]
    total: int

class StatsResponse(BaseModel):
    total_projects: int
    total_contacts: int
    total_relationships: int
    total_value_billion_vnd: float = 0.0
    provinces: List[str]
    statuses: List[str]