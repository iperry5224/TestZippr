"""
Servator data models.

Core entities used across the platform.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    SCO_ANOMALY = "sco_anomaly"
    SHELF_ANOMALY = "shelf_anomaly"
    EXIT_VERIFICATION = "exit_verification"
    INVENTORY_DISCREPANCY = "inventory_discrepancy"
    BEHAVIORAL_PATTERN = "behavioral_pattern"


class Alert(BaseModel):
    """Security alert from any module."""

    id: str
    store_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
    resolved: bool = False


class Store(BaseModel):
    """Store/franchise location."""

    id: str
    name: str
    region: Optional[str] = None
    sco_lanes: int = 0
    high_shrink_aisles: list[str] = Field(default_factory=list)


class RiskScore(BaseModel):
    """Predictive risk score for a dimension."""

    store_id: str
    dimension: str  # sku, aisle, shift, etc.
    value: str
    score: float  # 0-100
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    factors: list[str] = Field(default_factory=list)
