# backend/scripts/seed.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from app.db import get_session
from app.models import User, UserRole, KookBinding

# 预设种子用户（KOOK账号id, display_name, role）
SEED_USERS = [
    ("kook_admin_001", "Admin", UserRole.ADMIN),
    ("kook_boss_001", "Boss A", UserRole.BOSS),
    ("kook_player_001", "Player A", UserRole.PLAYER),
]

def main():
    created_users = 0
    created_bindings = 0

    with get_session() as s:
        for kook_uid, name, role in SEED_USERS:
            # 查 KookBinding 有没有同名 KOOK 账号
            binding = s.query(KookBinding).filter_by(kook_user_id=kook_uid).one_or_none()
            if binding:
                print(f"Skip existing KOOK user {kook_uid}")
                continue

            # 没有绑定 → 新建 User + KookBinding
            user = User(display_name=name, role=role)
            s.add(user)
            s.flush()  # 获取 user.id

            binding = KookBinding(user_id=user.id, kook_user_id=kook_uid)
            s.add(binding)

            created_users += 1
            created_bindings += 1

        s.commit()

    print(f"Seed done. created_users={created_users}, created_bindings={created_bindings}")

if __name__ == "__main__":
    main()
