import os
import re
import asyncio
import httpx
from dotenv import load_dotenv
from khl import Bot, Message

# ---------- 环境 ----------
load_dotenv()
BOT_TOKEN = os.getenv('KOOK_BOT_TOKEN')
BASE_URL  = os.getenv('BACKEND_BASE_URL', 'http://localhost:8000')

# 旧：可留作他用
ADMIN_IDS = {x.strip() for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}

# 新：权限白名单（在 bot/.env 配置）
BOSSES_IDS = {x.strip() for x in os.getenv("BOSSES_IDS", "").split(",") if x.strip()}
STAFF_IDS  = {x.strip() for x in os.getenv("STAFF_IDS", "").split(",") if x.strip()}

if not BOT_TOKEN:
    raise RuntimeError('KOOK_BOT_TOKEN not set')

def is_boss(uid: str) -> bool:
    return str(uid) in BOSSES_IDS

def is_staff(uid: str) -> bool:
    return str(uid) in STAFF_IDS

def is_operator(uid: str) -> bool:
    """老板或客服均可操作"""
    suid = str(uid)
    return (suid in BOSSES_IDS) or (suid in STAFF_IDS)

async def ensure_perm(msg: Message, *, need: str) -> bool:
    """
    统一权限判断。need 取值：
      - 'operate'：order/review/accept/done 需要（老板或客服）
      - 'boss_only'：info 仅老板
    返回 True 表示放行；False 表示已提示并拦截。
    """
    uid = str(msg.author.id)
    if need == 'operate':
        if is_operator(uid):
            return True
        await msg.reply("❌ 无权限，此命令仅限【老板或客服】使用。")
        return False
    if need == 'boss_only':
        if is_boss(uid):
            return True
        await msg.reply("❌ 无权限，此命令仅限【老板】使用。")
        return False
    await msg.reply("❌ 无权限。")
    return False

# ---- HTTP 客户端（全局复用）----
client = httpx.AsyncClient(base_url=BASE_URL, timeout=10)

async def api_post(path: str, json: dict):
    r = await client.post(path, json=json)
    if r.status_code >= 400:
        try:
            detail = r.json().get('detail', r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f'HTTP {r.status_code}: {detail}')
    return r.json()

async def api_get(path: str):
    r = await client.get(path)
    if r.status_code >= 400:
        try:
            detail = r.json().get('detail', r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f'HTTP {r.status_code}: {detail}')
    return r.json()

# ---- 创建机器人 ----
bot = Bot(token=BOT_TOKEN)

# ---------- KOOK 工具 ----------
MENTION_RE = re.compile(r"\(met\)(\d+)\(met\)")

def parse_kook_id(arg: str, author_id: str) -> str:
    """
    解析 KOOK 用户：支持 @提及 / 纯数字ID / @me
    返回 KOOK 数字 ID（字符串）
    """
    if not arg:
        raise RuntimeError("缺少用户参数")
    low = arg.lower().strip()
    if low in {"@me", "me", "self", "我"}:
        return str(author_id)
    m = MENTION_RE.search(arg)
    if m:
        return m.group(1)
    if arg.isdigit():
        return arg
    raise RuntimeError("用户参数既不是 @提及 也不是纯数字 ID，也不是 @me")

async def get_kook_tag(bot_obj: Bot, kook_id: str) -> str:
    """
    KOOK 数字ID -> '用户名#识别码'；失败则回退数字ID
    """
    try:
        u = await bot_obj.client.fetch_user(str(kook_id))
        name  = getattr(u, "username", None) or getattr(u, "name", None) or "unknown"
        ident = getattr(u, "identify_num", None) or getattr(u, "identify_num_", None)
        return f"{name}#{ident}" if ident else name
    except Exception:
        return str(kook_id)

# ---------- 帮助 ----------
HELP_TEXT = (
    "🧾 **Kook 订单指令**\n"
    "`/order <游戏名> <时长（小时）> <金额(元)> <@老板>`  创建订单\n"
    "`/review <订单ID> <ok|no> [原因]`  审核通过/驳回\n"
    "`/accept <订单ID> <@陪玩>`  接单并绑定陪玩\n"
    "`/done <订单ID>`  完成订单\n"
    "`/info <订单ID>`  查看订单详情\n"
)

@bot.command(name='help')
async def help_cmd(msg: Message):
    await msg.reply(HELP_TEXT)

def parse_int(x: str, name: str) -> int:
    try:
        return int(x)
    except Exception:
        raise RuntimeError(f'参数 `{name}` 必须是整数')

def parse_hours(x: str) -> float:
    try:
        val = float(x)
    except Exception:
        raise RuntimeError('参数 `hours` 必须是数字（支持小数），如 1.5')
    if val <= 0:
        raise RuntimeError('参数 `hours` 必须大于 0')
    return round(val, 2)  # 与 Numeric(6,2) 对齐

# ---------- 1) 创建订单：最后一参为 @老板 ----------
@bot.command(name='order')
async def order_cmd(msg: Message, game: str=None, hours: str=None, cents: str=None, boss_arg: str=None):
    # 权限：老板或客服
    if not await ensure_perm(msg, need='operate'):
        return
    """
    /order LOL 1.5 3000 @某老板 | 174142457 | @me
    """
    try:
        if not all([game, hours, cents, boss_arg]):
            await msg.reply("用法：`/order <game> <hours> <cents> <@老板|老板_id|@me>`（hours 支持小数，如 1.5）")
            return

        duration_hours = parse_hours(hours)
        amount_cents   = parse_int(cents, 'cents')

        boss_kook_id   = parse_kook_id(boss_arg, msg.author.id)
        boss_kook_name = await get_kook_tag(bot, boss_kook_id)

        data = await api_post("/api/orders", {
            "game_name": game,
            "amount_cents": amount_cents,
            "duration_hours": duration_hours,
            "boss_kook_id": boss_kook_id,
            "boss_kook_name": boss_kook_name
        })
        await msg.reply(
            f"✅ 订单创建成功：ID={data.get('id')}，老板={boss_kook_name}（{boss_kook_id}），"
            f"状态={data.get('status')}"
        )
    except Exception as e:
        await msg.reply(f"❌ 创建失败：{e}")

# ---------- 2) 审核 ----------
@bot.command(name='review')
async def review_cmd(msg: Message, order_id: str=None, decision: str=None, *reason_parts):
    # 权限：老板或客服
    if not await ensure_perm(msg, need='operate'):
        return
    try:
        if not order_id or decision not in ('ok', 'no'):
            await msg.reply("用法：`/review <订单ID> <ok|no> [原因]`")
            return
        oid = parse_int(order_id, 'id')
        approve = decision == 'ok'
        reviewer_kook_id = msg.author.id
        reason = ' '.join(reason_parts) if reason_parts else ('approved' if approve else 'rejected')

        data = await api_post(f"/api/orders/{oid}/review", {
            "reviewer_kook_id": str(reviewer_kook_id),
            "approve": approve,
            "reason": reason
        })
        await msg.reply(f"🪪 审核结果：ID={data.get('id')}，状态={data.get('status')}")
    except Exception as e:
        await msg.reply(f"❌ 审核失败：{e}")

# ---------- 3) 接单 ----------
@bot.command(name='accept')
async def accept_cmd(msg: Message, order_id: str=None, player_arg: str=None):
    # 权限：老板或客服（陪玩不需要使用机器人）
    if not await ensure_perm(msg, need='operate'):
        return
    """
    用法：
      /accept <订单ID> <@陪玩|陪玩_id|@me>
    行为：
      - 解析陪玩 KOOK 数字ID
      - 反查“用户名#识别码”
      - 一起传给后端: player_kook_id + player_kook_name
    """
    try:
        if not order_id or not player_arg:
            await msg.reply("用法：`/accept <订单ID> <@陪玩|陪玩_id|@me>`（必须指定）")
            return
        oid = parse_int(order_id, 'id')

        # 解析 KOOK 数字ID
        player_kook_id = parse_kook_id(player_arg, msg.author.id)
        # 反查“用户名#识别码”
        player_kook_name = await get_kook_tag(bot, player_kook_id)

        data = await api_post(f"/api/orders/{oid}/accept", {
            "player_kook_id": player_kook_id,
            "player_kook_name": player_kook_name,
            "payload": {"accepted_by": str(msg.author.id)}
        })

        await msg.reply(
            f"🎮 接单成功：ID={data.get('id')}，陪玩={player_kook_name}（{player_kook_id}），状态={data.get('status')}"
        )
    except Exception as e:
        await msg.reply(f"❌ 接单失败：{e}")

# ---------- 4) 完成 ----------
@bot.command(name='done')
async def done_cmd(msg: Message, order_id: str=None):
    # 权限：老板或客服
    if not await ensure_perm(msg, need='operate'):
        return
    try:
        if not order_id:
            await msg.reply("用法：`/done <订单ID>`")
            return
        oid = parse_int(order_id, 'id')
        actor_kook_id = str(msg.author.id)

        data = await api_post(f"/api/orders/{oid}/complete", {
            "actor_kook_id": actor_kook_id,
            "payload": {"finished_by": actor_kook_id}
        })
        await msg.reply(f"✅ 已完成：ID={data.get('id')}，状态={data.get('status')}")
    except Exception as e:
        await msg.reply(f"❌ 完成失败：{e}")

# ---------- 5) 查询 ----------
@bot.command(name='info')
async def info_cmd(msg: Message, order_id: str=None):
    # 权限：仅老板
    if not await ensure_perm(msg, need='boss_only'):
        return
    try:
        if not order_id:
            await msg.reply("用法：`/info <订单ID>`")
            return
        oid = parse_int(order_id, 'id')
        data = await api_get(f"/api/orders/{oid}")

        await msg.reply(
            "🧾 订单 {oid}：game={game}，时长={dur}h，金额={amt}元，"
            "老板={bname}（{bid}），陪玩={pname}（{pid}），状态={st}".format(
                oid=oid,
                game=data.get("game_name"),
                dur=data.get("duration_hours"),
                amt=data.get("amount_cents"),
                bname=data.get("boss_kook_name") or "—",
                bid=data.get("boss_kook_id") or "—",
                pname=data.get("player_kook_name") or "未绑定",
                pid=data.get("player_kook_id") or "—",
                st=data.get("status"),
            )
        )
    except Exception as e:
        await msg.reply(f"❌ 查询失败：{e}")

# ---------- 运行 ----------
if __name__ == '__main__':
    try:
        bot.run()
    finally:
        try:
            asyncio.get_event_loop().run_until_complete(client.aclose())
        except Exception:
            pass
