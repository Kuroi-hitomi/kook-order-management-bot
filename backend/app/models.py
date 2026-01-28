from __future__ import annotations
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column, BigInteger, Integer, Text, Enum, JSON, ForeignKey,
    func, DateTime
)
from sqlalchemy import Identity
from sqlalchemy import JSON
import enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text
import sqlalchemy as sa

Base = declarative_base()

# 1) 建议用 Enum 代替文本 CHECK，更安全
class UserRole(str, enum.Enum):
    PLAYER = "PLAYER"
    BOSS = "BOSS"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"

class OrderStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    REVIEW_REJECTED = "REVIEW_REJECTED"
    REVIEW_APPROVED = "REVIEW_APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

# 2) users
class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, Identity(always=False), primary_key=True)
    display_name = Column(Text, nullable=False)
    role = Column(Enum(UserRole, name="user_role"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    kook_binding = relationship("KookBinding", back_populates="user", uselist=False)

# 3) KOOK 绑定
class KookBinding(Base):
    __tablename__ = "kook_bindings"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kook_user_id = Column(Text, nullable=False, unique=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user = relationship("User", back_populates="kook_binding")

# 4) 订单
class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True)
    game_name = Column(Text, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    duration_hours = Column(sa.Numeric(6,2), nullable=False)
    boss_kook_id   = Column(Text, nullable=True)
    boss_kook_name = Column(Text, nullable=True)
    player_kook_id   = Column(Text, nullable=True)
    player_kook_name = Column(Text, nullable=True)
    status = Column(Enum(OrderStatus, name="order_status"), nullable=False)
    extra = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now()
    )

# 5) 审计
class OrderAudit(Base):
    __tablename__ = "order_audits"

    id = Column(BigInteger, primary_key=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    actor_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)  # 系统可为空
    from_status = Column(Enum(OrderStatus, name="order_status"), nullable=True)
    to_status = Column(Enum(OrderStatus, name="order_status"), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    payload = Column(JSON, nullable=True)

# 6) 回执
class ReceiptType(str, enum.Enum):
    ACCEPTANCE = "ACCEPTANCE"
    COMPLETION = "COMPLETION"

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(BigInteger, primary_key=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(ReceiptType, name="receipt_type"), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
