# app/schemas.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, Any, Dict

from pydantic import BaseModel, Field

from typing import Annotated

# ---- 入参 ----

class CreateOrderIn(BaseModel):
    game_name: str = Field(..., min_length=1, max_length=100)
    amount_cents: int = Field(..., ge=0, description="金额（分）")
    # 与 DB Numeric(6,2) 对齐
    duration_hours: Annotated[Decimal, Field(gt=0, max_digits=6, decimal_places=2)]
    # 机器人在 /order 时必须传入
    boss_kook_id: str = Field(..., min_length=1)
    boss_kook_name: str = Field(..., min_length=1, max_length=100)

class AcceptIn(BaseModel):
    # 机器人在 /accept 时必须传入
    player_kook_id: str = Field(..., min_length=1)
    player_kook_name: str = Field(..., min_length=1, max_length=100)
    # 审计或附加信息（可选）
    payload: Optional[Dict[str, Any]] = None

class ReviewIn(BaseModel):
    reviewer_kook_id: str
    approve: bool
    reason: Optional[str] = None

class CompleteIn(BaseModel):
    actor_kook_id: str
    payload: Optional[Dict[str, Any]] = None

# ---- 出参 ----

class OrderOut(BaseModel):
    id: int
    game_name: str
    amount_cents: int
    duration_hours: Annotated[Decimal, Field(gt=0, max_digits=6, decimal_places=2)]
    status: str

    boss_kook_id: Optional[str] = None
    boss_kook_name: Optional[str] = None
    player_kook_id: Optional[str] = None
    player_kook_name: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # 用 default_factory 防止可变默认值共享
    extra: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "from_attributes": True,  # v1 的 orm_mode=True
        "populate_by_name": True,
    }
