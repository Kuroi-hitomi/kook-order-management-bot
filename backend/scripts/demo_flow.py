from datetime import datetime
from app.db import get_session
from app.models import User, Order, OrderAudit, Receipt, UserRole, OrderStatus, ReceiptType

def main():
    with get_session() as s:
        # 1) 新建用户（若不存在）
        u = s.query(User).filter_by(kook_id="kook_1001").one_or_none()
        if not u:
            u = User(kook_id="kook_1001", name="Demo User", role=UserRole.PLAYER)
            s.add(u)
            s.flush()  # 拿到 u.id

        # 2) 下单
        o = Order(
            user_id=u.id,
            amount=9.99,
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow()
        )
        s.add(o); s.flush()

        # 3) 写审计
        s.add(OrderAudit(
            order_id=o.id,
            action="CREATE",
            note="initial create",
            created_at=datetime.utcnow()
        ))

        # 4) 开收据
        s.add(Receipt(
            order_id=o.id,
            user_id=u.id,
            type=ReceiptType.PAYMENT,
            amount=o.amount,
            created_at=datetime.utcnow()
        ))

        # 5) 更新订单为已支付
        o.status = OrderStatus.PAID

        s.commit()
        print("Demo flow OK. order_id=", o.id)

if __name__ == "__main__":
    main()
