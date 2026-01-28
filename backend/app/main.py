# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app.models import Order, OrderAudit, OrderStatus
from app.schemas import (
    CreateOrderIn, OrderOut,
    ReviewIn, AcceptIn, CompleteIn,
)


app = FastAPI(title="Kook Order Backend (MVP)")

# ---------- 通用异常处理 ----------
@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "duplicate or invalid data"}
    )

@app.get("/")
def root():
    return {"ok": True, "service": "Kook Order Backend"}

# ---------- 小工具：统一构造输出 ----------
def to_order_out(order: Order) -> OrderOut:
    # 有的 Enum 需要 .value，有的直接是 str
    status_val = order.status.value if hasattr(order.status, "value") else str(order.status)
    return OrderOut(
        id=order.id,
        game_name=order.game_name,
        amount_cents=order.amount_cents,
        duration_hours=order.duration_hours,
        status=status_val,
        extra=order.extra,
        # 新增：直接从 orders 表返回 KOOK 身份
        boss_kook_id=getattr(order, "boss_kook_id", None),
        boss_kook_name=getattr(order, "boss_kook_name", None),
        player_kook_id=getattr(order, "player_kook_id", None),
        player_kook_name=getattr(order, "player_kook_name", None),
    )

# ---------- 1) 创建订单：写入老板 KOOK id + name ----------
@app.post("/api/orders", response_model=OrderOut)
def create_order(payload: CreateOrderIn, db: Session = Depends(get_db)):
    """
    期望 payload（schemas.CreateOrderIn）包含：
    - game_name: str
    - amount_cents: int
    - duration_hours: Decimal/float(保留2位)
    - boss_kook_id: str               ← KOOK 数字ID（如 "174142457"）
    - boss_kook_name: str             ← KOOK 昵称（如 "奥巴马#1234"）
    """
    order = Order(
        game_name=payload.game_name.strip(),
        amount_cents=payload.amount_cents,
        duration_hours=payload.duration_hours,
        status=OrderStatus.PENDING_REVIEW,
        # 直接记录 KOOK 身份（不再依赖内部用户ID）
        boss_kook_id=payload.boss_kook_id,
        boss_kook_name=payload.boss_kook_name,
        # 玩家信息接单时写入
        player_kook_id=None,
        player_kook_name=None,
    )
    db.add(order)
    db.flush()

    db.add(OrderAudit(order_id=order.id,
                      to_status=OrderStatus.PENDING_REVIEW,
                      reason="create"))
    db.commit()
    db.refresh(order)
    return to_order_out(order)

# ---------- 2) 查询订单：直接返回四个 KOOK 字段 ----------
@app.get("/api/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return to_order_out(order)

# ---------- 3) 审核（保持原有业务，仅返回增加新字段） ----------
@app.post("/api/orders/{order_id}/review", response_model=OrderOut)
def review_order_api(order_id: int, payload: ReviewIn, db: Session = Depends(get_db)):
    """
    你的 services.review_order 如果仍可用也能继续用；
    这里为了最小改动，直接复用原有业务层（若有）。
    """
    from app.services.orders import review_order  # 局部导入，避免未使用报警
    order = review_order(
        db,
        order_id=order_id,
        reviewer_kook_id=payload.reviewer_kook_id,
        approve=payload.approve,
        reason=payload.reason,
    )
    return to_order_out(order)

# ---------- 4) 接单：必须提供陪玩 KOOK id + name，并写入 ----------
@app.post("/api/orders/{order_id}/accept", response_model=OrderOut)
def accept_order_api(order_id: int, payload: AcceptIn, db: Session = Depends(get_db)):
    """
    接单：必须提供 player_kook_id / player_kook_name
    逻辑委托给 services.orders.accept_order（新版）
    """
    from app.services.orders import accept_order as svc_accept_order
    order = svc_accept_order(
        db=db,
        order_id=order_id,
        player_kook_id=payload.player_kook_id,
        player_kook_name=payload.player_kook_name,
        payload=payload.payload,
    )
    return to_order_out(order)

# ---------- 5) 完成（保持原有业务，仅返回增加新字段） ----------
@app.post("/api/orders/{order_id}/complete", response_model=OrderOut)
def complete_order_api(order_id: int, payload: CompleteIn, db: Session = Depends(get_db)):
    from app.services.orders import complete_order  # 局部导入
    order = complete_order(
        db,
        order_id=order_id,
        actor_kook_id=payload.actor_kook_id,
        payload=payload.payload,
    )
    return to_order_out(order)
