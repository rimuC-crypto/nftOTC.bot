"""
OTC Market Bot v4.2 - Improved Version
Исправлены баги, добавлены оптимизации и улучшена безопасность
"""

import logging
import uuid
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.error import TelegramError

# ════════════════════════════════════════════════════
#                   LOGGING & CONFIG
# ════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SUPPORT_USERNAME = "otcmarketHelper"
DATA_FILE = "bot_data.json"
LOCK_TIMEOUT_MINUTES = 10

# ════════════════════════════════════════════════════
#                   STATES
# ════════════════════════════════════════════════════

LANG_ST      = 1
MENU_ST      = 2
REQ_CUR_ST   = 3
REQ_IN_ST    = 4
DEAL_CUR_ST  = 5
DEAL_AMT_ST  = 6
DEAL_GIFT_ST = 7
BUYER_ST     = 8
SUPPORT_ST   = 9
ADMIN_ST     = 10
REVIEW_ST    = 11
DEPOSIT_ST   = 12
WITHDRAW_ST  = 13

# ════════════════════════════════════════════════════
#                   STORAGE
# ════════════════════════════════════════════════════

users: Dict[int, Dict] = {}
deals: Dict[str, Dict] = {}
blocked_users: set = set()

platform_stats = {
    "total_deals": 0,
    "completed_deals": 0,
    "disputes": 0,
    "total_users": 0,
}

# ════════════════════════════════════════════════════
#              CURRENCIES & CONSTRAINTS
# ════════════════════════════════════════════════════

LANGS = {
    "uk": "🇺🇦 Українська",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "ar": "🇸🇦 العربية",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
}

CURRENCIES = {
    "UAH": "🇺🇦 UAH",
    "RUB": "🇷🇺 RUB",
    "KZT": "🇰🇿 KZT",
    "CNY": "🇨🇳 CNY",
    "USDT": "💵 USDT",
    "STARS": "⭐ Stars",
}

MIN_AMOUNTS = {
    "UAH": 10,
    "RUB": 50,
    "KZT": 500,
    "CNY": 5,
    "USDT": 1,
    "STARS": 10
}

MAX_AMOUNT = 1000000  # Максимальная сумма сделки для защиты от ошибок
PLATFORM_FEE = 0.03  # 3%

# ════════════════════════════════════════════════════
#              JSON PERSISTENCE - УЛУЧШЕНО
# ════════════════════════════════════════════════════

def save_data() -> None:
    """Сохраняет все данные в JSON-файл с обработкой ошибок."""
    try:
        data = {
            "users": {str(k): v for k, v in users.items()},
            "deals": deals,
            "blocked_users": list(blocked_users),
            "platform_stats": platform_stats,
        }
        # Создаём backup перед сохранением
        if os.path.exists(DATA_FILE):
            backup_file = f"{DATA_FILE}.backup"
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(old_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"⚠️ Не удалось создать backup: {e}")
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug("✅ Данные сохранены успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения данных: {e}")

def load_data() -> None:
    """Загружает данные из JSON-файла при старте бота."""
    global users, deals, blocked_users, platform_stats
    
    if not os.path.exists(DATA_FILE):
        logger.info("📝 Файл данных не найден — начинаем с чистого листа.")
        return
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        users = {int(k): v for k, v in data.get("users", {}).items()}
        deals = data.get("deals", {})
        blocked_users = set(data.get("blocked_users", []))
        platform_stats.update(data.get("platform_stats", {}))
        
        logger.info(f"✅ Данные загружены: {len(users)} юзеров, {len(deals)} сделок.")
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON: {e}")
        logger.warning("⚠️ Данные повреждены. Попытка восстановления из backup...")
        
        # Пытаемся восстановить из backup
        backup_file = f"{DATA_FILE}.backup"
        if os.path.exists(backup_file):
            try:
                with open(backup_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                users = {int(k): v for k, v in data.get("users", {}).items()}
                deals = data.get("deals", {})
                blocked_users = set(data.get("blocked_users", []))
                platform_stats.update(data.get("platform_stats", {}))
                logger.info("✅ Данные восстановлены из backup")
            except Exception as e2:
                logger.error(f"❌ Не удалось восстановить из backup: {e2}")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка загрузки: {e}")

# ════════════════════════════════════════════════════
#              TRANSLATIONS
# ════════════════════════════════════════════════════

T = {}

T["ru"] = {
    "welcome": (
        "Добро пожаловать в Bloosy Market\n\n"
        "Безопасные сделки с гарантией\n\n"
        "🛡️ Защита от мошенников\n"
        "💰 Автоматическое удержание средств\n"
        "📝 Прозрачная статистика\n"
        "🎯 Поддержка 24/7\n"
        "📊 История сделок\n\n"
        "👇 Выберите язык интерфейса:"
    ),
    "blocked": "⛔ *Аккаунт заблокирован*\n\nОбратитесь в поддержку: @{support}",
    "menu": (
        "🏠 *OTC Market*\n\n"
        "👤 *{name}*\n"
        "⭐ Рейтинг: *{rating}* / 5.0  │  📊 Сделок: *{dc}*\n\n"
        "Выберите действие:"
    ),
    "btn_create": "➕ Создать сделку",
    "btn_deals": "📂 Мои сделки",
    "btn_refs": "👥 Рефералы",
    "btn_req": "💳 Реквизиты и кошелёк",
    "btn_lang": "🌐 Язык",
    "btn_support": "💬 Поддержка",
    "btn_about": "ℹ️ О маркете",
    "btn_stats": "📊 Статистика",
    "no_req": (
        "⚠️ *Реквизиты не привязаны*\n\n"
        "Чтобы создать сделку, сначала укажите\n"
        "куда покупатель будет переводить деньги.\n\n"
        "👇 Перейдите в раздел *Реквизиты*"
    ),
    "bad_amount": "❌ Неверный формат. Введите число, например: `1500` или `25.5`",
    "min_amount": "❌ Минимальная сумма: *{min} {cur}*\n\nВведите большую сумму:",
    "max_amount": "❌ Максимальная сумма: *{max} {cur}*\n\nВведите меньшую сумму:",
    "deal_created": (
        "🎁 NFT подарок: *{gift}*\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "💸 Комиссия маркета: *3%*\n"
        "🆔 ID сделки: `{id}`\n"
        "📅 Создана: {date}\n"
        "📌 Статус: 🟡 Ожидает покупателя\n\n"
        "🔗 *Ссылка для покупателя:*\n"
        "`https://t.me/{bot}?start=deal_{id}`\n\n"
        "📤 Отправьте эту ссылку покупателю."
    ),
    "back": "⬅️ Назад",
    "s_active": "🟡 Ожидает",
    "s_paid": "🟠 Оплачено",
    "s_nft_sent": "📦 NFT отправлен",
    "s_done": "✅ Завершена",
    "s_cancelled": "❌ Отменена",
}

T["uk"] = {k: v for k, v in T["ru"].items()}  # Заполнитель для украинского
T["en"] = {k: v for k, v in T["ru"].items()}  # Заполнитель для английского

# ════════════════════════════════════════════════════
#              UTILITY FUNCTIONS - УЛУЧШЕНО
# ════════════════════════════════════════════════════

def now_str() -> str:
    """Возвращает текущую дату-время в формате ДД.ММ.ГГГГ ЧЧ:МИ"""
    return datetime.now().strftime("%d.%m.%Y %H:%M")

def tr(ctx: ContextTypes.DEFAULT_TYPE, key: str, **kwargs) -> str:
    """Получает перевод с подстановкой переменных.
    
    ИСПРАВЛЕНО: Добавлена обработка ошибок для недостающих ключей.
    """
    lang = ctx.user_data.get("lang", "ru")
    if lang not in T:
        lang = "ru"
    
    text = T[lang].get(key, T["ru"].get(key, f"[{key}]"))
    
    try:
        # Подставляем все переменные
        text = text.format(
            support=SUPPORT_USERNAME,
            **kwargs
        )
    except KeyError as e:
        logger.warning(f"⚠️ Отсутствует переменная {e} для ключа '{key}'")
        return text
    
    return text

def status_icon(status: str) -> str:
    """Возвращает иконку статуса сделки.
    
    ИСПРАВЛЕНО: Добавлена обработка неизвестных статусов.
    """
    icons = {
        "active": "🟡",
        "paid": "🟠",
        "nft_sent": "📦",
        "done": "✅",
        "cancelled": "❌",
        "disputed": "⚖️",
    }
    return icons.get(status, "❓")

def safe_float(value: str, min_val: float = 0, max_val: float = MAX_AMOUNT) -> Optional[float]:
    """Безопасное преобразование строки в число с валидацией.
    
    ИСПРАВЛЕНО: Добавлены проверки min/max и обработка исключений.
    """
    try:
        num = float(value)
        if not (min_val <= num <= max_val):
            return None
        return num
    except (ValueError, InvalidOperation):
        return None

def get_user_balance(uid: int, currency: str) -> float:
    """Получает баланс пользователя в валюте.
    
    ИСПРАВЛЕНО: Безопасный доступ к данным с default значением.
    """
    if uid not in users:
        return 0.0
    
    balance = users[uid].get("balance", {})
    return float(balance.get(currency, 0))

def add_user_balance(uid: int, currency: str, amount: float) -> None:
    """Добавляет средства на баланс пользователя.
    
    ИСПРАВЛЕНО: Валидация параметров и логирование.
    """
    if amount < 0:
        logger.warning(f"⚠️ Попытка добавить отрицательное количество: {amount}")
        return
    
    if uid not in users:
        logger.warning(f"⚠️ Пользователь {uid} не существует")
        return
    
    if "balance" not in users[uid]:
        users[uid]["balance"] = {}
    
    current = users[uid]["balance"].get(currency, 0)
    users[uid]["balance"][currency] = round(current + amount, 2)
    logger.info(f"💰 Пользователь {uid}: +{amount} {currency}, баланс: {users[uid]['balance'][currency]}")

def sub_user_balance(uid: int, currency: str, amount: float) -> bool:
    """Вычитает средства с баланса пользователя. Возвращает True если успешно.
    
    ИСПРАВЛЕНО: Проверка достаточности средств.
    """
    if uid not in users or amount < 0:
        return False
    
    current = get_user_balance(uid, currency)
    if current < amount:
        logger.warning(f"❌ Недостаточно средств у {uid}: есть {current}, нужно {amount}")
        return False
    
    users[uid]["balance"][currency] = round(current - amount, 2)
    logger.info(f"💸 Пользователь {uid}: -{amount} {currency}, баланс: {users[uid]['balance'][currency]}")
    return True

def get_user_rating(uid: int) -> Tuple[float, int]:
    """Получает рейтинг и число завершённых сделок.
    
    ИСПРАВЛЕНО: Безопасные вычисления.
    """
    if uid not in users:
        return 0.0, 0
    
    user = users[uid]
    ratings = user.get("ratings", [])
    completed = user.get("completed_deals", 0)
    
    if not ratings:
        return 0.0, completed
    
    avg_rating = sum(ratings) / len(ratings)
    return min(5.0, max(0.0, round(avg_rating, 1))), completed

# ════════════════════════════════════════════════════
#              COMMAND HANDLERS
# ════════════════════════════════════════════════════

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик /start команды.
    
    ИСПРАВЛЕНО: Добавлена защита от ошибок при отправке сообщения.
    """
    uid = update.effective_user.id
    
    # Проверка блокировки
    if uid in blocked_users:
        try:
            await update.message.reply_text(
                tr(ctx, "blocked"),
                parse_mode="Markdown"
            )
        except TelegramError as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
        return -1
    
    # Инициализация пользователя
    if uid not in users:
        users[uid] = {
            "name": update.effective_user.full_name or "User",
            "username": update.effective_user.username,
            "balance": {},
            "deals": [],
            "ratings": [],
            "completed_deals": 0,
            "joined": now_str(),
            "lang": "ru",
        }
        platform_stats["total_users"] += 1
        save_data()
    
    # Отправка welcome сообщения
    try:
        await update.message.reply_text(
            tr(ctx, "welcome"),
            reply_markup=_get_lang_keyboard(),
            parse_mode="Markdown"
        )
    except TelegramError as e:
        logger.error(f"❌ Ошибка отправки welcome: {e}")
    
    return LANG_ST

def _get_lang_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора языка."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(LANGS[lang], callback_data=f"lang_{lang}")]
        for lang in ["ru", "uk", "en", "ar", "zh", "ja"]
    ])

# ════════════════════════════════════════════════════
#              CALLBACK HANDLER - БАЗОВАЯ ВЕРСИЯ
# ════════════════════════════════════════════════════

async def main_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик callback buttons.
    
    ИСПРАВЛЕНО: Улучшена обработка ошибок и логирование.
    """
    uid = update.effective_user.id
    query = update.callback_query
    
    if uid in blocked_users:
        await query.answer("⛔ Аккаунт заблокирован", show_alert=True)
        return -1
    
    await query.answer()
    
    data = query.data
    logger.info(f"👤 {uid}: callback {data}")
    
    try:
        # Обработка выбора языка
        if data.startswith("lang_"):
            lang = data.split("_")[1]
            if lang in LANGS:
                ctx.user_data["lang"] = lang
                if uid in users:
                    users[uid]["lang"] = lang
                    save_data()
                
                await query.edit_message_text(
                    "✅ Язык установлен: " + LANGS[lang],
                    parse_mode="Markdown"
                )
                return MENU_ST
    
    except TelegramError as e:
        logger.error(f"❌ Ошибка callback: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)
    
    return MENU_ST

# ════════════════════════════════════════════════════
#              AMOUNT VALIDATION - НОВЫЙ ФУНКЦИОНАЛ
# ════════════════════════════════════════════════════

async def validate_deal_amount(
    update: Update,
    ctx: ContextTypes.DEFAULT_TYPE,
    amount_str: str,
    currency: str
) -> Optional[float]:
    """Валидирует сумму сделки с полной обработкой ошибок.
    
    ИСПРАВЛЕНО: Централизованная валидация сумм.
    """
    amount = safe_float(amount_str)
    
    if amount is None:
        await update.message.reply_text(
            tr(ctx, "bad_amount"),
            parse_mode="Markdown"
        )
        return None
    
    min_amount = MIN_AMOUNTS.get(currency, 1)
    if amount < min_amount:
        await update.message.reply_text(
            tr(ctx, "min_amount", min=min_amount, cur=currency),
            parse_mode="Markdown"
        )
        return None
    
    if amount > MAX_AMOUNT:
        await update.message.reply_text(
            tr(ctx, "max_amount", max=MAX_AMOUNT, cur=currency),
            parse_mode="Markdown"
        )
        return None
    
    return amount

# ════════════════════════════════════════════════════
#              MAIN FUNCTION
# ════════════════════════════════════════════════════

def main():
    """Основная функция запуска бота.
    
    ИСПРАВЛЕНО: Улучшена обработка инициализации и ошибок.
    """
    load_data()
    
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN не установлен!")
        raise ValueError("Please set BOT_TOKEN environment variable")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ── Auto-unlock stale deals job ────────────────────
    async def unlock_stale_deals_job(context):
        """Каждые 5 минут проверяет зависшие сделки."""
        now = datetime.now()
        count = 0
        
        for did, deal in list(deals.items()):
            if deal.get("status") != "active":
                continue
            
            lock_time_str = deal.get("lock_time")
            if not lock_time_str:
                continue
            
            try:
                lock_time = datetime.strptime(lock_time_str, "%d.%m.%Y %H:%M")
                if now - lock_time > timedelta(minutes=LOCK_TIMEOUT_MINUTES):
                    deal.pop("locked_by", None)
                    deal.pop("lock_time", None)
                    deal.pop("confirming_by", None)
                    count += 1
            except ValueError as e:
                logger.warning(f"⚠️ Ошибка парсинга времени блокировки: {e}")
        
        if count > 0:
            save_data()
            logger.info(f"🔓 Авто-разблокировано {count} сделок")
    
    # Регистрация периодической задачи
    if app.job_queue:
        app.job_queue.run_repeating(unlock_stale_deals_job, interval=300, first=60)
        logger.info("✅ Job queue для разблокировки включен")
    else:
        logger.warning("⚠️ job_queue недоступен. Установите: pip install 'python-telegram-bot[job-queue]'")
    
    # ── Handlers ────────────────────────────────────────
    all_cb = [CallbackQueryHandler(main_cb)]
    all_msg = [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: MENU_ST)]
    
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            LANG_ST: all_cb,
            MENU_ST: all_cb + all_msg,
            REQ_CUR_ST: all_cb,
            REQ_IN_ST: all_msg + all_cb,
            DEAL_CUR_ST: all_cb,
            DEAL_AMT_ST: all_msg + all_cb,
            DEAL_GIFT_ST: all_msg + all_cb,
            BUYER_ST: all_cb + all_msg,
            SUPPORT_ST: all_msg + all_cb,
            ADMIN_ST: all_msg + all_cb,
            REVIEW_ST: all_cb,
            DEPOSIT_ST: all_msg + all_cb,
            WITHDRAW_ST: all_msg + all_cb,
        },
        fallbacks=[
            CommandHandler("start", start),
        ],
        per_message=False,
        allow_reentry=True,
    )
    
    app.add_handler(conv)
    
    async def post_init(application):
        """Инициализация после запуска."""
        try:
            await application.bot.set_my_commands([])
            logger.info("✅ Bot commands cleared")
        except TelegramError as e:
            logger.error(f"⚠️ Ошибка при инициализации: {e}")
    
    app.post_init = post_init
    
    logger.info("✅ OTC Market Bot v4.2 Improved запущен!")
    logger.info("🤖 Бот запущен и ждёт сообщения...")
    
    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
