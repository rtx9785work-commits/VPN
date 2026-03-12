import asyncio
import re
import ssl
import socket
import sqlite3
import struct
import sys
import time
import threading
import uuid as uuid_mod
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from urllib.parse import unquote, quote

import aiohttp
import requests

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties


TOKEN          = "8751204871:AAGVRsFhuACciSRYDczrJmpy4nQE4Vsk6QI"
ADMIN_ID       = 2039569420
ADMIN_USERNAME = "hhlnnh"

DB_PATH        = "kick_vpn.db"

GITHUB_TOKEN   = "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"

FREE_GIST_ID   = None

MAX_TOTAL       = 100
MIN_TOTAL       = 50
CHECK_TIMEOUT   = 8
MAX_WORKERS     = 80
MAX_CHECK_SEC   = 110
UPDATE_INTERVAL = 3600

BYPASS_SOURCES = [
    "https://github.com/igareck/vpn-configs-for-russia/blob/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://github.com/igareck/vpn-configs-for-russia/blob/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
]

COUNTRY_PROXIMITY_ORDER = [
    "Россия", "Беларусь", "Казахстан", "Украина", "Молдова", "Грузия", "Армения", "Азербайджан", "Узбекистан",
    "Эстония", "Латвия", "Литва", "Финляндия", "Польша", "Румыния", "Болгария", "Венгрия", "Словакия", "Чехия",
    "Австрия", "Сербия", "Хорватия", "Словения", "Македония", "Босния", "Черногория", "Косово", "Швеция",
    "Норвегия", "Дания", "Германия", "Нидерланды", "Бельгия", "Люксембург", "Швейцария", "Франция", "Италия",
    "Испания", "Португалия", "Греция", "Кипр", "Мальта", "Ирландия", "Великобритания", "Исландия", "Албания",
    "Турция", "США",
]

ALLOWED_COUNTRIES = set(COUNTRY_PROXIMITY_ORDER)

COUNTRY_MAP = {
    "Russia": "Россия", "Germany": "Германия", "Netherlands": "Нидерланды",
    "United States": "США", "USA": "США", "Finland": "Финляндия", "France": "Франция",
    "United Kingdom": "Великобритания", "UK": "Великобритания", "Turkey": "Турция",
    "Poland": "Польша", "Sweden": "Швеция", "Kazakhstan": "Казахстан", "Anycast": "Россия",
    "Ukraine": "Украина", "Switzerland": "Швейцария", "Italy": "Италия",
    "Spain": "Испания", "Austria": "Австрия", "Czech": "Чехия", "Latvia": "Латвия",
    "Lithuania": "Литва", "Estonia": "Эстония", "Moldova": "Молдова", "Belarus": "Беларусь",
    "Serbia": "Сербия", "Romania": "Румыния", "Bulgaria": "Болгария", "Hungary": "Венгрия",
    "Slovakia": "Словакия", "Croatia": "Хорватия", "Slovenia": "Словения",
    "Georgia": "Грузия", "Armenia": "Армения", "Azerbaijan": "Азербайджан",
    "Uzbekistan": "Узбекистан", "Denmark": "Дания", "Norway": "Норвегия",
    "Belgium": "Бельгия", "Portugal": "Португалия", "Greece": "Греция",
    "Ireland": "Ирландия", "Luxembourg": "Люксембург", "Cyprus": "Кипр",
    "Iceland": "Исландия", "Malta": "Мальта", "Albania": "Албания",
    "North Macedonia": "Македония", "Bosnia": "Босния", "Montenegro": "Черногория",
    "Kosovo": "Косово",
}

FLAG_MAP = {
    "Россия": "🇷🇺", "Германия": "🇩🇪", "Нидерланды": "🇳🇱", "США": "🇺🇸",
    "Финляндия": "🇫🇮", "Франция": "🇫🇷", "Великобритания": "🇬🇧", "Турция": "🇹🇷",
    "Польша": "🇵🇱", "Швеция": "🇸🇪", "Казахстан": "🇰🇿", "Украина": "🇺🇦",
    "Швейцария": "🇨🇭", "Италия": "🇮🇹", "Испания": "🇪🇸", "Австрия": "🇦🇹",
    "Чехия": "🇨🇿", "Латвия": "🇱🇻", "Литва": "🇱🇹", "Эстония": "🇪🇪",
    "Молдова": "🇲🇩", "Беларусь": "🇧🇾", "Сербия": "🇷🇸", "Румыния": "🇷🇴",
    "Болгария": "🇧🇬", "Венгрия": "🇭🇺", "Грузия": "🇬🇪", "Армения": "🇦🇲",
    "Азербайджан": "🇦🇿", "Узбекистан": "🇺🇿", "Дания": "🇩🇰", "Норвегия": "🇳🇴",
    "Бельгия": "🇧🇪", "Португалия": "🇵🇹", "Греция": "🇬🇷", "Словакия": "🇸🇰",
    "Хорватия": "🇭🇷", "Словения": "🇸🇮", "Ирландия": "🇮🇪", "Люксембург": "🇱🇺",
    "Кипр": "🇨🇾", "Исландия": "🇮🇸", "Мальта": "🇲🇹", "Албания": "🇦🇱",
    "Македония": "🇲🇰", "Босния": "🇧🇦", "Черногория": "🇲🇪", "Косово": "🇽🇰",
}

PINNED_SERVERS = [
    "vless://00000000-0000-0000-0000-000000000001@104.16.0.1:443"
    "?type=tcp&security=tls&sni=cloudflare.com&fp=chrome&allowInsecure=1"
    "#" + quote("🌵 Telegram: @vpnkick_bot"),

    "vless://00000000-0000-0000-0000-000000000002@104.16.0.2:443"
    "?type=tcp&security=tls&sni=cloudflare.com&fp=chrome&allowInsecure=1"
    "#" + quote("❗️Нажмите 🔄 перед подключением❗️"),
]


RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
GRAY    = "\033[90m"

_log_lock = threading.Lock()


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log_info(msg: str):
    with _log_lock:
        print(f"  {GRAY}[{_ts()}]{RESET} {CYAN}ℹ{RESET}  {msg}")


def log_ok(msg: str):
    with _log_lock:
        print(f"  {GRAY}[{_ts()}]{RESET} {GREEN}✔{RESET}  {msg}")


def log_warn(msg: str):
    with _log_lock:
        print(f"  {GRAY}[{_ts()}]{RESET} {YELLOW}⚠{RESET}  {msg}")


def log_err(msg: str):
    with _log_lock:
        print(f"  {GRAY}[{_ts()}]{RESET} {RED}✘{RESET}  {msg}")


def log_event(icon: str, msg: str):
    with _log_lock:
        print(f"  {GRAY}[{_ts()}]{RESET} {MAGENTA}{icon}{RESET}  {msg}")


def log_user(action: str, uid: int, username: str | None, detail: str = ""):
    uname = f"@{username}" if username else f"ID:{uid}"
    extra = f"  {GRAY}{detail}{RESET}" if detail else ""
    with _log_lock:
        print(f"  {GRAY}[{_ts()}]{RESET} {BLUE}👤{RESET}  {WHITE}{uname}{RESET} {GRAY}({uid}){RESET} — {action}{extra}")


def log_admin(action: str, detail: str = ""):
    extra = f"  {GRAY}{detail}{RESET}" if detail else ""
    with _log_lock:
        print(f"  {GRAY}[{_ts()}]{RESET} {YELLOW}🛠{RESET}  {BOLD}ADMIN{RESET} — {action}{extra}")


def log_section(title: str):
    bar = "─" * 54
    with _log_lock:
        print(f"\n  {CYAN}{bar}{RESET}")
        print(f"  {CYAN}│{RESET}  {BOLD}{title}{RESET}")
        print(f"  {CYAN}{bar}{RESET}")


def print_banner():
    banner = f"""
{CYAN}╔══════════════════════════════════════════════════════╗{RESET}
{CYAN}║{RESET}  {BOLD}{WHITE}  ██╗  ██╗██╗ ██████╗██╗  ██╗    ██╗   ██╗██████╗ ███╗   ██╗  {RESET}{CYAN}║{RESET}
{CYAN}║{RESET}  {BOLD}{WHITE}  ██║ ██╔╝██║██╔════╝██║ ██╔╝    ██║   ██║██╔══██╗████╗  ██║  {RESET}{CYAN}║{RESET}
{CYAN}║{RESET}  {BOLD}{WHITE}  █████╔╝ ██║██║     █████╔╝     ██║   ██║██████╔╝██╔██╗ ██║  {RESET}{CYAN}║{RESET}
{CYAN}║{RESET}  {BOLD}{WHITE}  ██╔═██╗ ██║██║     ██╔═██╗     ╚██╗ ██╔╝██╔═══╝ ██║╚██╗██║  {RESET}{CYAN}║{RESET}
{CYAN}║{RESET}  {BOLD}{WHITE}  ██║  ██╗██║╚██████╗██║  ██╗     ╚████╔╝ ██║     ██║ ╚████║  {RESET}{CYAN}║{RESET}
{CYAN}║{RESET}  {BOLD}{WHITE}  ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝      ╚═══╝  ╚═╝     ╚═╝  ╚═══╝  {RESET}{CYAN}║{RESET}
{CYAN}║{RESET}                                                        {CYAN}║{RESET}
{CYAN}║{RESET}    {GREEN}Telegram VPN Bot{RESET}  {GRAY}·{RESET}  {YELLOW}@vpnkick_bot{RESET}  {GRAY}·{RESET}  {MAGENTA}v3.0 FREE{RESET}            {CYAN}║{RESET}
{CYAN}╚══════════════════════════════════════════════════════╝{RESET}
"""
    print(banner)


bot    = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp     = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)


class SupportState(StatesGroup):
    waiting_user_message = State()
    waiting_admin_reply  = State()
    waiting_user_reply   = State()


class BroadcastState(StatesGroup):
    waiting_message = State()
    waiting_confirm = State()


_db_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="db")


def _run_in_db(func):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(_db_executor, func)


def _init_db_sync():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id          INTEGER PRIMARY KEY,
            username         TEXT,
            full_name        TEXT,
            registered_at    TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()


async def init_db():
    await _run_in_db(_init_db_sync)


def _get_user_sync(user_id: int) -> dict | None:
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    cur = con.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


async def db_get_user(user_id: int) -> dict | None:
    return await _run_in_db(lambda: _get_user_sync(user_id))


def _upsert_user_sync(user_id, username, full_name):
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        con.execute(
            "INSERT INTO users (user_id, username, full_name, registered_at) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, datetime.now().isoformat()),
        )
    else:
        fields, vals = [], []
        if username  is not None: fields.append("username = ?");  vals.append(username)
        if full_name is not None: fields.append("full_name = ?"); vals.append(full_name)
        if fields:
            vals.append(user_id)
            con.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?", vals)
    con.commit()
    con.close()


async def db_upsert_user(user_id: int, username=None, full_name=None):
    await _run_in_db(lambda: _upsert_user_sync(user_id, username, full_name))


def _all_users_sync() -> list[dict]:
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM users").fetchall()
    con.close()
    return [dict(r) for r in rows]


async def db_all_users() -> list[dict]:
    return await _run_in_db(_all_users_sync)


def _find_by_username_sync(username: str) -> dict | None:
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT * FROM users WHERE LOWER(username) = LOWER(?)",
        (username.lstrip("@"),),
    ).fetchone()
    con.close()
    return dict(row) if row else None


async def db_find_by_username(username: str) -> dict | None:
    return await _run_in_db(lambda: _find_by_username_sync(username))


async def get_stats() -> dict:
    users = await db_all_users()
    return {"total": len(users)}


def _create_gist_sync() -> str | None:
    try:
        res = requests.post(
            "https://api.github.com/gists",
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={
                "description": "KICK VPN Free Config",
                "public": False,
                "files": {"servers.txt": {"content": "Initializing..."}}
            },
            timeout=30
        )
        if res.status_code == 201:
            gid = res.json()["id"]
            log_ok(f"Gist создан: {GRAY}{gid}{RESET}")
            return gid
    except Exception as e:
        log_err(f"Ошибка создания Gist: {e}")
    return None


def _get_free_gist_url() -> str | None:
    global FREE_GIST_ID
    if not FREE_GIST_ID:
        return None
    return f"https://gist.githubusercontent.com/rtx9785work-commits/{FREE_GIST_ID}/raw/servers.txt"


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛜 Подключить VPN",  callback_data="get_key")],
        [InlineKeyboardButton(text="👤 Мой аккаунт",    callback_data="my_account")],
        [InlineKeyboardButton(text="🆘 Поддержка",       callback_data="support")],
    ])


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="main_menu")]
    ])


WELCOME_TEXT = (
    "✨ <b>KICK VPN</b>\n\n"
    "🆓 <b>Полностью бесплатный VPN — навсегда!</b>\n\n"
    "🔐 Не подвержен замедлениям и блокировкам\n"
    "🚀 Высокая скорость соединения\n"
    "📍 Большое количество локаций\n"
    "📡 Серверы с обходом белых списков\n"
    "♾️ Без ограничений по трафику и времени\n\n"
    "<i>Выберите нужный пункт меню:</i>"
)

HOW_TO_USE_TEXT = (
    "📖 <b>Как пользоваться?</b>\n\n"
    "<b>Шаг 1.</b> Установите один из поддерживаемых VPN-клиентов:\n"
    "• <a href='https://apps.apple.com/app/v2raytun/id6476628951'>V2RayTun</a> — iOS\n"
    "• <a href='https://play.google.com/store/apps/details?id=com.v2ray.ang'>v2rayNG</a> — Android\n"
    "• <a href='https://apps.apple.com/app/streisand/id6450534064'>Streisand</a> — iOS / macOS\n"
    "• <a href='https://apps.apple.com/app/happ-proxy-utility/id6504287215'>Happ</a> — Android / iOS / Windows\n"
    "• <a href='https://hiddify.com/'>Hiddify</a> — Windows / Android / iOS / macOS\n\n"
    "<b>Шаг 2.</b> Скопируйте ссылку на подписку.\n\n"
    "<b>Шаг 3.</b> Откройте приложение, нажмите <b>«+»</b> и выберите "
    "<b>«Добавить по URL»</b> или <b>«Вставить из буфера обмена»</b>.\n\n"
    "<b>Шаг 4.</b> Нажмите <b>🔄 Обновить</b> в приложении и подключайтесь! 🚀"
)


_last_verified: list[dict] = []
_last_verified_lock = threading.Lock()


def _get_last_verified() -> list[dict]:
    with _last_verified_lock:
        return list(_last_verified)


def _set_last_verified(verified: list[dict]):
    global _last_verified
    with _last_verified_lock:
        _last_verified = list(verified)


@router.message(CommandStart())
async def cmd_start(message: Message):
    uid    = message.from_user.id
    user   = await db_get_user(uid)
    is_new = user is None

    await db_upsert_user(
        uid,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    if is_new:
        log_user("новый пользователь", uid, message.from_user.username, message.from_user.full_name or "")
        await bot.send_message(
            ADMIN_ID,
            f"👤 <b>Новый пользователь!</b>\n"
            f"@{message.from_user.username or 'нет'} | ID: <code>{uid}</code>\n"
            f"Имя: {message.from_user.full_name}",
        )
    else:
        log_user("/start", uid, message.from_user.username)

    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.callback_query(F.data == "my_account")
async def cb_my_account(call: CallbackQuery):
    user     = await db_get_user(call.from_user.id)
    username = call.from_user.username or "нет"
    uid      = call.from_user.id
    reg_str  = "неизвестно"

    if user and user.get("registered_at"):
        reg_str = datetime.fromisoformat(user["registered_at"]).strftime("%d.%m.%Y")

    await call.message.edit_text(
        f"👤 <b>Мой аккаунт</b>\n\n"
        f"<b>Username:</b> @{username}\n"
        f"<b>ID:</b> <code>{uid}</code>\n"
        f"<b>Дата регистрации:</b> {reg_str}\n\n"
        f"✅ <b>Статус:</b> Активен\n"
        f"♾️ <b>Подписка:</b> Бесплатная — бессрочно",
        reply_markup=back_kb(),
    )


@router.callback_query(F.data == "get_key")
async def cb_get_key(call: CallbackQuery):
    await call.message.edit_text("⏳ <b>Получаем ссылку на подписку...</b>")

    link = _get_free_gist_url()

    log_user("запросил ключ", call.from_user.id, call.from_user.username)

    if link:
        await call.message.edit_text(
            f"🆓 <b>KICK VPN — бесплатно и навсегда!</b>\n\n"
            f"{HOW_TO_USE_TEXT}\n\n"
            f"┌─────────────────────────\n"
            f"│ 🔗 <b>Ваша ссылка на подписку:</b>\n"
            f"└─────────────────────────\n"
            f"<code>{link}</code>\n\n"
            f"⚠️ <b>Важно:</b> Нажмите <b>🔄 Обновить</b> в приложении перед подключением.\n"
            f"Серверы автоматически обновляются каждый час.",
            reply_markup=back_kb(),
            disable_web_page_preview=True,
        )
    else:
        await call.message.edit_text(
            "⚠️ <b>Серверы ещё загружаются...</b>\n\n"
            "Подождите немного и попробуйте снова — список серверов обновляется при запуске.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="get_key")],
                [InlineKeyboardButton(text="⬅️ Назад",             callback_data="main_menu")],
            ]),
        )


@router.callback_query(F.data == "support")
async def cb_support(call: CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.waiting_user_message)
    await call.message.edit_text(
        "🆘 <b>Служба поддержки</b>\n\n"
        "Опишите вашу проблему или задайте вопрос — и мы ответим в ближайшее время.\n\n"
        "<i>Напишите сообщение прямо сейчас:</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
        ]),
    )


@router.message(SupportState.waiting_user_message)
async def user_support_message(message: Message, state: FSMContext):
    await state.clear()
    username     = message.from_user.username or "нет"
    uid          = message.from_user.id
    text_preview = (message.text or message.caption or "[медиафайл]")[:60]
    log_user("обращение в поддержку", uid, message.from_user.username, text_preview)
    await message.answer(
        "✅ <b>Сообщение отправлено.</b>\n\nОператор ответит в ближайшее время."
    )
    await bot.send_message(
        ADMIN_ID,
        f"🔔 <b>Новое обращение в поддержку</b>\n"
        f"👤 @{username} | ID: <code>{uid}</code>\n\n"
        f"<blockquote>{message.text or message.caption or '[медиафайл]'}</blockquote>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"admin_reply:{uid}:{username}")]
        ]),
    )


@router.callback_query(F.data.startswith("admin_reply:"))
async def cb_admin_reply(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Нет доступа.", show_alert=True)
        return
    parts    = call.data.split(":", 2)
    uid      = int(parts[1])
    username = parts[2]
    await state.set_state(SupportState.waiting_admin_reply)
    await state.update_data(target_user_id=uid, target_username=username)
    await call.message.answer(f"💬 Введите ответ для пользователя @{username}:")


@router.message(SupportState.waiting_admin_reply)
async def admin_reply_message(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data     = await state.get_data()
    uid      = data["target_user_id"]
    username = data["target_username"]
    await state.clear()
    log_admin(f"ответил пользователю @{username} (ID:{uid})")
    await message.answer(f"📤 Ответ отправлен @{username} (ID: <code>{uid}</code>).")
    await bot.send_message(
        uid,
        f"📩 <b>Ответ от оператора:</b>\n\n"
        f"<blockquote>{message.text or '[медиафайл]'}</blockquote>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"user_reply_op:{ADMIN_ID}")]
        ]),
    )


@router.callback_query(F.data.startswith("user_reply_op:"))
async def cb_user_reply_op(call: CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.waiting_user_reply)
    await state.update_data(target_user_id=ADMIN_ID)
    await call.message.answer("💬 Напишите ваше сообщение оператору:")


@router.message(SupportState.waiting_user_reply)
async def user_reply_message(message: Message, state: FSMContext):
    await state.clear()
    username     = message.from_user.username or "нет"
    uid          = message.from_user.id
    text_preview = (message.text or "[медиафайл]")[:60]
    log_user("ответ в поддержку", uid, message.from_user.username, text_preview)
    await message.answer("✅ Сообщение отправлено оператору.")
    await bot.send_message(
        ADMIN_ID,
        f"🔔 <b>Ответ от пользователя</b>\n"
        f"👤 @{username} | ID: <code>{uid}</code>\n\n"
        f"<blockquote>{message.text or '[медиафайл]'}</blockquote>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"admin_reply:{uid}:{username}")]
        ]),
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    log_admin("открыл панель администратора")
    s = await get_stats()
    await message.answer(
        "🛠 <b>Панель администратора</b>\n\n"
        f"👥 Всего пользователей: <b>{s['total']}</b>\n\n"
        "📋 <b>Команды:</b>\n"
        "<code>!sms @user текст</code> — написать пользователю\n"
        "<code>!users</code> — список пользователей\n"
        "<code>!broadcast</code> или <code>!bc</code> — рассылка всем\n"
        "<code>!stats</code> — статистика серверов"
    )


@router.message(F.text.regexp(r"^[`~!@#\"$%^&*.,/]users$"))
async def users_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    log_admin("запросил список пользователей")
    all_u = await db_all_users()
    if not all_u:
        await message.answer("📋 Нет пользователей.")
        return

    lines = [f"📋 <b>Все пользователи ({len(all_u)}):</b>\n"]
    for u in all_u:
        reg = datetime.fromisoformat(u["registered_at"]).strftime("%d.%m.%Y") if u.get("registered_at") else "?"
        uname = f"@{u['username']}" if u.get("username") else f"ID:{u['user_id']}"
        lines.append(f"👤 {uname} — с {reg}")

    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > 4000:
            await message.answer(chunk)
            chunk = line
        else:
            chunk += ("\n" if chunk else "") + line
    if chunk:
        await message.answer(chunk)


@router.message(F.text.regexp(r"^[`~!@#\"$%^&*.,/](broadcast|bc)$"))
async def broadcast_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    log_admin("начал рассылку")
    await state.set_state(BroadcastState.waiting_message)
    await message.answer(
        "📢 <b>Рассылка</b>\n\n"
        "Введите сообщение (HTML-форматирование поддерживается).",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel_entry")]
        ]),
    )


@router.callback_query(F.data == "broadcast_cancel_entry")
async def broadcast_cancel_entry(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return
    await state.clear()
    log_admin("отменил рассылку")
    await call.message.edit_text("❌ Рассылка отменена.")


@router.message(BroadcastState.waiting_message)
async def broadcast_received(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    text  = message.text or message.caption or ""
    total = len(await db_all_users())
    await state.update_data(broadcast_text=text)
    await state.set_state(BroadcastState.waiting_confirm)
    await message.answer(
        f"📢 <b>Подтверждение рассылки</b>\n\n"
        f"Сообщение будет отправлено <b>{total}</b> пользователям:\n\n"
        f"<blockquote>{text or '[медиа]'}</blockquote>\n\nПодтвердите:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Отменить",  callback_data="broadcast_cancel"),
        ]]),
    )


@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_confirm(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return
    data  = await state.get_data()
    text  = data.get("broadcast_text", "")
    await state.clear()
    users = await db_all_users()
    log_admin(f"подтвердил рассылку для {len(users)} пользователей")
    await call.message.edit_text(f"⏳ Рассылка для {len(users)} пользователей...")
    sent = failed = 0
    for u in users:
        try:
            await bot.send_message(u["user_id"], text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    log_admin(f"рассылка завершена — отправлено: {sent}, ошибок: {failed}")
    await call.message.answer(
        f"📢 <b>Рассылка завершена!</b>\n\n✅ Отправлено: <b>{sent}</b>\n❌ Не доставлено: <b>{failed}</b>"
    )


@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return
    await state.clear()
    log_admin("отменил рассылку")
    await call.message.edit_text("❌ Рассылка отменена.")


@router.message(F.text.regexp(r"^[`~!@#\"$%^&*.,/]stats$"))
async def stats_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    verified = _get_last_verified()
    by_country = defaultdict(int)
    for item in verified:
        by_country[item['country']] += 1
    lines = [f"📡 <b>Серверов в пуле: {len(verified)}</b>\n"]
    for country in COUNTRY_PROXIMITY_ORDER:
        if country in by_country:
            flag = FLAG_MAP.get(country, "🌐")
            lines.append(f"{flag} {country}: {by_country[country]}")
    await message.answer("\n".join(lines))


@router.message(F.text.regexp(r"^[`~!@#\"$%^&*.,/]sms\s+"))
async def sms_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    m = re.match(
        r"^[`~!@#\"$%^&*.,/]sms\s+@?(\S+)\s+(.+)$",
        message.text.strip(), re.IGNORECASE | re.DOTALL
    )
    if not m:
        await message.answer("❌ Пример: <code>!sms @username Ваш текст</code>")
        return
    target_raw, sms_text = m.group(1), m.group(2).strip()
    target = await _resolve_user(target_raw)
    if not target:
        await message.answer(f"❌ Пользователь <b>{target_raw}</b> не найден.")
        return
    try:
        await bot.send_message(
            target["user_id"],
            f"📩 <b>Сообщение от оператора:</b>\n\n<blockquote>{sms_text}</blockquote>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Ответить", callback_data=f"user_reply_op:{ADMIN_ID}")]
            ]),
        )
        log_admin(f"sms → @{target.get('username', '?')} (ID:{target['user_id']})")
        await message.answer(
            f"✅ Отправлено @{target.get('username', '?')} (ID: <code>{target['user_id']}</code>)."
        )
    except Exception:
        pass


async def _resolve_user(target_raw: str) -> dict | None:
    if target_raw.isdigit():
        return await db_get_user(int(target_raw))
    return await db_find_by_username(target_raw)


def _parse_vless(uri: str) -> dict | None:
    try:
        body = uri[8:]
        if '#' in body:
            body = body[:body.index('#')]
        uid_s, rest = body.split('@', 1)
        hostport, _, params_s = rest.partition('?')
        host, port_s = hostport.rsplit(':', 1)
        params: dict = {}
        for kv in params_s.split('&'):
            if '=' in kv:
                k, v = kv.split('=', 1)
                params[k] = unquote(v)
        host = host.strip('[]')
        sni  = params.get('sni') or params.get('serverName') or host
        flow = params.get('flow', '')
        pbk  = params.get('pbk', '')
        fp   = params.get('fp', 'chrome')
        sid  = params.get('sid', '')
        security = params.get('security', 'none').lower()
        net_type = params.get('type', 'tcp').lower()
        return {
            'uuid':     uid_s.strip(),
            'host':     host,
            'port':     int(port_s),
            'security': security,
            'sni':      sni,
            'pbk':      pbk,
            'fp':       fp,
            'sid':      sid,
            'flow':     flow,
            'type':     net_type,
        }
    except Exception:
        return None


def _build_vless_header(uuid_bytes: bytes, target_host: str, target_port: int) -> bytes:
    host_b = target_host.encode()
    return (
        b'\x00'
        + uuid_bytes
        + b'\x00'
        + b'\x01'
        + struct.pack('>H', target_port)
        + b'\x02'
        + bytes([len(host_b)])
        + host_b
    )


def _check_tcp_port(host: str, port: int) -> tuple[bool, float]:
    t0 = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=CHECK_TIMEOUT):
            return True, (time.monotonic() - t0) * 1000
    except Exception:
        return False, 9999.0


def _check_tls_handshake(host: str, port: int, sni: str) -> tuple[bool, float]:
    t0 = time.monotonic()
    try:
        raw = socket.create_connection((host, port), timeout=CHECK_TIMEOUT)
        raw.settimeout(CHECK_TIMEOUT)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
        ctx.set_ciphers('DEFAULT:@SECLEVEL=0')
        try:
            ctx.set_alpn_protocols(['h2', 'http/1.1'])
        except Exception:
            pass
        tls = ctx.wrap_socket(raw, server_hostname=sni, do_handshake_on_connect=True)
        tls.close()
        return True, (time.monotonic() - t0) * 1000
    except Exception:
        return False, 9999.0


def _check_vless_data_flow(host: str, port: int, sni: str, uuid_bytes: bytes, target_host: str = "1.1.1.1", target_port: int = 80) -> tuple[bool, float]:
    t0 = time.monotonic()
    try:
        raw = socket.create_connection((host, port), timeout=CHECK_TIMEOUT)
        raw.settimeout(CHECK_TIMEOUT)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
        ctx.set_ciphers('DEFAULT:@SECLEVEL=0')
        try:
            ctx.set_alpn_protocols(['h2', 'http/1.1'])
        except Exception:
            pass
        sock = ctx.wrap_socket(raw, server_hostname=sni, do_handshake_on_connect=True)
        header = _build_vless_header(uuid_bytes, target_host, target_port)
        http_req = (
            b"GET / HTTP/1.1\r\n"
            b"Host: " + target_host.encode() + b"\r\n"
            b"Connection: close\r\n\r\n"
        )
        sock.sendall(header + http_req)
        chunk = sock.recv(256)
        sock.close()
        if not chunk:
            return False, 9999.0
        if chunk[0] == 0x15:
            return False, 9999.0
        if chunk[0] != 0x00:
            return False, 9999.0
        return True, (time.monotonic() - t0) * 1000
    except Exception:
        return False, 9999.0


def _check_vless_reality(uri: str) -> tuple[bool, float]:
    parsed = _parse_vless(uri)
    if not parsed:
        return False, 9999.0
    try:
        uuid_bytes = bytes.fromhex(parsed['uuid'].replace('-', ''))
    except Exception:
        return False, 9999.0
    host, port, sec, sni = parsed['host'], parsed['port'], parsed['security'], parsed['sni']
    tcp_ok, tcp_lat = _check_tcp_port(host, port)
    if not tcp_ok:
        return False, 9999.0
    if sec in ('reality', 'tls', 'xtls'):
        tls_ok, tls_lat = _check_tls_handshake(host, port, sni)
        if not tls_ok:
            return False, 9999.0
        data_ok, data_lat = _check_vless_data_flow(host, port, sni, uuid_bytes)
        if not data_ok:
            return False, 9999.0
        return True, data_lat
    return tcp_ok, tcp_lat


def _to_raw(url: str) -> str:
    return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")


def _get_country(name: str) -> str:
    nl = name.lower()
    if 'anycast' in nl:
        return 'Россия'
    for eng, rus in COUNTRY_MAP.items():
        if eng.lower() in nl:
            return rus
    return name.split('-')[0].strip().split(' ')[0].strip()[:15]


def _fetch_reality_lines(url: str) -> list[str]:
    try:
        r = requests.get(_to_raw(url), timeout=20)
        if r.status_code != 200:
            return []
        out = []
        for line in r.text.splitlines():
            line = line.strip()
            if line.startswith('vless://') and '#' in line:
                if 'reality' in line.lower() or 'pbk=' in line.lower():
                    out.append(line)
        return out
    except Exception:
        return []


def _collect_candidates() -> list[dict]:
    seen, result = set(), []
    for url in BYPASS_SOURCES:
        lines = _fetch_reality_lines(url)
        for line in lines:
            raw_cfg, _, name_raw = line.partition('#')
            uri = raw_cfg.strip()
            if uri in seen:
                continue
            country = _get_country(unquote(name_raw))
            if country not in ALLOWED_COUNTRIES:
                continue
            seen.add(uri)
            result.append({'uri': uri, 'country': country, 'raw_config': uri})
    return result


_lock   = threading.Lock()
_p_done = _p_ok = _p_total = 0
_p_start_time: float = 0.0


def _render_progress_bar(done: int, total: int, ok: int, width: int = 30) -> str:
    if total == 0:
        return ""
    frac    = done / total
    filled  = int(width * frac)
    bar     = f"{GREEN}{'█' * filled}{GRAY}{'░' * (width - filled)}{RESET}"
    pct     = int(frac * 100)
    elapsed = time.monotonic() - _p_start_time
    speed   = done / elapsed if elapsed > 0 else 0
    eta     = (total - done) / speed if speed > 0 else 0
    return (
        f"  {bar} {WHITE}{pct:3d}%{RESET}  "
        f"{GREEN}✔ {ok}{RESET}  {GRAY}✘ {done - ok}{RESET}  "
        f"{CYAN}{done}/{total}{RESET}  "
        f"{GRAY}ETA {eta:.0f}s{RESET}"
    )


def _tick(ok: bool):
    global _p_done, _p_ok
    with _lock:
        _p_done += 1
        if ok:
            _p_ok += 1
        done  = _p_done
        ok_n  = _p_ok
        total = _p_total
    bar_line = _render_progress_bar(done, total, ok_n)
    sys.stdout.write(f"\r{bar_line}   ")
    sys.stdout.flush()


def _verify_all(candidates: list[dict]) -> list[dict]:
    global _p_done, _p_ok, _p_total, _p_start_time
    _p_done = _p_ok = 0
    _p_total      = len(candidates)
    _p_start_time = time.monotonic()
    good = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_map = {ex.submit(_check_vless_reality, c['uri']): c for c in candidates}
        for f in as_completed(fut_map, timeout=MAX_CHECK_SEC + 10):
            item = fut_map[f]
            try:
                ok, lat = f.result(timeout=1)
            except Exception:
                ok, lat = False, 9999.0
            _tick(ok)
            if ok:
                good.append({**item, 'latency': lat})
    sys.stdout.write("\n")
    return good


def _build_free_subscription(verified: list[dict]) -> str:
    header = (
        "#profile-title: 🚀 KICK VPN — Free\n"
        "#profile-update-interval: 1\n"
        "#subscription-userinfo: upload=0; download=0; total=0; expire=0\n"
    )

    by_country = defaultdict(list)
    for item in verified:
        by_country[item['country']].append(item)

    for c in by_country:
        by_country[c] = sorted(by_country[c], key=lambda x: x['latency'])[:5]

    ordered_countries = [c for c in COUNTRY_PROXIMITY_ORDER if c in by_country]
    lines = list(PINNED_SERVERS)

    for country in ordered_countries:
        servers = by_country[country]
        flag    = FLAG_MAP.get(country, '🌐')
        for i, s in enumerate(servers, 1):
            label = f"{flag} {country}" if len(servers) == 1 else f"{flag} {country} #{i}"
            lines.append(f"{s['raw_config']}#{quote(label)}")

    return header + "\n".join(lines) + "\n"


def _patch_gist_sync(gist_id: str, content: str):
    try:
        requests.patch(
            f"https://api.github.com/gists/{gist_id}",
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={"files": {"servers.txt": {"content": content}}},
            timeout=30
        )
    except Exception as e:
        log_err(f"Ошибка патча Gist {gist_id}: {e}")


def run_update():
    global FREE_GIST_ID

    if not FREE_GIST_ID:
        log_info("Создание общего Gist для бесплатной подписки...")
        FREE_GIST_ID = _create_gist_sync()
        if FREE_GIST_ID:
            log_ok(f"Общий Gist создан: {GRAY}{FREE_GIST_ID}{RESET}")
        else:
            log_err("Не удалось создать общий Gist!")
            return

    log_section(f"Обновление серверов  ·  {time.strftime('%d.%m.%Y %H:%M:%S')}")

    log_info("Загрузка кандидатов из источников...")
    candidates = _collect_candidates()
    if not candidates:
        log_warn("Кандидаты не найдены — пропуск цикла")
        return

    log_info(f"Найдено кандидатов: {WHITE}{len(candidates)}{RESET}  →  запуск проверки")
    print()

    t_check  = time.monotonic()
    verified = _verify_all(candidates)
    elapsed  = time.monotonic() - t_check

    log_ok(
        f"Проверка завершена за {WHITE}{elapsed:.1f}s{RESET}  "
        f"— рабочих: {GREEN}{len(verified)}{RESET} / {len(candidates)}"
    )

    _set_last_verified(verified)

    log_info("Обновление общего Gist...")
    content = _build_free_subscription(verified)
    _patch_gist_sync(FREE_GIST_ID, content)
    log_ok(f"Общий Gist обновлён: {GREEN}{len(verified)}{RESET} серверов")
    log_section("Цикл завершён")


async def updater_loop():
    loop = asyncio.get_running_loop()
    while True:
        try:
            await loop.run_in_executor(None, run_update)
        except Exception as e:
            log_err(f"Ошибка в цикле обновления: {e}")
        await asyncio.sleep(UPDATE_INTERVAL)


async def main():
    print_banner()
    log_section("Инициализация")
    log_info("Подключение к базе данных...")
    await init_db()
    log_ok("База данных готова")
    log_info("Запуск фонового обновления серверов...")
    asyncio.create_task(updater_loop())
    log_ok(f"Бот запущен  ·  Admin ID: {WHITE}{ADMIN_ID}{RESET}")
    log_section("Polling")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())