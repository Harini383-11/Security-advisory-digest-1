"""
Pydantic models for Security Advisory Digest system.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Database Models (for ORM-like operations)

class AdvisoryDB(BaseModel):
    """Advisory database model."""
    id: Optional[int] = None
    advisory_id: str
    title: str
    description: str
    severity: str
    vendor: str
    product: str
    published_date: datetime
    source_feed: str
    url: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InventoryItemDB(BaseModel):
    """Inventory item database model."""
    id: Optional[int] = None
    asset_id: str
    software_name: str
    version: str

    class Config:
        from_attributes = True


class MatchDB(BaseModel):
    """Match database model."""
    id: Optional[int] = None
    advisory_id: int
    inventory_item_id: int
    risk_level: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# API Request/Response Models

class Advisory(BaseModel):
    """Advisory model for API responses."""
    id: Optional[int] = None
    advisory_id: str
    title: str
    description: str
    severity: str
    vendor: str
    product: str
    published_date: datetime
    source_feed: str
    url: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class InventoryItem(BaseModel):
    """Inventory item model for API responses."""
    id: Optional[int] = None
    asset_id: str
    software_name: str
    version: str


class Match(BaseModel):
    """Match model for API responses."""
    id: Optional[int] = None
    advisory_id: int
    inventory_item_id: int
    risk_level: str
    created_at: Optional[datetime] = None


class AdvisoryMatch(BaseModel):
    """Complete advisory with matching inventory items."""
    advisory: Advisory
    matches: List[InventoryItem]
    risk_level: str


class AISummary(BaseModel):
    """AI-generated summary model."""
    executive_summary: str
    business_impact: str
    remediation_advice: str


class ReportData(BaseModel):
    """Report data model."""
    scan_time: str
    total_advisories: int
    matches: List[AdvisoryMatch]
    executive_summary: str
    all_advisories: Optional[List[Advisory]] = None


class ScanRequest(BaseModel):
    """Scan request model for POST /scan endpoint."""
    force_refresh: bool = False


class ScanResponse(BaseModel):
    """Scan response model."""
    status: str
    message: str
    report: Optional[ReportData] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    ollama_available: bool
    database_available: bool
