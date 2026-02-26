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

DB_PATH        = "platinum_vpn.db"

GITHUB_TOKEN   = "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"
GIST_ID        = "41b2637809a3be0ffab57b9493bed2a5"
GIST_RAW_URL   = f"https://gist.githubusercontent.com/rtx9785work-commits/{GIST_ID}/raw"
CLCK_API       = "https://clck.ru/--"

TRIAL_DAYS     = 30

MAX_TOTAL       = 100
MIN_TOTAL       = 50
CHECK_TIMEOUT   = 6
MAX_WORKERS     = 80
MAX_CHECK_SEC   = 110
UPDATE_INTERVAL = 3600

BYPASS_SOURCES = [
    "https://github.com/igareck/vpn-configs-for-russia/blob/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://github.com/igareck/vpn-configs-for-russia/blob/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
]

COUNTRY_PROXIMITY_ORDER = [
    "Россия",
    "Беларусь",
    "Казахстан",
    "Украина",
    "Молдова",
    "Грузия",
    "Армения",
    "Азербайджан",
    "Узбекистан",
    "Эстония",
    "Латвия",
    "Литва",
    "Финляндия",
    "Польша",
    "Румыния",
    "Болгария",
    "Венгрия",
    "Словакия",
    "Чехия",
    "Австрия",
    "Сербия",
    "Хорватия",
    "Словения",
    "Македония",
    "Босния",
    "Черногория",
    "Косово",
    "Швеция",
    "Норвегия",
    "Дания",
    "Германия",
    "Нидерланды",
    "Бельгия",
    "Люксембург",
    "Швейцария",
    "Франция",
    "Италия",
    "Испания",
    "Португалия",
    "Греция",
    "Кипр",
    "Мальта",
    "Ирландия",
    "Великобритания",
    "Исландия",
    "Албания",
    "Турция",
    "США",
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
    "#" + quote("⚡️ Telegram: @vpn_platinum_bot"),

    "vless://00000000-0000-0000-0000-000000000002@104.16.0.2:443"
    "?type=tcp&security=tls&sni=cloudflare.com&fp=chrome&allowInsecure=1"
    "#" + quote("⚠️ Если один сервер не работает, переключитесь на другой"),
]

GIST_HEADER = (
    "#profile-title: 🚀 Platinum VPN\n"
    "#profile-update-interval: 1\n"
    "#subscription-userinfo: upload=0; download=0; total=0; expire=2051222400\n"
)


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
            registered_at    TEXT NOT NULL,
            subscription_end TEXT,
            trial_used       INTEGER NOT NULL DEFAULT 0,
            is_trial         INTEGER NOT NULL DEFAULT 0
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


_UNSET = object()


def _upsert_user_sync(user_id, username, full_name, subscription_end, trial_used, is_trial):
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()

    if row is None:
        sub_val = None if (subscription_end is _UNSET) else subscription_end
        con.execute(
            """INSERT INTO users
               (user_id, username, full_name, registered_at,
                subscription_end, trial_used, is_trial)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                username if username is not _UNSET else None,
                full_name if full_name is not _UNSET else None,
                datetime.now().isoformat(),
                sub_val,
                int(trial_used) if (trial_used is not _UNSET and trial_used is not None) else 0,
                int(is_trial)   if (is_trial   is not _UNSET and is_trial   is not None) else 0,
            ),
        )
    else:
        fields, vals = [], []
        if username         is not _UNSET: fields.append("username = ?");         vals.append(username)
        if full_name        is not _UNSET: fields.append("full_name = ?");        vals.append(full_name)
        if subscription_end is not _UNSET: fields.append("subscription_end = ?"); vals.append(subscription_end)
        if trial_used       is not _UNSET: fields.append("trial_used = ?");       vals.append(int(trial_used) if trial_used is not None else 0)
        if is_trial         is not _UNSET: fields.append("is_trial = ?");         vals.append(int(is_trial)   if is_trial   is not None else 0)
        if fields:
            vals.append(user_id)
            con.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?", vals)

    con.commit()
    con.close()


async def db_upsert_user(
    user_id: int,
    username=_UNSET,
    full_name=_UNSET,
    subscription_end=_UNSET,
    trial_used=_UNSET,
    is_trial=_UNSET,
):
    await _run_in_db(lambda: _upsert_user_sync(
        user_id, username, full_name, subscription_end, trial_used, is_trial
    ))


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


def is_active(user: dict) -> bool:
    if not user or not user.get("subscription_end"):
        return False
    return datetime.fromisoformat(user["subscription_end"]) > datetime.now()


def calc_new_end(user: dict, delta: timedelta) -> str:
    base = (
        datetime.fromisoformat(user["subscription_end"])
        if is_active(user) else datetime.now()
    )
    return (base + delta).isoformat()


def parse_duration(s: str) -> timedelta | None:
    m = re.fullmatch(r"(\d+)([dwmy])", s.strip().lower())
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    return {
        "d": timedelta(days=n), "w": timedelta(weeks=n),
        "m": timedelta(days=n * 30), "y": timedelta(days=n * 365),
    }[unit]


async def resolve_user(target_raw: str) -> dict | None:
    if target_raw.isdigit():
        return await db_get_user(int(target_raw))
    return await db_find_by_username(target_raw)


async def get_stats() -> dict:
    users = await db_all_users()
    return {
        "total":   len(users),
        "active":  sum(1 for u in users if is_active(u) and not u.get("is_trial")),
        "trials":  sum(1 for u in users if is_active(u) and u.get("is_trial")),
        "expired": sum(1 for u in users if not is_active(u) and u.get("trial_used")),
    }


async def get_short_link() -> str | None:
    try:
        unique_url = f"{GIST_RAW_URL}?_={uuid_mod.uuid4().hex}"
        async with aiohttp.ClientSession() as session:
            async with session.get(
                CLCK_API, params={"url": unique_url},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return (await resp.text()).strip()
    except Exception as e:
        print(f"[clck.ru error] {e}")
    return None


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Пробный период",  callback_data="trial")],
        [InlineKeyboardButton(text="💎 Купить подписку", callback_data="buy")],
        [InlineKeyboardButton(text="🛜 Подключить VPN",  callback_data="get_key")],
        [InlineKeyboardButton(text="👤 Мой аккаунт",    callback_data="my_account")],
        [InlineKeyboardButton(text="🆘 Поддержка",       callback_data="support")],
    ])


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="main_menu")]
    ])


def buy_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 30 дней — 30⭐️",   callback_data="pay_30")],
        [InlineKeyboardButton(text="📅 90 дней — 80⭐️",   callback_data="pay_90")],
        [InlineKeyboardButton(text="📅 180 дней — 140⭐️", callback_data="pay_180")],
        [InlineKeyboardButton(text="📅 360 дней — 250⭐️", callback_data="pay_360")],
        [InlineKeyboardButton(text="⬅️ Назад",             callback_data="main_menu")],
    ])


WELCOME_TEXT = (
    "✨ <b>Platinum VPN</b>\n\n"
    "🔐 <b>Не подвержен замедлениям и блокировкам.</b>\n\n"
    "🚀 Высокая скорость соединения\n"
    "📍 Большое количество локаций\n"
    "📡 Серверы с обходом белых списков\n"
    f"🎁 Бесплатный пробный период — {TRIAL_DAYS} дней\n"
    "💸 Доступная стоимость\n"
    "⭐️ Оплата звёздами Telegram\n\n"
    "<i>Выберите нужный пункт меню ниже:</i>"
)

HOW_TO_USE_TEXT = (
    "📖 <b>Как пользоваться ключом?</b>\n\n"
    "<b>Шаг 1.</b> Установите один из поддерживаемых VPN-клиентов:\n"
    "• <a href='https://apps.apple.com/app/v2raytun/id6476628951'>V2RayTun</a> — iOS\n"
    "• <a href='https://play.google.com/store/apps/details?id=com.v2ray.ang'>v2rayNG</a> — Android\n"
    "• <a href='https://apps.apple.com/app/streisand/id6450534064'>Streisand</a> — iOS / macOS\n"
    "• <a href='https://apps.apple.com/app/happ-proxy-utility/id6504287215'>Happ</a> — Android / iOS / Windows\n"
    "• <a href='https://hiddify.com/'>Hiddify</a> — Windows / Android / iOS / macOS\n\n"
    "<b>Шаг 2.</b> Нажмите на ссылку ниже — она автоматически скопируется в буфер обмена.\n\n"
    "<b>Шаг 3.</b> Откройте приложение, нажмите <b>«+»</b> и выберите "
    "<b>«Вставить из буфера обмена»</b> или <b>«Добавить по URL»</b>.\n\n"
    "<b>Шаг 4.</b> Подключитесь и пользуйтесь интернетом без ограничений! 🚀"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    uid    = message.from_user.id
    is_new = (await db_get_user(uid)) is None

    await db_upsert_user(
        uid,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    if is_new:
        await bot.send_message(
            ADMIN_ID,
            f"👤 <b>Новый пользователь!</b>\n"
            f"@{message.from_user.username or 'нет'} | ID: <code>{uid}</code>\n"
            f"Имя: {message.from_user.full_name}",
        )

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

    if user and is_active(user):
        end       = datetime.fromisoformat(user["subscription_end"])
        days_left = (end - datetime.now()).days
        sub_type  = "🎁 Пробный период" if user.get("is_trial") else "💎 Платная подписка"
        status = (
            f"✅ <b>Статус:</b> Активна\n"
            f"<b>Тип:</b> {sub_type}\n"
            f"<b>Действует до:</b> {end.strftime('%d.%m.%Y %H:%M')}\n"
            f"<b>Осталось дней:</b> {days_left}"
        )
    else:
        status = "❌ <b>Статус:</b> Нет активной подписки"

    await call.message.edit_text(
        f"👤 <b>Мой аккаунт</b>\n\n"
        f"<b>Username:</b> @{username}\n"
        f"<b>ID:</b> <code>{uid}</code>\n"
        f"<b>Дата регистрации:</b> {reg_str}\n\n"
        f"{status}",
        reply_markup=back_kb(),
    )


@router.callback_query(F.data == "buy")
async def cb_buy(call: CallbackQuery):
    await call.message.edit_text(
        "💎 <b>Выберите тариф:</b>\n\n"
        "📅 <b>30 дней</b> — 30⭐️\n"
        "📅 <b>90 дней</b> — 80⭐️\n"
        "📅 <b>180 дней</b> — 140⭐️\n"
        "📅 <b>360 дней</b> — 250⭐️\n\n"
        "<i>Все серверы, все протоколы, никаких ограничений.</i>",
        reply_markup=buy_kb(),
    )


TARIFFS = {
    "pay_30":  (30,  30,  "30 дней",  "Platinum VPN — 30 дней"),
    "pay_90":  (90,  80,  "90 дней",  "Platinum VPN — 90 дней"),
    "pay_180": (180, 140, "180 дней", "Platinum VPN — 180 дней"),
    "pay_360": (360, 250, "360 дней", "Platinum VPN — 360 дней"),
}


@router.callback_query(F.data.in_({"pay_30", "pay_90", "pay_180", "pay_360"}))
async def cb_pay_tariff(call: CallbackQuery):
    days, stars, label, title = TARIFFS[call.data]
    await call.message.delete()
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=title,
        description=f"Доступ ко всем серверам. Срок действия — {label}.",
        payload=f"vpn_{days}d",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=label, amount=stars)],
    )


@router.pre_checkout_query()
async def pre_checkout(pcq: PreCheckoutQuery):
    await pcq.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    uid     = message.from_user.id
    user    = await db_get_user(uid) or {}
    payload = message.successful_payment.invoice_payload

    days_map = {"vpn_30d": 30, "vpn_90d": 90, "vpn_180d": 180, "vpn_360d": 360}
    days     = days_map.get(payload, 30)
    stars    = message.successful_payment.total_amount

    new_end = calc_new_end(user, timedelta(days=days))
    await db_upsert_user(
        uid,
        username=message.from_user.username,
        subscription_end=new_end,
        is_trial=False,
    )

    sub_end   = datetime.fromisoformat(new_end).strftime("%d.%m.%Y")
    label_map = {30: "30 дней", 90: "90 дней", 180: "180 дней", 360: "360 дней"}
    label     = label_map.get(days, f"{days} дней")

    await bot.send_message(
        ADMIN_ID,
        f"💰 <b>Новая оплата!</b>\n"
        f"@{message.from_user.username or 'нет'} | ID: <code>{uid}</code>\n"
        f"Тариф: {label} | {stars}⭐️\n"
        f"Подписка до: <b>{sub_end}</b>",
    )
    await message.answer(
        "❤️‍🔥 <b>Оплата прошла успешно — спасибо за покупку!</b>\n\n"
        f"Тариф: <b>{label}</b> — {stars}⭐️\n"
        f"Ваша подписка активна до <b>{sub_end}</b>.\n\n"
        "⚠️ <b>Примечание:</b> Некоторые серверы могут быть недоступны из-за блокировок "
        "Роскомнадзора. Если сервер не работает — попробуйте переключиться на другой.\n\n"
        "🔑 Перейдите в главное меню и нажмите <b>«Подключить VPN»</b>.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]),
    )


@router.callback_query(F.data == "get_key")
async def cb_get_key(call: CallbackQuery):
    user = await db_get_user(call.from_user.id)

    if user and is_active(user):
        await call.message.edit_text("⏳ <b>Получаем вашу ссылку...</b>")
        short_link = await get_short_link()
        end_str    = datetime.fromisoformat(user["subscription_end"]).strftime("%d.%m.%Y %H:%M:%S")
        days_left  = (datetime.fromisoformat(user["subscription_end"]) - datetime.now()).days

        if short_link:
            await call.message.edit_text(
                f"📅 Подписка действует до: <b>{end_str}</b> (осталось <b>{days_left} дн.</b>)\n\n"
                f"{HOW_TO_USE_TEXT}\n\n"
                f"<b>Ваша ссылка:</b>\n<code>{short_link}</code>\n\n"
                "⚠️ <b>Примечание:</b> Некоторые серверы могут быть недоступны из-за блокировок "
                "Роскомнадзора. Если один не работает — переключитесь на другой.",
                reply_markup=back_kb(),
                disable_web_page_preview=True,
            )
        else:
            await call.message.edit_text(
                f"📅 Подписка действует до: <b>{end_str}</b>\n\n"
                "⚠️ <b>Не удалось получить ссылку.</b>\nОбратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")],
                    [InlineKeyboardButton(text="⬅️ Назад",    callback_data="main_menu")],
                ]),
            )

    elif user and user.get("trial_used"):
        await call.message.edit_text(
            "🔑 <b>Получение ключа</b>\n\n"
            "❌ <b>Активная подписка не найдена.</b>\n\n"
            "Пробный период уже был использован. Оформите платную подписку.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💎 Купить подписку", callback_data="buy")],
                [InlineKeyboardButton(text="⬅️ Назад",           callback_data="main_menu")],
            ]),
        )
    else:
        await call.message.edit_text(
            "🔑 <b>Получение ключа</b>\n\n"
            "❌ <b>Активная подписка не найдена.</b>\n\n"
            "Оформите подписку или активируйте пробный период.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💎 Купить подписку", callback_data="buy")],
                [InlineKeyboardButton(text="🎁 Пробный период",  callback_data="trial")],
                [InlineKeyboardButton(text="⬅️ Назад",           callback_data="main_menu")],
            ]),
        )


@router.callback_query(F.data == "trial")
async def cb_trial(call: CallbackQuery):
    user = await db_get_user(call.from_user.id)

    if user and user.get("trial_used"):
        await call.answer("❌ Пробный период уже был использован.", show_alert=True)
        return
    if user and is_active(user):
        await call.answer("✅ У вас уже есть активная подписка!", show_alert=True)
        return

    trial_end = (datetime.now() + timedelta(days=TRIAL_DAYS)).isoformat()
    await db_upsert_user(
        call.from_user.id,
        username=call.from_user.username,
        subscription_end=trial_end,
        trial_used=True,
        is_trial=True,
    )

    end_str = datetime.fromisoformat(trial_end).strftime("%d.%m.%Y %H:%M:%S")
    await bot.send_message(
        ADMIN_ID,
        f"🎁 <b>Новый пробный период</b>\n"
        f"@{call.from_user.username or 'нет'} | ID: <code>{call.from_user.id}</code>\n"
        f"До: {datetime.fromisoformat(trial_end).strftime('%d.%m.%Y')}",
    )
    await call.message.edit_text(
        "🎉 <b>Пробный период успешно активирован!</b>\n\n"
        "В пробном периоде доступны все сервера.\n"
        f"📅 Действует до: <b>{end_str}</b>\n\n"
        "Нажмите <b>«Подключить VPN»</b> в главном меню, чтобы подключиться.",
        reply_markup=back_kb(),
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
    username = message.from_user.username or "нет"
    uid      = message.from_user.id
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
    username = message.from_user.username or "нет"
    uid      = message.from_user.id
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
    s = await get_stats()
    await message.answer(
        "🛠 <b>Панель администратора</b>\n\n"
        f"👥 Всего пользователей: <b>{s['total']}</b>\n"
        f"💎 Платных подписок: <b>{s['active']}</b>\n"
        f"🎁 Активных триалов: <b>{s['trials']}</b>\n"
        f"⏰ Истекших (без подписки): <b>{s['expired']}</b>\n\n"
        "📋 <b>Команды:</b>\n"
        "<code>!gift @user 30d</code> — подарить подписку\n"
        "<code>!revoke @user</code> — отозвать подписку\n"
        "<code>!sms @user текст</code> — написать пользователю\n"
        "<code>!users</code> — список активных пользователей\n"
        "<code>!broadcast</code> — рассылка всем пользователям\n\n"
        "Единицы: <code>d</code> дни · <code>w</code> недели · <code>m</code> месяцы · <code>y</code> годы"
    )


@router.message(F.text.regexp(r"^[`~!@#\"$%^&*.,/]gift\s+"))
async def gift_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    m = re.match(r"^[`~!@#\"$%^&*.,/]gift\s+@?(\S+)\s+(\S+)$", message.text.strip(), re.IGNORECASE)
    if not m:
        await message.answer("❌ Пример: <code>!gift @username 14d</code>")
        return
    target_raw, dur_str = m.group(1), m.group(2)
    delta = parse_duration(dur_str)
    if not delta:
        await message.answer("❌ Неверный срок. Примеры: <code>7d</code>, <code>2w</code>, <code>1m</code>")
        return
    target = await resolve_user(target_raw)
    if not target:
        await message.answer(f"❌ Пользователь <b>{target_raw}</b> не найден.")
        return

    new_end = calc_new_end(target, delta)
    await db_upsert_user(target["user_id"], subscription_end=new_end, is_trial=False)
    end_str = datetime.fromisoformat(new_end).strftime("%d.%m.%Y %H:%M:%S")
    await message.answer(
        f"🎁 Подписка подарена <b>@{target.get('username', target_raw)}</b> "
        f"(ID: <code>{target['user_id']}</code>) на <b>{dur_str}</b>."
    )
    try:
        await bot.send_message(
            target["user_id"],
            f"🎁 <b>Администратор подарил вам подписку на {dur_str}!</b>\n\n"
            f"📅 Действует до: <b>{end_str}</b>",
        )
    except Exception:
        await message.answer("⚠️ <i>Не удалось уведомить пользователя.</i>")


@router.message(F.text.regexp(r"^[`~!@#\"$%^&*.,/]revoke\s+"))
async def revoke_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    m = re.match(r"^[`~!@#\"$%^&*.,/]revoke\s+@?(\S+)$", message.text.strip(), re.IGNORECASE)
    if not m:
        await message.answer("❌ Пример: <code>!revoke @username</code>")
        return
    target = await resolve_user(m.group(1))
    if not target:
        await message.answer(f"❌ Пользователь <b>{m.group(1)}</b> не найден.")
        return
    await db_upsert_user(target["user_id"], subscription_end=None, is_trial=False)
    await message.answer(
        f"🚫 Подписка отозвана у <b>@{target.get('username', '?')}</b> "
        f"(ID: <code>{target['user_id']}</code>)."
    )
    try:
        await bot.send_message(
            target["user_id"],
            "⚠️ <b>Ваша подписка была деактивирована администратором.</b>\n\n"
            "Если вы считаете это ошибкой, обратитесь в поддержку.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
            ]),
        )
    except Exception:
        await message.answer("⚠️ <i>Не удалось уведомить пользователя.</i>")


@router.message(F.text.regexp(r"^[`~!@#\"$%^&*.,/]users$"))
async def users_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    all_u  = await db_all_users()
    active = sorted([u for u in all_u if is_active(u)], key=lambda u: u.get("subscription_end", ""))
    if not active:
        await message.answer("📋 Нет активных пользователей.")
        return

    lines = ["📋 <b>Активные пользователи:</b>\n"]
    for u in active:
        end       = datetime.fromisoformat(u["subscription_end"]).strftime("%d.%m.%Y")
        days_left = (datetime.fromisoformat(u["subscription_end"]) - datetime.now()).days
        tag       = "🎁" if u.get("is_trial") else "💎"
        uname     = f"@{u['username']}" if u.get("username") else f"ID:{u['user_id']}"
        lines.append(f"{tag} {uname} — до {end} ({days_left} дн.)")

    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > 4000:
            await message.answer(chunk)
            chunk = line
        else:
            chunk += ("\n" if chunk else "") + line
    if chunk:
        await message.answer(chunk)


@router.message(F.text.regexp(r"^[`~!@#\"$%^&*.,/]broadcast$"))
async def broadcast_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(BroadcastState.waiting_message)
    await message.answer(
        "📢 <b>Рассылка</b>\n\nВведите сообщение (HTML-форматирование поддерживается).\n\n"
        "Напишите <code>отмена</code> для отмены."
    )


@router.message(BroadcastState.waiting_message)
async def broadcast_received(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text and message.text.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Рассылка отменена.")
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
            InlineKeyboardButton(text="❌ Отмена",    callback_data="broadcast_cancel"),
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
    await call.message.edit_text(f"⏳ Рассылка для {len(users)} пользователей...")
    sent = failed = 0
    for u in users:
        try:
            await bot.send_message(u["user_id"], text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await call.message.answer(
        f"📢 <b>Рассылка завершена!</b>\n\n✅ Отправлено: <b>{sent}</b>\n❌ Не доставлено: <b>{failed}</b>"
    )


@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await call.message.edit_text("❌ Рассылка отменена.")


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
    target = await resolve_user(target_raw)
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
        await message.answer(
            f"✅ Отправлено @{target.get('username', '?')} (ID: <code>{target['user_id']}</code>)."
        )
    except Exception:
        await message.answer("⚠️ <i>Не удалось отправить — бот заблокирован пользователем.</i>")


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
        return {
            'uuid':     uid_s.strip(),
            'host':     host,
            'port':     int(port_s),
            'security': params.get('security', 'none').lower(),
            'sni':      sni,
        }
    except Exception:
        return None


def _build_vless_header(uuid_bytes: bytes) -> bytes:
    target = b'1.1.1.1'
    return (
        b'\x00'
        + uuid_bytes
        + b'\x00'
        + b'\x01'
        + struct.pack('>H', 80)
        + b'\x02'
        + bytes([len(target)])
        + target
    )


def _check_vless_reality(uri: str) -> tuple[bool, float]:
    """Returns (is_alive, latency_ms). latency_ms=9999 if dead."""
    parsed = _parse_vless(uri)
    if not parsed:
        return False, 9999.0

    try:
        uuid_bytes = bytes.fromhex(parsed['uuid'].replace('-', ''))
        assert len(uuid_bytes) == 16
    except Exception:
        return False, 9999.0

    host = parsed['host']
    port = parsed['port']
    sec  = parsed['security']
    sni  = parsed['sni']

    t_start = time.monotonic()

    try:
        sock = socket.create_connection((host, port), timeout=CHECK_TIMEOUT)
        sock.settimeout(CHECK_TIMEOUT)
    except Exception:
        return False, 9999.0

    try:
        if sec in ('reality', 'tls', 'xtls'):
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode    = ssl.CERT_NONE
            ctx.set_ciphers('DEFAULT:@SECLEVEL=0')
            try:
                ctx.set_alpn_protocols(['h2', 'http/1.1'])
            except Exception:
                pass
            try:
                sock = ctx.wrap_socket(
                    sock,
                    server_hostname=sni,
                    do_handshake_on_connect=True,
                )
            except ssl.SSLError:
                return False, 9999.0
            except OSError:
                return False, 9999.0

        header = _build_vless_header(uuid_bytes)
        sock.sendall(header)

        sock.settimeout(CHECK_TIMEOUT)
        try:
            chunk = sock.recv(128)
            if chunk and len(chunk) >= 2 and chunk[0] == 0x15:
                return False, 9999.0
            latency = (time.monotonic() - t_start) * 1000
            return True, latency
        except socket.timeout:
            latency = (time.monotonic() - t_start) * 1000
            return True, latency
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            return False, 9999.0

    except Exception:
        return False, 9999.0
    finally:
        try:
            sock.close()
        except Exception:
            pass


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
            if not line or not line.startswith('vless://') or '#' not in line:
                continue
            lo = line.lower()
            if 'reality' in lo or 'pbk=' in lo:
                out.append(line)
        return out
    except Exception:
        return []


def _collect_candidates() -> list[dict]:
    print("  Загрузка Reality-источников...", flush=True)
    seen:   set  = set()
    result: list = []

    for url in BYPASS_SOURCES:
        lines = _fetch_reality_lines(url)
        fname = url.split('/')[-1]
        added = 0
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
            added += 1
        print(f"    {fname}: {len(lines)} строк → {added} Reality-кандидатов")

    print(f"  Итого кандидатов: {len(result)}")
    return result


_lock   = threading.Lock()
_p_done = _p_ok = _p_total = 0


def _tick(ok: bool):
    global _p_done, _p_ok
    with _lock:
        _p_done += 1
        if ok:
            _p_ok += 1
        d, t, o = _p_done, _p_total, _p_ok
    filled = int(40 * d / max(t, 1))
    pct    = 100.0 * d / max(t, 1)
    bar    = '█' * filled + '░' * (40 - filled)
    sys.stdout.write(f'\r  [{bar}] {pct:5.1f}%  ✅ {o}  ❌ {d-o}  ({d}/{t})')
    sys.stdout.flush()


def _verify_all(candidates: list[dict]) -> list[dict]:
    global _p_done, _p_ok, _p_total
    _p_done = _p_ok = 0
    _p_total = len(candidates)
    deadline = time.time() + MAX_CHECK_SEC
    good: list[dict] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_map      = {ex.submit(_check_vless_reality, c['uri']): c for c in candidates}
        timeout_left = max(5.0, deadline - time.time() + 5)
        for f in as_completed(fut_map, timeout=timeout_left):
            item = fut_map[f]
            try:
                ok, latency = f.result(timeout=1)
            except Exception:
                ok, latency = False, 9999.0
            _tick(ok)
            if ok:
                good.append({**item, 'latency': latency})

    print()
    return good


def _select_best_per_country(items: list[dict]) -> dict[str, list[dict]]:
    by_country: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_country[item['country']].append(item)
    result = {}
    for country, servers in by_country.items():
        result[country] = sorted(servers, key=lambda x: x.get('latency', 9999.0))
    return result


def _build_subscription(verified: list[dict]) -> str:
    by_country = _select_best_per_country(verified)

    countries_present = [c for c in COUNTRY_PROXIMITY_ORDER if c in by_country]
    countries_other   = [c for c in by_country if c not in set(COUNTRY_PROXIMITY_ORDER)]
    ordered_countries = countries_present + countries_other

    available_slots = MAX_TOTAL - len(PINNED_SERVERS)
    num_countries   = len(ordered_countries)

    if num_countries == 0:
        return GIST_HEADER + "\n".join(PINNED_SERVERS) + "\n"

    base_per_country = max(1, available_slots // num_countries)
    extra_slots      = available_slots - base_per_country * num_countries

    alloc: dict[str, int] = {}
    for country in ordered_countries:
        alloc[country] = min(base_per_country, len(by_country[country]))

    remaining = available_slots - sum(alloc.values())
    for country in ordered_countries:
        if remaining <= 0:
            break
        can_add = len(by_country[country]) - alloc[country]
        if can_add > 0:
            add = min(can_add, remaining)
            alloc[country] += add
            remaining -= add

    lines = list(PINNED_SERVERS)
    country_total = {c: alloc[c] for c in ordered_countries}
    country_seen: Counter = Counter()

    for country in ordered_countries:
        servers = by_country[country][:alloc[country]]
        flag    = FLAG_MAP.get(country, '🌐')
        total   = country_total[country]
        for server in servers:
            country_seen[country] += 1
            n     = country_seen[country]
            label = f"{flag} {country}" if total == 1 else f"{flag} {country} #{n}"
            lines.append(f"{server['raw_config']}#{quote(label)}")

    return GIST_HEADER + "\n".join(lines) + "\n"


def _push_to_gist(content: str) -> bool:
    try:
        res = requests.patch(
            f"https://api.github.com/gists/{GIST_ID}",
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={"files": {"servers.txt": {"content": content}}},
            timeout=30,
        )
        if res.status_code != 200:
            print(f"  [Gist error] status={res.status_code} body={res.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"  [Gist error] {e}")
        return False


def run_update():
    t0 = time.time()
    print(f"\n{'═'*62}")
    print(f"  🚀 Platinum VPN Updater  |  {time.strftime('%H:%M:%S  %d.%m.%Y')}")
    print(f"{'═'*62}\n")

    candidates = _collect_candidates()
    if not candidates:
        print("  ⚠️  Нет кандидатов. Проверьте источники.")
        return

    print(f"\n  Проверка {len(candidates)} Reality-серверов "
          f"({MAX_WORKERS} потоков, лимит {MAX_CHECK_SEC} с)...\n")
    verified  = _verify_all(candidates)
    total_ok  = len(verified)
    elapsed   = time.time() - t0
    print(f"\n  Готово за {elapsed:.0f} с  |  рабочих Reality: {total_ok}")

    if total_ok < MIN_TOTAL:
        print(f"  ⚠️  Мало серверов ({total_ok} < {MIN_TOTAL}).")

    content  = _build_subscription(verified)
    srv_cnt  = content.count('\nvless://') + content.count('\nvless://')
    print(f"  Итого в подписке: до {MAX_TOTAL} серверов (+ {len(PINNED_SERVERS)} информационных)")

    print("\n  Отправка в Gist...", end=" ", flush=True)
    if _push_to_gist(content):
        print(f"✅  (полный цикл: {time.time()-t0:.0f} с)")
    else:
        print("❌ Ошибка!")


async def updater_loop():
    loop = asyncio.get_running_loop()
    while True:
        try:
            await loop.run_in_executor(None, run_update)
        except Exception as e:
            print(f"[updater error] {e}")
        print(f"\n  Следующий цикл через {UPDATE_INTERVAL // 60} минут...\n")
        await asyncio.sleep(UPDATE_INTERVAL)


async def main():
    await init_db()
    asyncio.create_task(updater_loop())
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())

