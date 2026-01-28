# app/services/users.py
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import User, UserRole, KookBinding

def get_or_create_user_by_kook(db: Session, kook_id: str, role_hint: Optional[str] = None) -> User:
    """按 KOOK 用户ID 找到 User；没有就创建 user+binding（幂等）"""
    kid = str(kook_id)

    # 1) 先查绑定，避免重复插入触发 UNIQUE
    kb = db.query(KookBinding).filter_by(kook_user_id=kid).one_or_none()
    if kb:
        return kb.user

    # 2) 没有则新建
    role = None
    if role_hint:
        role_hint = role_hint.upper()
        try:
            role = UserRole[role_hint]
        except KeyError:
            role = UserRole.PLAYER  # 兜底

    user = User(display_name=f"kook_{kid}", role=role or UserRole.PLAYER)
    db.add(user)
    db.flush()  # 得到 user.id

    db.add(KookBinding(user_id=user.id, kook_user_id=kid))
    try:
        db.commit()
    except IntegrityError:
        # 并发或其它请求已创建 -> 回滚重查
        db.rollback()
        kb2 = db.query(KookBinding).filter_by(kook_user_id=kid).one()
        return kb2.user

    db.refresh(user)
    return user
