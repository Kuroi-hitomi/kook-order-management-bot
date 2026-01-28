# app/services/orders.py
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import (
    Order, OrderAudit, OrderStatus,
    Receipt, ReceiptType,
)
from app.services.users import get_or_create_user_by_kook


def _ensure_order(db: Session, order_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id).one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return order


def review_order(
    db: Session,
    order_id: int,
    reviewer_kook_id: str,
    approve: bool,
    reason: Optional[str] = None,
) -> Order:
    """审核通过/驳回：PENDING_REVIEW -> REVIEW_APPROVED / REVIEW_REJECTED"""
    order = _ensure_order(db, order_id)

    if order.status != OrderStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=409,
            detail=f"invalid state: {order.status}. expect PENDING_REVIEW"
        )

    reviewer = get_or_create_user_by_kook(db, reviewer_kook_id, role_hint="REVIEWER")
    to_status = OrderStatus.REVIEW_APPROVED if approve else OrderStatus.REVIEW_REJECTED

    db.add(OrderAudit(
        order_id=order.id,
        actor_user_id=reviewer.id,
        from_status=order.status,
        to_status=to_status,
        reason=reason or ("approved" if approve else "rejected"),
    ))
    order.status = to_status

    db.commit(); db.refresh(order)
    return order


def accept_order(
    db: Session,
    order_id: int,
    player_kook_id: str,
    player_kook_name: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Order:
    """
    陪玩接单：REVIEW_APPROVED -> IN_PROGRESS
    - 直接写入 player_kook_id / player_kook_name
    - 不再校验内部 user_id（我们已去掉）
    """
    order = _ensure_order(db, order_id)

    if order.status not in (OrderStatus.REVIEW_APPROVED):
        raise HTTPException(
            status_code=409,
            detail=f"invalid state: {order.status}. expect REVIEW_APPROVED/PENDING_REVIEW"
        )

    # 写入陪玩 KOOK 身份
    order.player_kook_id = player_kook_id
    if player_kook_name:
        order.player_kook_name = player_kook_name

    # 状态流转
    order.status = OrderStatus.IN_PROGRESS

    # 审计（保留最小必需字段）
    db.add(OrderAudit(
        order_id=order.id,
        to_status=order.status,
        reason="accept",
        # 如果你的 OrderAudit 有 payload 字段可以加上：payload=payload
    ))

    db.commit()
    db.refresh(order)
    return order


def complete_order(
    db: Session,
    order_id: int,
    actor_kook_id: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Order:
    """结单：IN_PROGRESS -> COMPLETED，同时生成完成回执"""
    order = _ensure_order(db, order_id)

    if order.status != OrderStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409,
            detail=f"invalid state: {order.status}. expect IN_PROGRESS"
        )

    # 谁来触发完成都行（老板/陪玩/系统），这里用 kook id 记录审计人
    actor = get_or_create_user_by_kook(db, actor_kook_id, role_hint="PLAYER")

    db.add(OrderAudit(
        order_id=order.id,
        actor_user_id=actor.id,
        from_status=order.status,
        to_status=OrderStatus.COMPLETED,
        reason="completed",
    ))

    # 生成回执：COMPLETION
    default_payload = {
        "completed_by": getattr(actor, "display_name", actor_kook_id),
        "amount_cents": order.amount_cents,
        "duration_hours": order.duration_hours,
    }
    db.add(Receipt(
        order_id=order.id,
        type=ReceiptType.COMPLETION,
        payload=(payload or default_payload),
    ))

    order.status = OrderStatus.COMPLETED
    db.commit(); db.refresh(order)
    return order
