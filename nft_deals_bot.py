import logging
import uuid
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SUPPORT_USERNAME = "otcmarketHelper"

# ── States ──────────────────────────────────────────
LANG_ST    = 1
MENU_ST    = 2
REQ_CUR_ST = 3
REQ_IN_ST  = 4
DEAL_CUR_ST= 5
DEAL_AMT_ST= 6
DEAL_GIFT_ST=7
BUYER_ST   = 8
SUPPORT_ST = 9
ADMIN_ST   = 10
REVIEW_ST  = 11

# ── Storage ─────────────────────────────────────────
users         = {}
deals         = {}
blocked_users = set()

LANGS = {
    "uk": "🇺🇦 Українська",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "ar": "🇸🇦 العربية",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
}

CURRENCIES = {
    "UAH":   "🇺🇦 UAH",
    "RUB":   "🇷🇺 RUB",
    "KZT":   "🇰🇿 KZT",
    "CNY":   "🇨🇳 CNY",
    "USDT":  "💵 USDT",
    "STARS": "⭐ Stars",
}

MIN_AMOUNTS = {"UAH": 10, "RUB": 50, "KZT": 500, "CNY": 5, "USDT": 1, "STARS": 10}

# ════════════════════════════════════════════════════
#                   TRANSLATIONS
# ════════════════════════════════════════════════════
T = {}

T["ru"] = {
    "welcome": (
        "💎 *OTC NFT Market*\n\n"
        "Добро пожаловать на *самую безопасную* площадку\n"
        "для торговли NFT‑подарками в Telegram!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 *Эскроу‑защита* — ваши деньги под охраной\n"
        "   до момента передачи NFT подарка\n\n"
        "⚡️ *Мгновенные уведомления* о каждом\n"
        "   шаге сделки в реальном времени\n\n"
        "🛡️ *Верификация* каждого продавца и\n"
        "   покупателя перед сделкой\n\n"
        "🌍 *6 валют* — UAH, RUB, KZT, CNY,\n"
        "   USDT, Telegram Stars\n\n"
        "💬 *Поддержка 24/7* — менеджеры\n"
        "   всегда на связи\n\n"
        "⭐ *Рейтинговая система* — видите\n"
        "   историю и репутацию каждого\n\n"
        "⚖️ *Арбитраж споров* — решаем\n"
        "   конфликты в течение 30 минут\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 Выберите язык интерфейса:"
    ),
    "blocked": "⛔ *Аккаунт заблокирован*\n\nОбратитесь в поддержку: @{support}",
    "menu": (
        "🏠 *OTC NFT Market*\n\n"
        "👤 *{name}*\n"
        "⭐ Рейтинг: *{rating}* / 5.0  |  📊 Сделок: *{dc}*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Выберите действие:"
    ),
    "btn_create":  "➕ Создать сделку",
    "btn_deals":   "📂 Мои сделки",
    "btn_refs":    "👥 Рефералы",
    "btn_req":     "💳 Реквизиты",
    "btn_lang":    "🌐 Язык",
    "btn_support": "💬 Поддержка",
    "btn_about":   "ℹ️ О маркете",
    "btn_stats":   "📊 Статистика",
    "no_req": (
        "⚠️ *Реквизиты не привязаны*\n\n"
        "Чтобы создать сделку, сначала укажите\n"
        "куда покупатель будет переводить деньги.\n\n"
        "👇 Перейдите в раздел *Реквизиты*"
    ),
    "req_menu":  "💳 *Реквизиты*\n\nВыберите валюту для привязки.\n✅ — уже привязано:",
    "req_enter": (
        "✏️ *Привязка реквизитов — {cur}*\n\n"
        "Введите ваши платёжные данные:\n\n"
        "• Карты: номер карты\n"
        "• USDT: адрес TRC20 / ERC20\n"
        "• Stars: ваш username в Telegram\n\n"
        "_(Эти данные увидит покупатель при оплате)_"
    ),
    "req_saved": "✅ *Реквизиты сохранены!*\n\nВалюта: *{cur}*\n\nТеперь можно создавать сделки.",
    "deal_cur":    "💱 *Создание сделки — Шаг 1 / 3*\n\nВыберите валюту расчёта:",
    "deal_amount": "💰 *Создание сделки — Шаг 2 / 3*\n\nВведите сумму в *{cur}*:\n\n_(Именно столько заплатит покупатель)_",
    "deal_gift":   "🎁 *Создание сделки — Шаг 3 / 3*\n\nВведите название NFT подарка:\n\n_(Например: «Плюшевый мишка», «Торт», «Сердце»)_",
    "bad_amount":  "❌ Неверный формат. Введите число, например: `1500` или `25.5`",
    "min_amount":  "❌ Минимальная сумма: *{min} {cur}*\n\nВведите большую сумму:",
    "deal_created": (
        "✅ *Сделка успешно создана!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 NFT подарок: *{gift}*\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "💸 Комиссия маркета: *3%*\n"
        "🆔 ID сделки: `{id}`\n"
        "📅 Создана: {date}\n"
        "📌 Статус: 🟡 Ожидает покупателя\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔗 *Ссылка для покупателя:*\n"
        "`https://t.me/{bot}?start=deal_{id}`\n\n"
        "📤 Отправьте эту ссылку покупателю.\n"
        "Как только он оплатит — вы получите уведомление."
    ),
    "no_deals":   "📭 *Нет активных сделок*\n\nСоздайте первую сделку!",
    "deals_list": "📂 *Ваши сделки:*\n\n{list}",
    "deal_row":   "{icon} `{id}` — 🎁 *{gift}* | 💰 {amount} {cur}\n",
    "deal_cancel_confirm": (
        "🗑 *Отменить сделку?*\n\n"
        "🆔 `{id}`\n"
        "🎁 {gift}  |  💰 {amount} {cur}\n\n"
        "⚠️ Отменить можно только если\n"
        "покупатель ещё не оплатил."
    ),
    "deal_cancelled":   "✅ Сделка `{id}` отменена.",
    "deal_cancel_fail": "❌ Нельзя отменить — покупатель уже оплатил.\nОбратитесь в поддержку: @{support}",
    "refs": (
        "👥 *Реферальная программа*\n\n"
        "Приглашайте друзей и зарабатывайте *0.5 USDT*\n"
        "за каждого активного реферала!\n\n"
        "🔗 *Ваша реферальная ссылка:*\n"
        "`https://t.me/{bot}?start=ref_{uid}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 Приглашено: *{count}* чел.\n"
        "💎 Заработано: *{bonus}* USDT\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    ),
    "support": (
        "💬 *Служба поддержки OTC NFT Market*\n\n"
        "Мы работаем *24/7* и готовы помочь\n"
        "с любым вопросом!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📩 Менеджер: @{support}\n"
        "⏱ Время ответа: до 15 минут\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Или напишите сообщение прямо здесь:"
    ),
    "support_sent": "✅ *Сообщение отправлено!*\n\nМенеджер @{support} ответит в течение 15 минут. 🙏",
    "about": (
        "ℹ️ *OTC NFT Market — Официальная площадка*\n\n"
        "Мы создали самый надёжный способ покупать\n"
        "и продавать NFT‑подарки в Telegram.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 *Безопасность сделок:*\n\n"
        "• *Эскроу‑защита* — деньги покупателя\n"
        "  блокируются до момента передачи NFT.\n"
        "  Продавец не получит средства раньше\n"
        "  времени, покупатель не потеряет деньги.\n\n"
        "• *Верификация* — перед первой сделкой\n"
        "  каждый пользователь проходит проверку.\n\n"
        "• *Рейтинговая система* — смотрите\n"
        "  историю и оценки любого участника.\n\n"
        "• *Арбитраж* — спорные ситуации\n"
        "  решаются модераторами за 30 минут.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 *Как проходит сделка:*\n\n"
        "1️⃣ Продавец создаёт сделку\n"
        "2️⃣ Делится ссылкой с покупателем\n"
        "3️⃣ Покупатель оплачивает и подтверждает\n"
        "4️⃣ Продавец передаёт NFT подарок\n"
        "5️⃣ Покупатель подтверждает получение\n"
        "6️⃣ Сделка завершена ✅\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💬 Поддержка: @{support}\n"
        "📊 Версия: 3.0"
    ),
    "lang_pick": "🌐 *Выберите язык интерфейса:*",
    "back":      "⬅️ Назад",
    "s_active":    "🟡 Ожидает",
    "s_paid":      "🟠 Оплачено",
    "s_nft_sent":  "📦 NFT отправлен",
    "s_done":      "✅ Завершена",
    "s_cancelled": "❌ Отменена",
    "buyer_welcome": (
        "👋 *Добро пожаловать в OTC NFT Market!*\n\n"
        "Вас пригласили к участию в защищённой сделке.\n\n"
        "🔐 Все транзакции проходят через систему\n"
        "эскроу‑защиты — ваши средства в безопасности.\n\n"
        "👇 Выберите язык:"
    ),
    "buyer_viewing": (
        "👁 *Покупатель просматривает вашу сделку*\n\n"
        "🆔 `{id}`\n"
        "🎁 {gift}  |  💰 {amount} {cur}\n\n"
        "⏳ Ожидайте оплаты..."
    ),
    "buyer_deal": (
        "🤝 *Предложение о сделке*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 NFT подарок: *{gift}*\n"
        "💰 Сумма к оплате: *{amount} {cur}*\n"
        "👤 Продавец: *{seller}*\n"
        "⭐ Рейтинг продавца: *{rating}* / 5.0\n"
        "📊 Завершённых сделок: *{dc}*\n"
        "🆔 ID сделки: `{id}`\n"
        "📌 Статус: 🟡 Ожидает оплаты\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔐 *Гарантия безопасности:*\n"
        "После вашей оплаты продавец обязан передать\n"
        "NFT подарок. Вы подтверждаете получение.\n"
        "При проблемах — откройте спор: @{support}"
    ),
    "btn_pay":         "💳 Перейти к оплате",
    "btn_cancel_deal": "❌ Отменить",
    "btn_dispute":     "⚖️ Открыть спор",
    "buyer_pay_info": (
        "💳 *Реквизиты для оплаты*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 Подарок: *{gift}*\n"
        "💰 Сумма к переводу: *{amount} {cur}*\n"
        "📋 Реквизиты продавца:\n"
        "`{req}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ *Важно:*\n"
        "• Переведите *точную* сумму — {amount} {cur}\n"
        "• Сохраните скриншот / чек перевода\n"
        "• После перевода нажмите кнопку ниже\n\n"
        "👇 Нажмите после оплаты:"
    ),
    "btn_confirm_pay": "✅ Я оплатил — Подтвердить",
    "buyer_paid": (
        "⏳ *Оплата подтверждена!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "📌 Статус: 🟠 Ожидание передачи NFT\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Продавец уведомлён и должен передать\n"
        "вам NFT подарок в ближайшее время.\n\n"
        "🔔 Как только продавец отправит NFT —\n"
        "вы получите уведомление для подтверждения.\n\n"
        "⚠️ Если продавец не отвечает более 30 минут —\n"
        "откройте спор: @{support}"
    ),
    "seller_notif": (
        "🔔 *ПОКУПАТЕЛЬ ОПЛАТИЛ ВАШУ СДЕЛКУ!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 Подарок: *{gift}*\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "👤 Покупатель: *{buyer}*\n"
        "🆔 ID: `{id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Покупатель подтвердил оплату.\n\n"
        "👉 *Передайте NFT подарок покупателю*\n"
        "и нажмите кнопку ниже:"
    ),
    "btn_nft_sent": "📦 Я передал NFT подарок",
    "seller_waiting_confirm": (
        "⏳ *Ожидание подтверждения покупателя*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 Подарок: *{gift}*\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "📌 Статус: 📦 NFT передан, ожидаем подтверждения\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Покупатель получил уведомление и должен\n"
        "подтвердить получение NFT подарка.\n\n"
        "⚠️ Если покупатель не отвечает — @{support}"
    ),
    "buyer_nft_received_prompt": (
        "📦 *Продавец передал NFT подарок!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 Подарок: *{gift}*\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Проверьте, что NFT подарок был передан вам.\n\n"
        "✅ Если всё в порядке — подтвердите получение.\n"
        "⚖️ Если подарок не получен — откройте спор."
    ),
    "btn_confirm_receipt": "✅ Подтверждаю — получил NFT",
    "deal_done_seller": (
        "🎉 *Сделка успешно завершена!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Покупатель подтвердил получение NFT\n"
        "💰 Средства разблокированы\n"
        "📊 Счётчик сделок обновлён\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Спасибо за использование OTC NFT Market! 💎"
    ),
    "deal_done_buyer": (
        "🎉 *Сделка завершена!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Вы подтвердили получение NFT подарка\n"
        "🔐 Эскроу‑защита снята\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Пожалуйста, оцените продавца:"
    ),
    "review_prompt": "⭐ *Оцените продавца*\n\nВыберите оценку от 1 до 5:",
    "review_thanks":  "✅ Спасибо за отзыв!\n\nВаша оценка учтена. Это помогает другим участникам.",
    "dispute_opened": (
        "⚖️ *Спор открыт*\n\n"
        "Ваш запрос передан модераторам.\n\n"
        "🆔 ID сделки: `{id}`\n\n"
        "Специалист @{support} свяжется с вами\n"
        "в течение 30 минут."
    ),
    "dispute_notif": (
        "⚖️ *ОТКРЫТ СПОР ПО СДЕЛКЕ!*\n\n"
        "🆔 ID: `{id}`\n"
        "👤 Покупатель: {buyer}\n"
        "💰 {amount} {cur}\n\n"
        "Обратитесь к покупателю или @{support}"
    ),
    "deal_not_found": (
        "❌ *Сделка не найдена*\n\n"
        "Возможные причины:\n"
        "• Сделка уже завершена или отменена\n"
        "• Неверная ссылка\n\n"
        "По вопросам: @{support}"
    ),
    "buyer_left": (
        "👤 *Покупатель покинул сделку*\n\n"
        "🆔 `{id}`\n"
        "🎁 {gift}  |  💰 {amount} {cur}\n\n"
        "Сделка снова доступна для покупателей."
    ),
    "seller_reminder": (
        "⏰ *Напоминание!*\n\n"
        "Покупатель оплатил сделку `{id}`,\n"
        "но вы ещё не передали NFT.\n\n"
        "🎁 {gift}  |  💰 {amount} {cur}\n\n"
        "Пожалуйста, передайте подарок или\n"
        "обратитесь в поддержку: @{support}"
    ),
    "deal_detail": (
        "📋 *Детали сделки*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🆔 ID: `{id}`\n"
        "🎁 Подарок: *{gift}*\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "📌 Статус: {status_icon} {status}\n"
        "📅 Создана: {date}\n"
        "{buyer_line}"
        "━━━━━━━━━━━━━━━━━━━━━━"
    ),
    "btn_deal_detail": "🔎 Детали",
    "seller_stats": (
        "📊 *Статистика продавца*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 Всего сделок: *{total}*\n"
        "✅ Завершено: *{done}*\n"
        "🟡 Активных: *{active}*\n"
        "❌ Отменено: *{cancelled}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 *Оборот по валютам:*\n"
        "{turnover}"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💵 Средний чек: *{avg_deal}*\n"
        "⭐ Рейтинг: *{rating}* / 5.0\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    ),
    "search_deal_prompt": "🔍 *Поиск сделки*\n\nВведите ID сделки (или первые символы):",
    "search_deal_found":  "🔍 *Результаты поиска:*\n\n{result}",
    "search_deal_none":   "❌ Сделка с таким ID не найдена.",
    "btn_search":         "🔍 Найти сделку",
    "fee_choice": (
        "💸 *Кто покрывает комиссию маркета (3%)?*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 Базовая сумма: *{amount} {cur}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "• *Покупатель платит комиссию*\n"
        "  Вы получите: *{amount} {cur}*\n"
        "  Покупатель заплатит: *{amount_with_fee} {cur}*\n\n"
        "• *Вы покрываете комиссию*\n"
        "  Покупатель заплатит: *{amount} {cur}*\n"
        "  Вы получите: *{amount_after_fee} {cur}*\n\n"
        "Выберите:"
    ),
    "btn_fee_buyer":  "👤 Покупатель платит комиссию",
    "btn_fee_seller": "🏪 Я покрываю комиссию",
    "admin_granted":  "🔐 *Права администратора активированы*\n\nИспользуйте кнопки ниже:",
}

# ── Ukrainian ────────────────────────────────────────
T["uk"] = {
    "welcome": "💎 *OTC NFT Market*\n\nЛаскаво просимо!\n\n━━━━━━━━━━━━━━━━━━━━━━\n🔐 Ескроу‑захист кожної угоди\n⚡️ Миттєві сповіщення\n🛡️ Верифікація учасників\n🌍 6 валют\n💬 Підтримка 24/7\n⚖️ Арбітраж спорів\n━━━━━━━━━━━━━━━━━━━━━━\n\n👇 Оберіть мову:",
    "blocked": "⛔ *Акаунт заблоковано*\n\nЗверніться до підтримки: @{support}",
    "menu": "🏠 *OTC NFT Market*\n\n👤 *{name}*\n⭐ Рейтинг: *{rating}* / 5.0  |  📊 Угод: *{dc}*\n\n━━━━━━━━━━━━━━━━━━━━━━\nОберіть дію:",
    "btn_create": "➕ Створити угоду", "btn_deals": "📂 Мої угоди", "btn_refs": "👥 Реферали",
    "btn_req": "💳 Реквізити", "btn_lang": "🌐 Мова", "btn_support": "💬 Підтримка",
    "btn_about": "ℹ️ Про маркет", "btn_stats": "📊 Статистика",
    "no_req": "⚠️ *Реквізити не прив'язані*\n\nДодайте реквізити перед створенням угоди.\n\n👇 Розділ *Реквізити*",
    "req_menu": "💳 *Реквізити*\n\nОберіть валюту.\n✅ — вже прив'язано:",
    "req_enter": "✏️ *Реквізити — {cur}*\n\nВведіть платіжні дані:\n• Картка: номер\n• USDT: адреса TRC20/ERC20\n• Stars: username",
    "req_saved": "✅ *Реквізити збережено!*\n\nВалюта: *{cur}*",
    "deal_cur": "💱 *Створення угоди — Крок 1/3*\n\nОберіть валюту:",
    "deal_amount": "💰 *Крок 2/3*\n\nСума в *{cur}*:",
    "deal_gift": "🎁 *Крок 3/3*\n\nНазва NFT подарунка:",
    "bad_amount": "❌ Невірний формат. Введіть число.",
    "min_amount": "❌ Мінімальна сума: *{min} {cur}*",
    "deal_created": "✅ *Угоду створено!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 *{gift}*\n💰 {amount} {cur}\n💸 Комісія: 3%\n🆔 `{id}`\n📅 {date}\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔗 Посилання:\n`https://t.me/{bot}?start=deal_{id}`",
    "no_deals": "📭 Немає угод.\n\nСтворіть першу!", "deals_list": "📂 *Ваші угоди:*\n\n{list}",
    "deal_row": "{icon} `{id}` — 🎁 *{gift}* | 💰 {amount} {cur}\n",
    "deal_cancel_confirm": "🗑 *Скасувати угоду?*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}",
    "deal_cancelled": "✅ Угоду `{id}` скасовано.",
    "deal_cancel_fail": "❌ Не можна скасувати — покупець вже оплатив.\n@{support}",
    "refs": "👥 *Реферали*\n\n🔗 `https://t.me/{bot}?start=ref_{uid}`\n\n👤 Запрошено: *{count}*\n💎 Зароблено: *{bonus}* USDT",
    "support": "💬 *Підтримка OTC NFT Market*\n\n📩 @{support}\n⏱ До 15 хвилин\n\nАбо напишіть тут:",
    "support_sent": "✅ Надіслано! @{support} відповість протягом 15 хвилин. 🙏",
    "about": "ℹ️ *OTC NFT Market*\n\nНайнадійніший майданчик для торгівлі NFT подарунками.\n\n🔐 Ескроу‑захист\n🛡️ Верифікація\n⭐ Рейтинги\n⚖️ Арбітраж\n\n💬 @{support}",
    "lang_pick": "🌐 *Оберіть мову:*", "back": "⬅️ Назад",
    "s_active": "🟡 Очікує", "s_paid": "🟠 Оплачено", "s_nft_sent": "📦 NFT відправлено",
    "s_done": "✅ Завершено", "s_cancelled": "❌ Скасовано",
    "buyer_welcome": "👋 *Ласкаво просимо!*\n\nВас запросили до захищеної угоди.\n\n🔐 Ескроу‑захист.\n\n👇 Оберіть мову:",
    "buyer_viewing": "👁 *Покупець переглядає угоду*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\n⏳ Очікуйте...",
    "buyer_deal": "🤝 *Пропозиція угоди*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 *{gift}*\n💰 {amount} {cur}\n👤 Продавець: *{seller}*\n⭐ Рейтинг: *{rating}*\n📊 Угод: *{dc}*\n🆔 `{id}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔐 Кошти захищені ескроу до передачі NFT.",
    "btn_pay": "💳 До оплати", "btn_cancel_deal": "❌ Скасувати", "btn_dispute": "⚖️ Відкрити спір",
    "buyer_pay_info": "💳 *Реквізити для оплати*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n📋 Реквізити:\n`{req}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ Переведіть *точну* суму.\n\n👇 Після оплати:",
    "btn_confirm_pay": "✅ Я оплатив — Підтвердити",
    "buyer_paid": "⏳ *Оплату підтверджено!*\n\n💰 {amount} {cur}\n📌 Очікування передачі NFT\n\n✅ Продавець сповіщений.\n\n⚠️ Якщо не відповідає — @{support}",
    "seller_notif": "🔔 *ПОКУПЕЦЬ ОПЛАТИВ!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n👤 {buyer}\n🆔 `{id}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n👉 Передайте NFT та натисніть кнопку:",
    "btn_nft_sent": "📦 Я передав NFT подарунок",
    "seller_waiting_confirm": "⏳ *Очікування підтвердження*\n\n🎁 {gift} | 💰 {amount} {cur}\n📌 NFT передано, очікуємо підтвердження покупця.\n\n⚠️ Якщо не відповідає — @{support}",
    "buyer_nft_received_prompt": "📦 *Продавець передав NFT!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n━━━━━━━━━━━━━━━━━━━━━━\n\nПеревірте отримання NFT.\n\n✅ Якщо все гаразд — підтвердіть.\n⚖️ Якщо не отримано — відкрийте спір.",
    "btn_confirm_receipt": "✅ Підтверджую — отримав NFT",
    "deal_done_seller": "🎉 *Угода завершена!*\n\n✅ Покупець підтвердив отримання NFT\n💰 Кошти розблоковано\n\nДякуємо! 💎",
    "deal_done_buyer": "🎉 *Угода завершена!*\n\n✅ Ви підтвердили отримання NFT\n🔐 Ескроу знято\n\nОцініть продавця:",
    "review_prompt": "⭐ *Оцініть продавця:*", "review_thanks": "✅ Дякуємо за відгук!",
    "dispute_opened": "⚖️ *Спір відкрито*\n\n🆔 `{id}`\n\nСпеціаліст @{support} зв'яжеться протягом 30 хвилин.",
    "dispute_notif": "⚖️ *ВІДКРИТО СПІР!*\n\n🆔 `{id}`\n👤 {buyer}\n💰 {amount} {cur}\n\n@{support}",
    "deal_not_found": "❌ *Угоду не знайдено*\n\n@{support}",
    "buyer_left": "👤 *Покупець покинув угоду*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\nУгода знову доступна.",
    "seller_reminder": "⏰ *Нагадування!*\n\nПокупець оплатив `{id}`, але ви ще не передали NFT.\n🎁 {gift} | 💰 {amount} {cur}\n\n@{support}",
    "deal_detail": "📋 *Деталі угоди*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🆔 `{id}`\n🎁 {gift}\n💰 {amount} {cur}\n📌 {status_icon} {status}\n📅 {date}\n{buyer_line}━━━━━━━━━━━━━━━━━━━━━━",
    "btn_deal_detail": "🔎 Деталі",
    "seller_stats": "📊 *Статистика*\n\n📋 Всього: *{total}*\n✅ Завершено: *{done}*\n🟡 Активних: *{active}*\n❌ Скасовано: *{cancelled}*\n\n💰 Оборот:\n{turnover}\n💵 Середній чек: *{avg_deal}*\n⭐ Рейтинг: *{rating}*",
    "search_deal_prompt": "🔍 Введіть ID угоди:", "search_deal_found": "🔍 *Результати:*\n\n{result}",
    "search_deal_none": "❌ Угоду не знайдено.", "btn_search": "🔍 Знайти угоду",
    "fee_choice": "💸 *Хто покриває комісію (3%)?*\n\n💰 Сума: *{amount} {cur}*\n\n• Покупець платить {amount_with_fee} {cur}\n• Ви отримуєте {amount_after_fee} {cur} (покупець платить {amount})\n\nОберіть:",
    "btn_fee_buyer": "👤 Покупець платить комісію", "btn_fee_seller": "🏪 Я покриваю комісію",
    "admin_granted": "🔐 *Права адміністратора активовано*",
}

# ── English ──────────────────────────────────────────
T["en"] = {
    "welcome": "💎 *OTC NFT Market*\n\nWelcome to the safest NFT gift trading platform!\n\n━━━━━━━━━━━━━━━━━━━━━━\n🔐 Escrow protection for every deal\n⚡️ Real‑time notifications\n🛡️ User verification\n🌍 6 currencies\n💬 24/7 support\n⚖️ Dispute arbitration\n━━━━━━━━━━━━━━━━━━━━━━\n\n👇 Choose your language:",
    "blocked": "⛔ *Account blocked*\n\nContact support: @{support}",
    "menu": "🏠 *OTC NFT Market*\n\n👤 *{name}*\n⭐ Rating: *{rating}* / 5.0  |  📊 Deals: *{dc}*\n\n━━━━━━━━━━━━━━━━━━━━━━\nChoose an action:",
    "btn_create": "➕ Create Deal", "btn_deals": "📂 My Deals", "btn_refs": "👥 Referrals",
    "btn_req": "💳 Requisites", "btn_lang": "🌐 Language", "btn_support": "💬 Support",
    "btn_about": "ℹ️ About", "btn_stats": "📊 Statistics",
    "no_req": "⚠️ *Requisites not linked*\n\nAdd payment details before creating a deal.\n\n👇 Go to *Requisites*",
    "req_menu": "💳 *Requisites*\n\nChoose currency.\n✅ — already linked:",
    "req_enter": "✏️ *Requisites — {cur}*\n\nEnter payment details:\n• Cards: card number\n• USDT: TRC20/ERC20 address\n• Stars: Telegram username",
    "req_saved": "✅ *Requisites saved!*\n\nCurrency: *{cur}*",
    "deal_cur": "💱 *Create Deal — Step 1/3*\n\nChoose currency:",
    "deal_amount": "💰 *Step 2/3*\n\nAmount in *{cur}*:",
    "deal_gift": "🎁 *Step 3/3*\n\nNFT gift name:",
    "bad_amount": "❌ Invalid format. Enter a number.",
    "min_amount": "❌ Minimum amount: *{min} {cur}*",
    "deal_created": "✅ *Deal created!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 *{gift}*\n💰 {amount} {cur}\n💸 Fee: 3%\n🆔 `{id}`\n📅 {date}\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔗 Buyer link:\n`https://t.me/{bot}?start=deal_{id}`",
    "no_deals": "📭 No deals yet.", "deals_list": "📂 *Your Deals:*\n\n{list}",
    "deal_row": "{icon} `{id}` — 🎁 *{gift}* | 💰 {amount} {cur}\n",
    "deal_cancel_confirm": "🗑 *Cancel deal?*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}",
    "deal_cancelled": "✅ Deal `{id}` cancelled.",
    "deal_cancel_fail": "❌ Cannot cancel — buyer already paid.\n@{support}",
    "refs": "👥 *Referrals*\n\n🔗 `https://t.me/{bot}?start=ref_{uid}`\n\n👤 Invited: *{count}*\n💎 Earned: *{bonus}* USDT",
    "support": "💬 *OTC NFT Market Support*\n\n📩 @{support}\n⏱ Up to 15 minutes\n\nOr message here:",
    "support_sent": "✅ Sent! @{support} will reply within 15 minutes. 🙏",
    "about": "ℹ️ *OTC NFT Market*\n\nThe safest NFT gift trading platform.\n\n🔐 Escrow\n🛡️ Verification\n⭐ Ratings\n⚖️ Arbitration\n\n💬 @{support}",
    "lang_pick": "🌐 *Choose language:*", "back": "⬅️ Back",
    "s_active": "🟡 Pending", "s_paid": "🟠 Paid", "s_nft_sent": "📦 NFT Sent",
    "s_done": "✅ Done", "s_cancelled": "❌ Cancelled",
    "buyer_welcome": "👋 *Welcome to OTC NFT Market!*\n\nYou've been invited to a secured deal.\n\n🔐 Escrow protection.\n\n👇 Choose language:",
    "buyer_viewing": "👁 *Buyer is viewing your deal*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\n⏳ Awaiting payment...",
    "buyer_deal": "🤝 *Deal Offer*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 *{gift}*\n💰 {amount} {cur}\n👤 Seller: *{seller}*\n⭐ Rating: *{rating}*\n📊 Deals: *{dc}*\n🆔 `{id}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔐 Funds held in escrow until NFT transferred.",
    "btn_pay": "💳 Proceed to Payment", "btn_cancel_deal": "❌ Cancel", "btn_dispute": "⚖️ Open Dispute",
    "buyer_pay_info": "💳 *Payment Details*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n📋 Requisites:\n`{req}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ Transfer *exact* amount.\n\n👇 After payment:",
    "btn_confirm_pay": "✅ I've paid — Confirm",
    "buyer_paid": "⏳ *Payment confirmed!*\n\n💰 {amount} {cur}\n📌 Waiting for NFT transfer\n\n✅ Seller notified.\n\n⚠️ No response? — @{support}",
    "seller_notif": "🔔 *BUYER HAS PAID!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n👤 {buyer}\n🆔 `{id}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n👉 Transfer the NFT and click:",
    "btn_nft_sent": "📦 I transferred the NFT gift",
    "seller_waiting_confirm": "⏳ *Waiting for buyer confirmation*\n\n🎁 {gift} | 💰 {amount} {cur}\n📌 NFT sent, awaiting buyer confirmation.\n\n⚠️ Issues? — @{support}",
    "buyer_nft_received_prompt": "📦 *Seller transferred the NFT!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n━━━━━━━━━━━━━━━━━━━━━━\n\nCheck your NFT gift.\n\n✅ Confirm if received.\n⚖️ Open dispute if not.",
    "btn_confirm_receipt": "✅ Confirm — I received the NFT",
    "deal_done_seller": "🎉 *Deal completed!*\n\n✅ Buyer confirmed NFT receipt\n💰 Funds unlocked\n\nThank you! 💎",
    "deal_done_buyer": "🎉 *Deal completed!*\n\n✅ NFT receipt confirmed\n🔐 Escrow released\n\nPlease rate the seller:",
    "review_prompt": "⭐ *Rate the seller:*", "review_thanks": "✅ Thank you for your review!",
    "dispute_opened": "⚖️ *Dispute opened*\n\n🆔 `{id}`\n\n@{support} will contact you within 30 minutes.",
    "dispute_notif": "⚖️ *DISPUTE OPENED!*\n\n🆔 `{id}`\n👤 {buyer}\n💰 {amount} {cur}\n\n@{support}",
    "deal_not_found": "❌ *Deal not found*\n\n@{support}",
    "buyer_left": "👤 *Buyer left the deal*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\nDeal is available again.",
    "seller_reminder": "⏰ *Reminder!*\n\nBuyer paid `{id}` but you haven't sent the NFT.\n🎁 {gift} | 💰 {amount} {cur}\n\n@{support}",
    "deal_detail": "📋 *Deal Details*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🆔 `{id}`\n🎁 {gift}\n💰 {amount} {cur}\n📌 {status_icon} {status}\n📅 {date}\n{buyer_line}━━━━━━━━━━━━━━━━━━━━━━",
    "btn_deal_detail": "🔎 Details",
    "seller_stats": "📊 *Statistics*\n\n📋 Total: *{total}*\n✅ Done: *{done}*\n🟡 Active: *{active}*\n❌ Cancelled: *{cancelled}*\n\n💰 Turnover:\n{turnover}\n💵 Avg deal: *{avg_deal}*\n⭐ Rating: *{rating}*",
    "search_deal_prompt": "🔍 Enter deal ID:", "search_deal_found": "🔍 *Results:*\n\n{result}",
    "search_deal_none": "❌ Deal not found.", "btn_search": "🔍 Find Deal",
    "fee_choice": "💸 *Who covers the fee (3%)?*\n\n💰 Amount: *{amount} {cur}*\n\n• Buyer pays {amount_with_fee} {cur}\n• You get {amount_after_fee} {cur} (buyer pays {amount})\n\nChoose:",
    "btn_fee_buyer": "👤 Buyer pays the fee", "btn_fee_seller": "🏪 I cover the fee",
    "admin_granted": "🔐 *Admin rights activated*",
}

# ── Arabic ──────────────────────────────────────────
T["ar"] = {
    "welcome": "💎 *OTC NFT Market*\n\nمرحباً بك في أكثر منصة آمانًا لتداول هدايا NFT!\n\n━━━━━━━━━━━━━━━━━━━━━━\n🔐 حماية الضمان لكل صفقة\n⚡️ إشعارات فورية\n🛡️ التحقق من المستخدمين\n🌍 6 عملات\n💬 دعم 24/7\n⚖️ حل النزاعات\n━━━━━━━━━━━━━━━━━━━━━━\n\n👇 اختر لغتك:",
    "blocked": "⛔ *تم حظر حسابك*\n\nتواصل مع الدعم: @{support}",
    "menu": "🏠 *OTC NFT Market*\n\n👤 *{name}*\n⭐ التقييم: *{rating}* / 5.0  |  📊 الصفقات: *{dc}*\n\n━━━━━━━━━━━━━━━━━━━━━━\nاختر إجراءً:",
    "btn_create": "➕ إنشاء صفقة", "btn_deals": "📂 صفقاتي", "btn_refs": "👥 الإحالات",
    "btn_req": "💳 بيانات الدفع", "btn_lang": "🌐 اللغة", "btn_support": "💬 الدعم",
    "btn_about": "ℹ️ عن المنصة", "btn_stats": "📊 الإحصاء",
    "no_req": "⚠️ *لم يتم ربط بيانات الدفع*\n\nأضف بيانات الدفع قبل إنشاء صفقة.\n\n👇 انتقل إلى *بيانات الدفع*",
    "req_menu": "💳 *بيانات الدفع*\n\nاختر العملة.\n✅ — تم الربط:",
    "req_enter": "✏️ *بيانات الدفع — {cur}*\n\nأدخل بيانات الدفع:\n• البطاقات: رقم البطاقة\n• USDT: عنوان TRC20/ERC20\n• Stars: اسم المستخدم",
    "req_saved": "✅ *تم حفظ البيانات!*\n\nالعملة: *{cur}*",
    "deal_cur": "💱 *إنشاء صفقة — الخطوة 1/3*\n\nاختر العملة:",
    "deal_amount": "💰 *الخطوة 2/3*\n\nالمبلغ بـ *{cur}*:",
    "deal_gift": "🎁 *الخطوة 3/3*\n\nاسم هدية NFT:",
    "bad_amount": "❌ تنسيق غير صحيح. أدخل رقمًا.",
    "min_amount": "❌ الحد الأدنى: *{min} {cur}*",
    "deal_created": "✅ *تم إنشاء الصفقة!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 *{gift}*\n💰 {amount} {cur}\n💸 العمولة: 3%\n🆔 `{id}`\n📅 {date}\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔗 رابط المشتري:\n`https://t.me/{bot}?start=deal_{id}`",
    "no_deals": "📭 لا توجد صفقات.", "deals_list": "📂 *صفقاتك:*\n\n{list}",
    "deal_row": "{icon} `{id}` — 🎁 *{gift}* | 💰 {amount} {cur}\n",
    "deal_cancel_confirm": "🗑 *إلغاء الصفقة؟*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}",
    "deal_cancelled": "✅ تم إلغاء الصفقة `{id}`.",
    "deal_cancel_fail": "❌ لا يمكن الإلغاء — دفع المشتري بالفعل.\n@{support}",
    "refs": "👥 *الإحالات*\n\n🔗 `https://t.me/{bot}?start=ref_{uid}`\n\n👤 المدعوون: *{count}*\n💎 الأرباح: *{bonus}* USDT",
    "support": "💬 *دعم OTC NFT Market*\n\n📩 @{support}\n⏱ حتى 15 دقيقة\n\nأو اكتب هنا:",
    "support_sent": "✅ تم الإرسال! سيرد @{support} خلال 15 دقيقة. 🙏",
    "about": "ℹ️ *OTC NFT Market*\n\nأكثر منصة موثوقة لتداول هدايا NFT.\n\n🔐 الضمان\n🛡️ التحقق\n⭐ التقييمات\n⚖️ التحكيم\n\n💬 @{support}",
    "lang_pick": "🌐 *اختر اللغة:*", "back": "⬅️ رجوع",
    "s_active": "🟡 انتظار", "s_paid": "🟠 مدفوع", "s_nft_sent": "📦 NFT أُرسل",
    "s_done": "✅ مكتمل", "s_cancelled": "❌ ملغى",
    "buyer_welcome": "👋 *مرحباً بك في OTC NFT Market!*\n\nتمت دعوتك للمشاركة في صفقة محمية.\n\n🔐 حماية الضمان.\n\n👇 اختر اللغة:",
    "buyer_viewing": "👁 *المشتري يشاهد صفقتك*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\n⏳ انتظر الدفع...",
    "buyer_deal": "🤝 *عرض صفقة*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 *{gift}*\n💰 {amount} {cur}\n👤 البائع: *{seller}*\n⭐ التقييم: *{rating}*\n📊 الصفقات: *{dc}*\n🆔 `{id}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔐 الأموال محمية حتى نقل NFT.",
    "btn_pay": "💳 الدفع", "btn_cancel_deal": "❌ إلغاء", "btn_dispute": "⚖️ فتح نزاع",
    "buyer_pay_info": "💳 *تفاصيل الدفع*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n📋 بيانات الدفع:\n`{req}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ حوّل المبلغ الدقيق.\n\n👇 بعد الدفع:",
    "btn_confirm_pay": "✅ دفعت — تأكيد",
    "buyer_paid": "⏳ *تم تأكيد الدفع!*\n\n💰 {amount} {cur}\n📌 انتظار نقل NFT\n\n✅ تم إشعار البائع.\n\n⚠️ لا يوجد رد؟ — @{support}",
    "seller_notif": "🔔 *دفع المشتري!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n👤 {buyer}\n🆔 `{id}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n👉 انقل هدية NFT واضغط:",
    "btn_nft_sent": "📦 نقلت هدية NFT",
    "seller_waiting_confirm": "⏳ *انتظار تأكيد المشتري*\n\n🎁 {gift} | 💰 {amount} {cur}\n📌 NFT أُرسل، ننتظر التأكيد.\n\n⚠️ مشكلة؟ — @{support}",
    "buyer_nft_received_prompt": "📦 *البائع نقل NFT!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n━━━━━━━━━━━━━━━━━━━━━━\n\nتحقق من استلام هدية NFT.\n\n✅ أكّد إذا استلمت.\n⚖️ افتح نزاعاً إذا لم تستلم.",
    "btn_confirm_receipt": "✅ تأكيد — استلمت NFT",
    "deal_done_seller": "🎉 *اكتملت الصفقة!*\n\n✅ أكّد المشتري الاستلام\n💰 الأموال محررة\n\nشكراً! 💎",
    "deal_done_buyer": "🎉 *اكتملت الصفقة!*\n\n✅ تم تأكيد الاستلام\n🔐 الضمان محرر\n\nقيّم البائع:",
    "review_prompt": "⭐ *قيّم البائع:*", "review_thanks": "✅ شكراً على تقييمك!",
    "dispute_opened": "⚖️ *تم فتح النزاع*\n\n🆔 `{id}`\n\nسيتواصل معك @{support} خلال 30 دقيقة.",
    "dispute_notif": "⚖️ *نزاع مفتوح!*\n\n🆔 `{id}`\n👤 {buyer}\n💰 {amount} {cur}\n\n@{support}",
    "deal_not_found": "❌ *الصفقة غير موجودة*\n\n@{support}",
    "buyer_left": "👤 *غادر المشتري*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\nالصفقة متاحة مجدداً.",
    "seller_reminder": "⏰ *تذكير!*\n\nدفع المشتري `{id}` لكنك لم ترسل NFT.\n🎁 {gift} | 💰 {amount} {cur}\n\n@{support}",
    "deal_detail": "📋 *تفاصيل الصفقة*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🆔 `{id}`\n🎁 {gift}\n💰 {amount} {cur}\n📌 {status_icon} {status}\n📅 {date}\n{buyer_line}━━━━━━━━━━━━━━━━━━━━━━",
    "btn_deal_detail": "🔎 التفاصيل",
    "seller_stats": "📊 *الإحصاء*\n\n📋 المجموع: *{total}*\n✅ مكتمل: *{done}*\n🟡 نشط: *{active}*\n❌ ملغى: *{cancelled}*\n\n💰 حجم التداول:\n{turnover}\n💵 متوسط الصفقة: *{avg_deal}*\n⭐ التقييم: *{rating}*",
    "search_deal_prompt": "🔍 أدخل معرف الصفقة:", "search_deal_found": "🔍 *النتائج:*\n\n{result}",
    "search_deal_none": "❌ لم يتم العثور على الصفقة.", "btn_search": "🔍 بحث",
    "fee_choice": "💸 *من يدفع العمولة (3%)?*\n\n💰 المبلغ: *{amount} {cur}*\n\n• المشتري يدفع: {amount_with_fee} {cur}\n• أنت تحصل على: {amount_after_fee} {cur}\n\nاختر:",
    "btn_fee_buyer": "👤 المشتري يدفع العمولة", "btn_fee_seller": "🏪 أنا أدفع العمولة",
    "admin_granted": "🔐 *تم تفعيل صلاحيات المسؤول*",
}

# ── Chinese ──────────────────────────────────────────
T["zh"] = {
    "welcome": "💎 *OTC NFT Market*\n\n欢迎使用最安全的NFT礼品交易平台！\n\n━━━━━━━━━━━━━━━━━━━━━━\n🔐 每笔交易的托管保护\n⚡️ 实时通知\n🛡️ 用户验证\n🌍 6种货币\n💬 24/7支持\n⚖️ 争议仲裁\n━━━━━━━━━━━━━━━━━━━━━━\n\n👇 选择语言:",
    "blocked": "⛔ *账号已封禁*\n\n联系客服: @{support}",
    "menu": "🏠 *OTC NFT Market*\n\n👤 *{name}*\n⭐ 评分: *{rating}* / 5.0  |  📊 交易: *{dc}*\n\n━━━━━━━━━━━━━━━━━━━━━━\n选择操作:",
    "btn_create": "➕ 创建交易", "btn_deals": "📂 我的交易", "btn_refs": "👥 推荐",
    "btn_req": "💳 收款信息", "btn_lang": "🌐 语言", "btn_support": "💬 客服",
    "btn_about": "ℹ️ 关于", "btn_stats": "📊 统计",
    "no_req": "⚠️ *未绑定收款信息*\n\n创建交易前请添加收款信息。\n\n👇 前往 *收款信息*",
    "req_menu": "💳 *收款信息*\n\n选择货币。\n✅ — 已绑定:",
    "req_enter": "✏️ *收款信息 — {cur}*\n\n请输入收款方式:\n• 银行卡: 卡号\n• USDT: TRC20/ERC20地址\n• Stars: Telegram用户名",
    "req_saved": "✅ *已保存!*\n\n货币: *{cur}*",
    "deal_cur": "💱 *创建交易 — 第1步/共3步*\n\n选择货币:",
    "deal_amount": "💰 *第2步/共3步*\n\n*{cur}*金额:",
    "deal_gift": "🎁 *第3步/共3步*\n\nNFT礼品名称:",
    "bad_amount": "❌ 格式错误，请输入数字。",
    "min_amount": "❌ 最低金额: *{min} {cur}*",
    "deal_created": "✅ *交易创建成功!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 *{gift}*\n💰 {amount} {cur}\n💸 手续费: 3%\n🆔 `{id}`\n📅 {date}\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔗 买家链接:\n`https://t.me/{bot}?start=deal_{id}`",
    "no_deals": "📭 暂无交易。", "deals_list": "📂 *我的交易:*\n\n{list}",
    "deal_row": "{icon} `{id}` — 🎁 *{gift}* | 💰 {amount} {cur}\n",
    "deal_cancel_confirm": "🗑 *取消交易?*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}",
    "deal_cancelled": "✅ 交易 `{id}` 已取消。",
    "deal_cancel_fail": "❌ 无法取消 — 买家已付款。\n@{support}",
    "refs": "👥 *推荐计划*\n\n🔗 `https://t.me/{bot}?start=ref_{uid}`\n\n👤 已邀请: *{count}*\n💎 已获得: *{bonus}* USDT",
    "support": "💬 *OTC NFT Market 客服*\n\n📩 @{support}\n⏱ 15分钟内回复\n\n或在此留言:",
    "support_sent": "✅ 已发送! @{support} 将在15分钟内回复。🙏",
    "about": "ℹ️ *OTC NFT Market*\n\n最可靠的NFT礼品交易平台。\n\n🔐 托管保护\n🛡️ 身份验证\n⭐ 评分系统\n⚖️ 争议仲裁\n\n💬 @{support}",
    "lang_pick": "🌐 *选择语言:*", "back": "⬅️ 返回",
    "s_active": "🟡 等待中", "s_paid": "🟠 已付款", "s_nft_sent": "📦 NFT已发送",
    "s_done": "✅ 已完成", "s_cancelled": "❌ 已取消",
    "buyer_welcome": "👋 *欢迎来到OTC NFT Market!*\n\n您已被邀请参与一笔受保护的交易。\n\n🔐 托管保护。\n\n👇 选择语言:",
    "buyer_viewing": "👁 *买家正在查看您的交易*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\n⏳ 等待付款...",
    "buyer_deal": "🤝 *交易邀请*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 *{gift}*\n💰 {amount} {cur}\n👤 卖家: *{seller}*\n⭐ 评分: *{rating}*\n📊 交易数: *{dc}*\n🆔 `{id}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔐 资金托管直到NFT转让。",
    "btn_pay": "💳 去付款", "btn_cancel_deal": "❌ 取消", "btn_dispute": "⚖️ 开启争议",
    "buyer_pay_info": "💳 *付款详情*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n📋 收款信息:\n`{req}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ 请转账*精确*金额。\n\n👇 付款后:",
    "btn_confirm_pay": "✅ 我已付款 — 确认",
    "buyer_paid": "⏳ *付款已确认!*\n\n💰 {amount} {cur}\n📌 等待NFT转让\n\n✅ 卖家已收到通知。\n\n⚠️ 无回应? — @{support}",
    "seller_notif": "🔔 *买家已付款!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n👤 {buyer}\n🆔 `{id}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n👉 转让NFT礼品并点击:",
    "btn_nft_sent": "📦 我已转让NFT礼品",
    "seller_waiting_confirm": "⏳ *等待买家确认*\n\n🎁 {gift} | 💰 {amount} {cur}\n📌 NFT已发送，等待买家确认。\n\n⚠️ 有问题? — @{support}",
    "buyer_nft_received_prompt": "📦 *卖家已转让NFT!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n━━━━━━━━━━━━━━━━━━━━━━\n\n请确认收到NFT礼品。\n\n✅ 已收到请确认。\n⚖️ 未收到请开启争议。",
    "btn_confirm_receipt": "✅ 确认 — 已收到NFT",
    "deal_done_seller": "🎉 *交易完成!*\n\n✅ 买家确认收到NFT\n💰 资金已解锁\n\n感谢使用! 💎",
    "deal_done_buyer": "🎉 *交易完成!*\n\n✅ 已确认收到NFT\n🔐 托管已解除\n\n请为卖家评分:",
    "review_prompt": "⭐ *为卖家评分:*", "review_thanks": "✅ 感谢您的评价!",
    "dispute_opened": "⚖️ *争议已开启*\n\n🆔 `{id}`\n\n@{support} 将在30分钟内联系您。",
    "dispute_notif": "⚖️ *争议开启!*\n\n🆔 `{id}`\n👤 {buyer}\n💰 {amount} {cur}\n\n@{support}",
    "deal_not_found": "❌ *未找到交易*\n\n@{support}",
    "buyer_left": "👤 *买家已离开*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\n交易再次可用。",
    "seller_reminder": "⏰ *提醒!*\n\n买家已付款 `{id}` 但您还未发送NFT。\n🎁 {gift} | 💰 {amount} {cur}\n\n@{support}",
    "deal_detail": "📋 *交易详情*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🆔 `{id}`\n🎁 {gift}\n💰 {amount} {cur}\n📌 {status_icon} {status}\n📅 {date}\n{buyer_line}━━━━━━━━━━━━━━━━━━━━━━",
    "btn_deal_detail": "🔎 详情",
    "seller_stats": "📊 *统计*\n\n📋 总计: *{total}*\n✅ 完成: *{done}*\n🟡 进行中: *{active}*\n❌ 已取消: *{cancelled}*\n\n💰 成交量:\n{turnover}\n💵 平均金额: *{avg_deal}*\n⭐ 评分: *{rating}*",
    "search_deal_prompt": "🔍 输入交易ID:", "search_deal_found": "🔍 *搜索结果:*\n\n{result}",
    "search_deal_none": "❌ 未找到交易。", "btn_search": "🔍 搜索交易",
    "fee_choice": "💸 *谁支付手续费 (3%)?*\n\n💰 金额: *{amount} {cur}*\n\n• 买家支付: {amount_with_fee} {cur}\n• 您收到: {amount_after_fee} {cur}\n\n选择:",
    "btn_fee_buyer": "👤 买家支付手续费", "btn_fee_seller": "🏪 我支付手续费",
    "admin_granted": "🔐 *管理员权限已激活*",
}

# ── Japanese ─────────────────────────────────────────
T["ja"] = {
    "welcome": "💎 *OTC NFT Market*\n\n最も安全なNFTギフト取引プラットフォームへようこそ！\n\n━━━━━━━━━━━━━━━━━━━━━━\n🔐 全取引のエスクロー保護\n⚡️ リアルタイム通知\n🛡️ ユーザー認証\n🌍 6通貨対応\n💬 24時間サポート\n⚖️ 紛争仲裁\n━━━━━━━━━━━━━━━━━━━━━━\n\n👇 言語を選択:",
    "blocked": "⛔ *アカウントが停止されました*\n\nサポートへ: @{support}",
    "menu": "🏠 *OTC NFT Market*\n\n👤 *{name}*\n⭐ 評価: *{rating}* / 5.0  |  📊 取引: *{dc}*\n\n━━━━━━━━━━━━━━━━━━━━━━\n操作を選択:",
    "btn_create": "➕ 取引作成", "btn_deals": "📂 取引一覧", "btn_refs": "👥 紹介",
    "btn_req": "💳 支払情報", "btn_lang": "🌐 言語", "btn_support": "💬 サポート",
    "btn_about": "ℹ️ について", "btn_stats": "📊 統計",
    "no_req": "⚠️ *支払情報未登録*\n\n取引作成前に支払情報を追加してください。\n\n👇 *支払情報* へ",
    "req_menu": "💳 *支払情報*\n\n通貨を選択。\n✅ — 登録済み:",
    "req_enter": "✏️ *支払情報 — {cur}*\n\n支払方法を入力:\n• カード: カード番号\n• USDT: TRC20/ERC20アドレス\n• Stars: Telegramユーザー名",
    "req_saved": "✅ *保存しました!*\n\n通貨: *{cur}*",
    "deal_cur": "💱 *取引作成 — ステップ1/3*\n\n通貨を選択:",
    "deal_amount": "💰 *ステップ2/3*\n\n*{cur}*の金額:",
    "deal_gift": "🎁 *ステップ3/3*\n\nNFTギフト名:",
    "bad_amount": "❌ 無効な形式。数字を入力してください。",
    "min_amount": "❌ 最低金額: *{min} {cur}*",
    "deal_created": "✅ *取引作成完了!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 *{gift}*\n💰 {amount} {cur}\n💸 手数料: 3%\n🆔 `{id}`\n📅 {date}\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔗 購入者リンク:\n`https://t.me/{bot}?start=deal_{id}`",
    "no_deals": "📭 取引なし。", "deals_list": "📂 *取引一覧:*\n\n{list}",
    "deal_row": "{icon} `{id}` — 🎁 *{gift}* | 💰 {amount} {cur}\n",
    "deal_cancel_confirm": "🗑 *取引をキャンセル?*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}",
    "deal_cancelled": "✅ 取引 `{id}` をキャンセルしました。",
    "deal_cancel_fail": "❌ キャンセル不可 — 購入者が支払済み。\n@{support}",
    "refs": "👥 *紹介プログラム*\n\n🔗 `https://t.me/{bot}?start=ref_{uid}`\n\n👤 招待済み: *{count}*\n💎 獲得: *{bonus}* USDT",
    "support": "💬 *OTC NFT Market サポート*\n\n📩 @{support}\n⏱ 15分以内に返信\n\nまたはここに書いてください:",
    "support_sent": "✅ 送信完了! @{support} が15分以内に返信します。🙏",
    "about": "ℹ️ *OTC NFT Market*\n\n最も信頼性の高いNFTギフト取引プラットフォーム。\n\n🔐 エスクロー\n🛡️ 認証\n⭐ 評価\n⚖️ 仲裁\n\n💬 @{support}",
    "lang_pick": "🌐 *言語を選択:*", "back": "⬅️ 戻る",
    "s_active": "🟡 待機中", "s_paid": "🟠 支払済", "s_nft_sent": "📦 NFT送信済",
    "s_done": "✅ 完了", "s_cancelled": "❌ キャンセル",
    "buyer_welcome": "👋 *OTC NFT Marketへようこそ!*\n\n保護された取引に招待されました。\n\n🔐 エスクロー保護。\n\n👇 言語を選択:",
    "buyer_viewing": "👁 *購入者があなたの取引を確認中*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\n⏳ 支払待ち...",
    "buyer_deal": "🤝 *取引オファー*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 *{gift}*\n💰 {amount} {cur}\n👤 販売者: *{seller}*\n⭐ 評価: *{rating}*\n📊 取引数: *{dc}*\n🆔 `{id}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔐 NFT転送まで資金はエスクロー保護。",
    "btn_pay": "💳 支払へ", "btn_cancel_deal": "❌ キャンセル", "btn_dispute": "⚖️ 紛争開始",
    "buyer_pay_info": "💳 *支払詳細*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n📋 支払情報:\n`{req}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️ *正確な*金額を送金してください。\n\n👇 支払後:",
    "btn_confirm_pay": "✅ 支払いました — 確認",
    "buyer_paid": "⏳ *支払確認済!*\n\n💰 {amount} {cur}\n📌 NFT転送待ち\n\n✅ 販売者に通知済み。\n\n⚠️ 応答なし? — @{support}",
    "seller_notif": "🔔 *購入者が支払いました!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n👤 {buyer}\n🆔 `{id}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n👉 NFTギフトを転送してクリック:",
    "btn_nft_sent": "📦 NFTギフトを転送しました",
    "seller_waiting_confirm": "⏳ *購入者の確認待ち*\n\n🎁 {gift} | 💰 {amount} {cur}\n📌 NFT送信済み、購入者の確認待ち。\n\n⚠️ 問題? — @{support}",
    "buyer_nft_received_prompt": "📦 *販売者がNFTを転送しました!*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 {gift}\n💰 {amount} {cur}\n━━━━━━━━━━━━━━━━━━━━━━\n\nNFTギフトの受取を確認してください。\n\n✅ 受取済みなら確認。\n⚖️ 未受取なら紛争開始。",
    "btn_confirm_receipt": "✅ 確認 — NFT受取済み",
    "deal_done_seller": "🎉 *取引完了!*\n\n✅ 購入者がNFT受取を確認\n💰 資金解放\n\nご利用ありがとう! 💎",
    "deal_done_buyer": "🎉 *取引完了!*\n\n✅ NFT受取確認済み\n🔐 エスクロー解除\n\n販売者を評価してください:",
    "review_prompt": "⭐ *販売者を評価:*", "review_thanks": "✅ 評価ありがとうございます!",
    "dispute_opened": "⚖️ *紛争開始*\n\n🆔 `{id}`\n\n@{support} が30分以内に連絡します。",
    "dispute_notif": "⚖️ *紛争開始!*\n\n🆔 `{id}`\n👤 {buyer}\n💰 {amount} {cur}\n\n@{support}",
    "deal_not_found": "❌ *取引が見つかりません*\n\n@{support}",
    "buyer_left": "👤 *購入者が取引を離れました*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\n取引は再び利用可能です。",
    "seller_reminder": "⏰ *リマインダー!*\n\n購入者が `{id}` を支払いましたがNFTを送っていません。\n🎁 {gift} | 💰 {amount} {cur}\n\n@{support}",
    "deal_detail": "📋 *取引詳細*\n\n━━━━━━━━━━━━━━━━━━━━━━\n🆔 `{id}`\n🎁 {gift}\n💰 {amount} {cur}\n📌 {status_icon} {status}\n📅 {date}\n{buyer_line}━━━━━━━━━━━━━━━━━━━━━━",
    "btn_deal_detail": "🔎 詳細",
    "seller_stats": "📊 *統計*\n\n📋 合計: *{total}*\n✅ 完了: *{done}*\n🟡 進行中: *{active}*\n❌ キャンセル: *{cancelled}*\n\n💰 取引高:\n{turnover}\n💵 平均金額: *{avg_deal}*\n⭐ 評価: *{rating}*",
    "search_deal_prompt": "🔍 取引IDを入力:", "search_deal_found": "🔍 *検索結果:*\n\n{result}",
    "search_deal_none": "❌ 取引が見つかりません。", "btn_search": "🔍 取引検索",
    "fee_choice": "💸 *手数料 (3%) を誰が払う?*\n\n💰 金額: *{amount} {cur}*\n\n• 購入者が払う: {amount_with_fee} {cur}\n• あなたが受取: {amount_after_fee} {cur}\n\n選択:",
    "btn_fee_buyer": "👤 購入者が手数料を払う", "btn_fee_seller": "🏪 私が手数料を払う",
    "admin_granted": "🔐 *管理者権限が有効化されました*",
}


# ════════════════════════════════════════════════════
#                    HELPERS
# ════════════════════════════════════════════════════

def get_user(uid):
    if uid not in users:
        users[uid] = {
            "lang": "en", "req": {}, "deals": [], "buyer_deals": [],
            "refs": 0, "rating": 5.0, "rating_count": 0,
            "deals_count": 0, "balance": {},
        }
    return users[uid]

def ulang(ctx):
    return ctx.user_data.get("lang", "en")

def tr(ctx, key, **kw):
    l   = ulang(ctx)
    txt = T.get(l, T["en"]).get(key, T["en"].get(key, key))
    kw.setdefault("support", SUPPORT_USERNAME)
    try:
        txt = txt.format(**kw)
    except Exception:
        pass
    return txt

def tr_raw(lang_code, key, **kw):
    txt = T.get(lang_code, T["en"]).get(key, T["en"].get(key, key))
    kw.setdefault("support", SUPPORT_USERNAME)
    try:
        txt = txt.format(**kw)
    except Exception:
        pass
    return txt

def lang_kb():
    rows  = []
    items = list(LANGS.items())
    for i in range(0, len(items), 2):
        row = [InlineKeyboardButton(items[i][1], callback_data=f"lang_{items[i][0]}")]
        if i + 1 < len(items):
            row.append(InlineKeyboardButton(items[i+1][1], callback_data=f"lang_{items[i+1][0]}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def menu_kb(ctx):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(tr(ctx,"btn_create"),  callback_data="create"),
         InlineKeyboardButton(tr(ctx,"btn_deals"),   callback_data="mydeals")],
        [InlineKeyboardButton(tr(ctx,"btn_refs"),    callback_data="refs"),
         InlineKeyboardButton(tr(ctx,"btn_req"),     callback_data="req")],
        [InlineKeyboardButton(tr(ctx,"btn_lang"),    callback_data="changelang"),
         InlineKeyboardButton(tr(ctx,"btn_support"), callback_data="support")],
        [InlineKeyboardButton(tr(ctx,"btn_stats"),   callback_data="seller_stats"),
         InlineKeyboardButton(tr(ctx,"btn_about"),   callback_data="about")],
    ])

def back_kb(ctx, cb="menu"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(tr(ctx,"back"), callback_data=cb)]])

def status_icon(status):
    return {"active":"🟡","paid":"🟠","nft_sent":"📦","done":"✅","cancelled":"❌"}.get(status,"❓")

def now_str():
    return datetime.now().strftime("%d.%m.%Y %H:%M")


# ════════════════════════════════════════════════════
#                  ADMIN PANEL
# ════════════════════════════════════════════════════

def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Подтвердить оплату", callback_data="adm_pay"),
         InlineKeyboardButton("⭐ Рейтинг",            callback_data="adm_rating")],
        [InlineKeyboardButton("📊 Кол‑во сделок",     callback_data="adm_dc"),
         InlineKeyboardButton("💰 Баланс",             callback_data="adm_bal")],
        [InlineKeyboardButton("👥 Пользователи",       callback_data="adm_users"),
         InlineKeyboardButton("📋 Все сделки",         callback_data="adm_alldeals")],
        [InlineKeyboardButton("🚫 Блокировка",         callback_data="adm_block"),
         InlineKeyboardButton("📊 Статистика",         callback_data="adm_stats")],
        [InlineKeyboardButton("❌ Закрыть панель",     callback_data="adm_close")],
    ])

async def otcteam_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["is_admin"] = True
    await update.message.reply_text(
        tr_raw("ru", "admin_granted"),
        reply_markup=admin_kb(),
        parse_mode="Markdown"
    )
    return ADMIN_ST

async def adm_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q        = update.callback_query
    await q.answer()
    d        = q.data
    back_adm = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В панель", callback_data="adm_back")]])

    if d == "adm_stats":
        ac = sum(1 for dl in deals.values() if dl["status"] == "active")
        pc = sum(1 for dl in deals.values() if dl["status"] == "paid")
        nc = sum(1 for dl in deals.values() if dl["status"] == "nft_sent")
        dc = sum(1 for dl in deals.values() if dl["status"] == "done")
        cc = sum(1 for dl in deals.values() if dl["status"] == "cancelled")
        await q.edit_message_text(
            f"📊 *Статистика OTC NFT Market*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Пользователей: *{len(users)}*\n"
            f"🚫 Заблокировано: *{len(blocked_users)}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 Всего сделок: *{len(deals)}*\n"
            f"🟡 Ожидают: *{ac}*\n"
            f"🟠 Оплачено: *{pc}*\n"
            f"📦 NFT отправлен: *{nc}*\n"
            f"✅ Завершено: *{dc}*\n"
            f"❌ Отменено: *{cc}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=back_adm, parse_mode="Markdown"
        )

    elif d == "adm_pay":
        # Admin triggers buyer payment on an active deal
        active_deals = [(did, dl) for did, dl in deals.items() if dl["status"] == "active"]
        if not active_deals:
            await q.edit_message_text("📭 Нет активных сделок.", reply_markup=back_adm)
            return
        kb = []
        for did, dl in active_deals[:15]:
            kb.append([InlineKeyboardButton(
                f"🟡 #{did[:8]} — {dl['gift']} | {dl['amount']} {dl['currency']}",
                callback_data=f"adm_dopay_{did}"
            )])
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")])
        await q.edit_message_text(
            "💳 *Выберите сделку для подтверждения оплаты:*\n\n"
            "_(Имитирует оплату покупателем — продавец получит уведомление передать NFT)_",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )

    elif d.startswith("adm_dopay_"):
        did  = d[10:]
        deal = deals.get(did)
        if not deal:
            await q.edit_message_text("❌ Сделка не найдена.", reply_markup=back_adm)
            return
        if deal["status"] != "active":
            await q.edit_message_text(f"⚠️ Статус: {deal['status']}", reply_markup=back_adm)
            return
        deal["status"]     = "paid"
        deal["buyer_id"]   = None
        deal["buyer_name"] = "Покупатель"
        sl = get_user(deal["seller_id"]).get("lang","ru")
        try:
            await ctx.bot.send_message(
                chat_id=deal["seller_id"],
                text=tr_raw(sl,"seller_notif",
                            gift=deal["gift"], amount=deal["amount"],
                            cur=CURRENCIES.get(deal["currency"],deal["currency"]),
                            buyer=deal["buyer_name"], id=did[:8]),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(tr_raw(sl,"btn_nft_sent"), callback_data=f"nftsent_{did}")
                ]]),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"adm_dopay error: {e}")
        await q.edit_message_text(
            f"✅ Оплата подтверждена!\n\n🆔 `{did[:8]}`\nПродавец уведомлён.",
            reply_markup=back_adm, parse_mode="Markdown"
        )

    elif d == "adm_block":
        ctx.user_data["adm_action"] = "block"
        await q.edit_message_text("🚫 Введите ID пользователя:", reply_markup=back_adm, parse_mode="Markdown")

    elif d == "adm_rating":
        ctx.user_data["adm_action"] = "rating"
        await q.edit_message_text("⭐ Формат: `ID значение`\nПример: `123456789 4.9`", reply_markup=back_adm, parse_mode="Markdown")

    elif d == "adm_dc":
        ctx.user_data["adm_action"] = "deals_count"
        await q.edit_message_text("📊 Формат: `ID количество`", reply_markup=back_adm, parse_mode="Markdown")

    elif d == "adm_bal":
        ctx.user_data["adm_action"] = "balance"
        curs = " | ".join(CURRENCIES.keys())
        await q.edit_message_text(f"💰 Формат: `ID ВАЛЮТА сумма`\nВалюты: `{curs}`", reply_markup=back_adm, parse_mode="Markdown")

    elif d == "adm_users":
        if not users:
            await q.edit_message_text("📭 Нет пользователей.", reply_markup=back_adm)
            return
        txt = "👥 *Пользователи:*\n\n"
        for uid_k, u in list(users.items())[:20]:
            bm  = "🚫 " if uid_k in blocked_users else ""
            bal = " | ".join(f"{v} {k}" for k,v in u.get("balance",{}).items()) or "—"
            txt += f"{bm}👤 `{uid_k}`\n⭐ {u.get('rating',5.0)} | 📊 {u.get('deals_count',0)} | 💰 {bal}\n\n"
        await q.edit_message_text(txt, reply_markup=back_adm, parse_mode="Markdown")

    elif d == "adm_alldeals":
        if not deals:
            await q.edit_message_text("📭 Нет сделок.", reply_markup=back_adm)
            return
        txt = "📋 *Все сделки:*\n\n"
        for did, dl in list(deals.items())[:20]:
            txt += f"{status_icon(dl['status'])} `{did[:8]}` {dl['gift']} | {dl['amount']} {dl['currency']}\n"
        await q.edit_message_text(txt, reply_markup=back_adm, parse_mode="Markdown")

    elif d == "adm_back":
        await q.edit_message_text(tr_raw("ru","admin_granted"), reply_markup=admin_kb(), parse_mode="Markdown")

    elif d == "adm_close":
        ctx.user_data.pop("is_admin", None)
        await q.edit_message_text("✅ Панель закрыта.")

async def adm_input_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    action   = ctx.user_data.get("adm_action")
    text     = update.message.text.strip()
    back_adm = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В панель", callback_data="adm_back")]])
    try:
        parts  = text.split()
        target = int(parts[0])
        if action == "block":
            if target in blocked_users:
                blocked_users.discard(target)
                await update.message.reply_text(f"✅ Пользователь `{target}` разблокирован.", parse_mode="Markdown", reply_markup=back_adm)
            else:
                blocked_users.add(target)
                await update.message.reply_text(f"🚫 Пользователь `{target}` заблокирован.", parse_mode="Markdown", reply_markup=back_adm)
        elif action == "rating":
            val = round(float(parts[1]), 1)
            get_user(target)["rating"] = val
            await update.message.reply_text(f"✅ Рейтинг `{target}` → *{val}*", parse_mode="Markdown", reply_markup=back_adm)
        elif action == "deals_count":
            val = int(parts[1])
            get_user(target)["deals_count"] = val
            await update.message.reply_text(f"✅ Сделок `{target}` → *{val}*", parse_mode="Markdown", reply_markup=back_adm)
        elif action == "balance":
            cur = parts[1].upper()
            if cur not in CURRENCIES:
                await update.message.reply_text("❌ Неизвестная валюта.", reply_markup=back_adm)
                return ADMIN_ST
            val = float(parts[2])
            get_user(target).setdefault("balance",{})[cur] = val
            await update.message.reply_text(f"✅ Баланс `{target}`: {cur} → *{val}*", parse_mode="Markdown", reply_markup=back_adm)
    except Exception:
        await update.message.reply_text("❌ Ошибка формата.", reply_markup=back_adm)
    ctx.user_data.pop("adm_action", None)
    return ADMIN_ST


# ════════════════════════════════════════════════════
#                  MAIN HANDLERS
# ════════════════════════════════════════════════════

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in blocked_users:
        lang = ctx.user_data.get("lang","ru")
        await update.message.reply_text(tr_raw(lang,"blocked"), parse_mode="Markdown")
        return MENU_ST

    args = ctx.args or []

    if args and args[0].startswith("ref_"):
        try:
            ref = int(args[0][4:])
            if ref != uid:
                get_user(ref)["refs"] = get_user(ref).get("refs",0) + 1
        except Exception:
            pass

    if args and args[0].startswith("deal_"):
        did  = args[0][5:]
        deal = deals.get(did)
        if not deal or deal["status"] in ("done","cancelled","paid","nft_sent"):
            await update.message.reply_text(tr_raw("en","deal_not_found"), parse_mode="Markdown")
            return LANG_ST
        if deal["seller_id"] == uid:
            await update.message.reply_text("⚠️ Это ваша собственная сделка.", parse_mode="Markdown")
            return LANG_ST
        ctx.user_data["pending_deal"] = did
        ctx.user_data["flow"]         = "buyer"
        await update.message.reply_text(T["en"]["buyer_welcome"], reply_markup=lang_kb(), parse_mode="Markdown")
        return LANG_ST

    ctx.user_data["flow"] = "seller"
    await update.message.reply_text(T["en"]["welcome"], reply_markup=lang_kb(), parse_mode="Markdown")
    return LANG_ST


async def main_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    await q.answer()
    d    = q.data
    uid  = update.effective_user.id
    name = update.effective_user.first_name or "User"
    u    = get_user(uid)

    if uid in blocked_users and not d.startswith("adm_"):
        lang = ctx.user_data.get("lang","ru")
        await q.edit_message_text(tr_raw(lang,"blocked"), parse_mode="Markdown")
        return MENU_ST

    if d.startswith("adm_"):
        return await adm_cb(update, ctx)

    # ── Review ────────────────────────────────────
    if d.startswith("rev_"):
        parts     = d.split("_")
        stars     = int(parts[1])
        seller_id = int(parts[2])
        su        = get_user(seller_id)
        rc        = su.get("rating_count",0)
        su["rating"]       = round((su.get("rating",5.0) * rc + stars) / (rc + 1), 1)
        su["rating_count"] = rc + 1
        await q.edit_message_text(
            tr(ctx,"review_thanks"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Menu", callback_data="menu")
            ]]),
            parse_mode="Markdown"
        )
        return MENU_ST

    # ── Language selection ────────────────────────
    if d.startswith("lang_"):
        code = d[5:]
        ctx.user_data["lang"] = code
        u["lang"] = code

        if ctx.user_data.get("flow") == "buyer":
            did  = ctx.user_data.get("pending_deal")
            deal = deals.get(did)
            if not deal or deal["status"] in ("done","cancelled"):
                await q.edit_message_text(tr(ctx,"deal_not_found"), parse_mode="Markdown")
                return MENU_ST
            su           = get_user(deal["seller_id"])
            buyer_amount = deal["amount"]
            if deal.get("fee_mode") == "buyer":
                buyer_amount = round(deal["amount"] * 1.03, 2)
            await q.edit_message_text(
                tr(ctx,"buyer_deal",
                   gift=deal["gift"], amount=buyer_amount,
                   cur=CURRENCIES.get(deal["currency"],deal["currency"]),
                   seller=deal["seller_name"],
                   rating=su.get("rating",5.0), dc=su.get("deals_count",0),
                   id=did[:8]),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tr(ctx,"btn_pay"),         callback_data=f"pay_{did}")],
                    [InlineKeyboardButton(tr(ctx,"btn_dispute"),     callback_data=f"dispute_{did}")],
                    [InlineKeyboardButton(tr(ctx,"btn_cancel_deal"), callback_data="buyer_cancel")],
                ]),
                parse_mode="Markdown"
            )
            try:
                sl = su.get("lang","ru")
                await ctx.bot.send_message(
                    chat_id=deal["seller_id"],
                    text=tr_raw(sl,"buyer_viewing",
                                id=did[:8], gift=deal["gift"],
                                amount=deal["amount"],
                                cur=CURRENCIES.get(deal["currency"],deal["currency"])),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
            return BUYER_ST

        await q.edit_message_text(
            tr(ctx,"menu", name=name, rating=u.get("rating",5.0), dc=u.get("deals_count",0)),
            reply_markup=menu_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    # ── Menu ──────────────────────────────────────
    if d == "menu":
        ctx.user_data["flow"] = "seller"
        ctx.user_data.pop("await", None)
        await q.edit_message_text(
            tr(ctx,"menu", name=name, rating=u.get("rating",5.0), dc=u.get("deals_count",0)),
            reply_markup=menu_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    # ── Create deal ───────────────────────────────
    if d == "create":
        if not u["req"]:
            await q.edit_message_text(
                tr(ctx,"no_req"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tr(ctx,"btn_req"), callback_data="req")],
                    [InlineKeyboardButton(tr(ctx,"back"),    callback_data="menu")],
                ]),
                parse_mode="Markdown"
            )
            return MENU_ST
        my_curs = list(u["req"].keys())
        kb = []
        for i in range(0, len(my_curs), 2):
            row = [InlineKeyboardButton(CURRENCIES[my_curs[i]], callback_data=f"dcur_{my_curs[i]}")]
            if i+1 < len(my_curs):
                row.append(InlineKeyboardButton(CURRENCIES[my_curs[i+1]], callback_data=f"dcur_{my_curs[i+1]}"))
            kb.append(row)
        kb.append([InlineKeyboardButton(tr(ctx,"back"), callback_data="menu")])
        await q.edit_message_text(tr(ctx,"deal_cur"), reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return DEAL_CUR_ST

    if d.startswith("dcur_"):
        cur = d[5:]
        ctx.user_data["dcur"]  = cur
        ctx.user_data["await"] = "amount"
        await q.edit_message_text(
            tr(ctx,"deal_amount", cur=CURRENCIES.get(cur,cur)),
            reply_markup=back_kb(ctx,"create"), parse_mode="Markdown"
        )
        return DEAL_AMT_ST

    # ── Fee choice ────────────────────────────────
    if d in ("fee_buyer","fee_seller"):
        amount = ctx.user_data.get("damount")
        cur    = ctx.user_data.get("dcur")
        if not amount or not cur:
            await q.edit_message_text(
                tr(ctx,"menu", name=name, rating=u.get("rating",5.0), dc=u.get("deals_count",0)),
                reply_markup=menu_kb(ctx), parse_mode="Markdown"
            )
            return MENU_ST
        ctx.user_data["dfee_mode"] = "buyer" if d == "fee_buyer" else "seller"
        ctx.user_data["await"]     = "gift"
        await q.edit_message_text(
            tr(ctx,"deal_gift"),
            reply_markup=back_kb(ctx,"create"), parse_mode="Markdown"
        )
        return DEAL_GIFT_ST

    # ── My deals ──────────────────────────────────
    if d == "mydeals":
        rating    = u.get("rating",5.0)
        dc        = u.get("deals_count",0)
        bal_lines = "\n".join(f"  • {v} {k}" for k,v in u.get("balance",{}).items())
        bal_str   = bal_lines or "  • —"
        header    = f"👤 *Профиль*\n⭐ Рейтинг: *{rating}* / 5.0\n📊 Завершено: *{dc}*\n💳 Баланс:\n{bal_str}\n\n"

        active_deals_kb = []
        detail_kb       = []

        seller_section = ""
        if u["deals"]:
            rows = ""
            for did in reversed(u["deals"][-20:]):
                dl = deals.get(did)
                if dl:
                    rows += tr(ctx,"deal_row", icon=status_icon(dl["status"]),
                               id=did[:8], gift=dl["gift"], amount=dl["amount"], cur=dl["currency"])
                    if dl["status"] == "active":
                        active_deals_kb.append([InlineKeyboardButton(
                            f"🗑 Отменить #{did[:8]}", callback_data=f"cancel_deal_{did}"
                        )])
                    detail_kb.append([InlineKeyboardButton(
                        f"🔎 #{did[:8]} {dl['gift'][:15]}", callback_data=f"detail_{did}"
                    )])
            seller_section = "📤 *Мои продажи:*\n" + rows
        else:
            seller_section = tr(ctx,"no_deals")

        buyer_section = ""
        buyer_deals   = u.get("buyer_deals",[])
        if buyer_deals:
            brows = ""
            for did2 in reversed(buyer_deals[-10:]):
                dl2 = deals.get(did2)
                if dl2:
                    brows += tr(ctx,"deal_row", icon=status_icon(dl2["status"]),
                                id=did2[:8], gift=dl2["gift"], amount=dl2["amount"], cur=dl2["currency"])
            if brows:
                buyer_section = "\n🛒 *История покупок:*\n" + brows

        kb_rows = (
            active_deals_kb
            + detail_kb[:5]
            + [[InlineKeyboardButton(tr(ctx,"btn_search"), callback_data="search_deal")]]
            + [[InlineKeyboardButton(tr(ctx,"back"),       callback_data="menu")]]
        )
        await q.edit_message_text(
            header + seller_section + buyer_section,
            reply_markup=InlineKeyboardMarkup(kb_rows),
            parse_mode="Markdown"
        )
        return MENU_ST

    # ── Cancel deal ───────────────────────────────
    if d.startswith("cancel_deal_"):
        did  = d[12:]
        deal = deals.get(did)
        if not deal:
            await q.answer("❌ Сделка не найдена", show_alert=True)
            return MENU_ST
        if deal["seller_id"] != uid:
            await q.answer("❌ Это не ваша сделка", show_alert=True)
            return MENU_ST
        await q.edit_message_text(
            tr(ctx,"deal_cancel_confirm", id=did[:8], gift=deal["gift"],
               amount=deal["amount"], cur=deal["currency"]),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да, отменить", callback_data=f"confirm_cancel_{did}"),
                 InlineKeyboardButton("❌ Нет",          callback_data="mydeals")],
            ]),
            parse_mode="Markdown"
        )
        return MENU_ST

    if d.startswith("confirm_cancel_"):
        did  = d[15:]
        deal = deals.get(did)
        if deal:
            if deal["status"] in ("paid","done","nft_sent"):
                await q.edit_message_text(tr(ctx,"deal_cancel_fail"), reply_markup=back_kb(ctx,"mydeals"), parse_mode="Markdown")
            else:
                deal["status"] = "cancelled"
                await q.edit_message_text(tr(ctx,"deal_cancelled", id=did[:8]), reply_markup=back_kb(ctx,"mydeals"), parse_mode="Markdown")
        return MENU_ST

    # ── Referrals ─────────────────────────────────
    if d == "refs":
        bot_info = await ctx.bot.get_me()
        await q.edit_message_text(
            tr(ctx,"refs", bot=bot_info.username, uid=uid,
               count=u.get("refs",0), bonus=round(u.get("refs",0)*0.5,2)),
            reply_markup=back_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    # ── Requisites ────────────────────────────────
    if d == "req":
        items = list(CURRENCIES.items())
        kb = []
        for i in range(0, len(items), 2):
            row = []
            for j in range(2):
                if i+j < len(items):
                    code, cname = items[i+j]
                    check = "✅ " if code in u["req"] else ""
                    row.append(InlineKeyboardButton(f"{check}{cname}", callback_data=f"rq_{code}"))
            kb.append(row)
        kb.append([InlineKeyboardButton(tr(ctx,"back"), callback_data="menu")])
        await q.edit_message_text(tr(ctx,"req_menu"), reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return REQ_CUR_ST

    if d.startswith("rq_"):
        cur = d[3:]
        if cur in CURRENCIES:
            ctx.user_data["rq_cur"] = cur
            ctx.user_data["await"]  = "req"
            await q.edit_message_text(
                tr(ctx,"req_enter", cur=CURRENCIES.get(cur,cur)),
                reply_markup=back_kb(ctx,"req"), parse_mode="Markdown"
            )
            return REQ_IN_ST
        return MENU_ST

    if d == "changelang":
        await q.edit_message_text(tr(ctx,"lang_pick"), reply_markup=lang_kb(), parse_mode="Markdown")
        return LANG_ST

    if d == "support":
        ctx.user_data["await"] = "support"
        await q.edit_message_text(tr(ctx,"support"), reply_markup=back_kb(ctx), parse_mode="Markdown")
        return SUPPORT_ST

    if d == "about":
        await q.edit_message_text(tr(ctx,"about"), reply_markup=back_kb(ctx), parse_mode="Markdown")
        return MENU_ST

    # ── Seller stats ──────────────────────────────
    if d == "seller_stats":
        my_deals  = [deals[did] for did in u.get("deals",[]) if did in deals]
        total     = len(my_deals)
        done_c    = sum(1 for dl in my_deals if dl["status"] == "done")
        act_c     = sum(1 for dl in my_deals if dl["status"] == "active")
        canc_c    = sum(1 for dl in my_deals if dl["status"] == "cancelled")
        turnover  = {}
        for dl in my_deals:
            if dl["status"] == "done":
                turnover[dl["currency"]] = turnover.get(dl["currency"],0) + dl["amount"]
        turn_str  = "".join(f"  • {round(v,2)} {c}\n" for c,v in turnover.items()) or "  • —\n"
        done_dl   = [dl for dl in my_deals if dl["status"] == "done"]
        avg       = round(sum(dl["amount"] for dl in done_dl)/len(done_dl),2) if done_dl else 0
        await q.edit_message_text(
            tr(ctx,"seller_stats", total=total, done=done_c, active=act_c,
               cancelled=canc_c, turnover=turn_str,
               avg_deal=avg if avg else "—", rating=u.get("rating",5.0)),
            reply_markup=back_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    # ── Deal detail ───────────────────────────────
    if d.startswith("detail_"):
        did  = d[7:]
        deal = deals.get(did)
        if not deal:
            await q.answer("❌ Не найдена", show_alert=True)
            return MENU_ST
        snames     = {"active":"Ожидает","paid":"Оплачено","nft_sent":"NFT отправлен","done":"Завершена","cancelled":"Отменена"}
        buyer_line = f"👤 Покупатель: *{deal['buyer_name']}*\n" if deal.get("buyer_name") else ""
        await q.edit_message_text(
            tr(ctx,"deal_detail", id=did[:8], gift=deal["gift"],
               amount=deal["amount"], cur=CURRENCIES.get(deal["currency"],deal["currency"]),
               status_icon=status_icon(deal["status"]),
               status=snames.get(deal["status"],deal["status"]),
               date=deal.get("created","—"), buyer_line=buyer_line),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr(ctx,"back"), callback_data="mydeals")]]),
            parse_mode="Markdown"
        )
        return MENU_ST

    # ── Search deal ───────────────────────────────
    if d == "search_deal":
        ctx.user_data["await"] = "search_deal"
        await q.edit_message_text(tr(ctx,"search_deal_prompt"), reply_markup=back_kb(ctx,"mydeals"), parse_mode="Markdown")
        return MENU_ST

    # ════════════════════════════════════════════════
    # BUYER FLOW
    # ════════════════════════════════════════════════

    # ── Open payment screen ───────────────────────
    if d.startswith("pay_"):
        did  = d[4:]
        deal = deals.get(did)
        if not deal or deal["status"] in ("done","cancelled","paid","nft_sent"):
            await q.edit_message_text(tr(ctx,"deal_not_found"), parse_mode="Markdown")
            return MENU_ST
        if deal["seller_id"] == uid:
            await q.answer("❌ Нельзя купить собственную сделку", show_alert=True)
            return BUYER_ST
        if deal.get("locked_by") and deal["locked_by"] != uid:
            await q.answer("⚠️ Сделка уже открыта другим покупателем.", show_alert=True)
            return BUYER_ST
        deal["locked_by"]  = uid
        req                = get_user(deal["seller_id"])["req"].get(deal["currency"],"—")
        fee_mode           = deal.get("fee_mode","seller")
        display_amount     = deal["amount"]
        if fee_mode == "buyer":
            display_amount = round(deal["amount"] * 1.03, 2)
        await q.edit_message_text(
            tr(ctx,"buyer_pay_info", gift=deal["gift"], amount=display_amount,
               cur=CURRENCIES.get(deal["currency"],deal["currency"]), req=req),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(tr(ctx,"btn_confirm_pay"),  callback_data=f"confirmpay_{did}")],
                [InlineKeyboardButton(tr(ctx,"btn_dispute"),      callback_data=f"dispute_{did}")],
                [InlineKeyboardButton(tr(ctx,"btn_cancel_deal"),  callback_data=f"buyer_cancel_{did}")],
            ]),
            parse_mode="Markdown"
        )
        return BUYER_ST

    # ── Confirm payment ───────────────────────────
    if d.startswith("confirmpay_"):
        did  = d[11:]
        deal = deals.get(did)
        if not deal:
            await q.edit_message_text(tr(ctx,"deal_not_found"), parse_mode="Markdown")
            return MENU_ST
        if deal["seller_id"] == uid:
            await q.answer("❌ Нельзя оплатить собственную сделку", show_alert=True)
            return BUYER_ST
        if deal["status"] != "active":
            await q.answer("⚠️ Сделка уже не активна.", show_alert=True)
            return BUYER_ST

        deal["status"]     = "paid"
        deal["buyer_id"]   = uid
        deal["buyer_name"] = update.effective_user.full_name or "Buyer"
        u.setdefault("buyer_deals",[])
        if did not in u["buyer_deals"]:
            u["buyer_deals"].append(did)

        fee_mode       = deal.get("fee_mode","seller")
        display_amount = deal["amount"]
        if fee_mode == "buyer":
            display_amount = round(deal["amount"] * 1.03, 2)

        await q.edit_message_text(
            tr(ctx,"buyer_paid", amount=display_amount,
               cur=CURRENCIES.get(deal["currency"],deal["currency"])),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(tr(ctx,"btn_dispute"), callback_data=f"dispute_{did}")],
                [InlineKeyboardButton(tr(ctx,"btn_support"), callback_data="support")],
            ]),
            parse_mode="Markdown"
        )

        # Notify seller
        sl = get_user(deal["seller_id"]).get("lang","ru")
        try:
            await ctx.bot.send_message(
                chat_id=deal["seller_id"],
                text=tr_raw(sl,"seller_notif",
                            gift=deal["gift"], amount=display_amount,
                            cur=CURRENCIES.get(deal["currency"],deal["currency"]),
                            buyer=deal["buyer_name"], id=did[:8]),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(tr_raw(sl,"btn_nft_sent"), callback_data=f"nftsent_{did}")
                ]]),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Seller notify error: {e}")

        # Reminder in 15 min
        async def seller_reminder_job(context):
            d2 = deals.get(did)
            if d2 and d2["status"] == "paid":
                s_lang = get_user(d2["seller_id"]).get("lang","ru")
                try:
                    await context.bot.send_message(
                        chat_id=d2["seller_id"],
                        text=tr_raw(s_lang,"seller_reminder",
                                    id=did[:8], gift=d2["gift"],
                                    amount=display_amount,
                                    cur=CURRENCIES.get(d2["currency"],d2["currency"])),
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(tr_raw(s_lang,"btn_nft_sent"), callback_data=f"nftsent_{did}")
                        ]]),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        try:
            ctx.application.job_queue.run_once(seller_reminder_job, when=900, name=f"remind_{did}")
        except Exception:
            pass
        return BUYER_ST

    # ── Dispute ───────────────────────────────────
    if d.startswith("dispute_"):
        did  = d[8:]
        deal = deals.get(did)
        if not deal:
            await q.edit_message_text(tr(ctx,"deal_not_found"), parse_mode="Markdown")
            return MENU_ST
        await q.edit_message_text(
            tr(ctx,"dispute_opened", id=did[:8]),
            reply_markup=back_kb(ctx,"menu"), parse_mode="Markdown"
        )
        sl = get_user(deal["seller_id"]).get("lang","ru")
        try:
            await ctx.bot.send_message(
                chat_id=deal["seller_id"],
                text=tr_raw(sl,"dispute_notif", id=did[:8],
                            buyer=update.effective_user.full_name or "Buyer",
                            amount=deal["amount"],
                            cur=CURRENCIES.get(deal["currency"],deal["currency"])),
                parse_mode="Markdown"
            )
        except Exception:
            pass
        return BUYER_ST

    # ── Buyer cancel ──────────────────────────────
    if d == "buyer_cancel" or d.startswith("buyer_cancel_"):
        did = d[13:] if d.startswith("buyer_cancel_") else ctx.user_data.get("pending_deal")
        if did:
            deal = deals.get(did)
            if deal and deal.get("status") == "active":
                deal.pop("locked_by", None)
                sl = get_user(deal["seller_id"]).get("lang","ru")
                try:
                    await ctx.bot.send_message(
                        chat_id=deal["seller_id"],
                        text=tr_raw(sl,"buyer_left", id=did[:8],
                                    gift=deal["gift"], amount=deal["amount"],
                                    cur=CURRENCIES.get(deal["currency"],deal["currency"])),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        ctx.user_data.pop("pending_deal", None)
        ctx.user_data["flow"] = "seller"
        await q.edit_message_text(
            tr(ctx,"menu", name=name, rating=u.get("rating",5.0), dc=u.get("deals_count",0)),
            reply_markup=menu_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    # ════════════════════════════════════════════════
    # SELLER: marks NFT as sent  →  buyer must confirm
    # ════════════════════════════════════════════════
    if d.startswith("nftsent_"):
        did  = d[8:]
        deal = deals.get(did)
        if not deal:
            await q.answer("❌ Сделка не найдена", show_alert=True)
            return MENU_ST
        if deal["seller_id"] != uid:
            await q.answer("❌ Это не ваша сделка", show_alert=True)
            return MENU_ST
        if deal["status"] != "paid":
            await q.answer("⚠️ Некорректный статус", show_alert=True)
            return MENU_ST

        deal["status"] = "nft_sent"

        fee_mode       = deal.get("fee_mode","seller")
        display_amount = deal["amount"]
        if fee_mode == "buyer":
            display_amount = round(deal["amount"] * 1.03, 2)

        # Seller sees: waiting for buyer confirmation
        sl_lang = get_user(uid).get("lang","ru")
        await q.edit_message_text(
            tr_raw(sl_lang,"seller_waiting_confirm",
                   gift=deal["gift"], amount=display_amount,
                   cur=CURRENCIES.get(deal["currency"],deal["currency"])),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚖️ Открыть спор", callback_data=f"dispute_{did}")
            ]]),
            parse_mode="Markdown"
        )

        # Notify buyer: confirm receipt
        if deal.get("buyer_id"):
            bl = get_user(deal["buyer_id"]).get("lang","ru")
            try:
                await ctx.bot.send_message(
                    chat_id=deal["buyer_id"],
                    text=tr_raw(bl,"buyer_nft_received_prompt",
                                gift=deal["gift"], amount=display_amount,
                                cur=CURRENCIES.get(deal["currency"],deal["currency"])),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(tr_raw(bl,"btn_confirm_receipt"), callback_data=f"confirmreceipt_{did}")],
                        [InlineKeyboardButton("⚖️ Открыть спор",               callback_data=f"dispute_{did}")],
                    ]),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Buyer receipt notify error: {e}")
        else:
            # Admin-triggered payment: no real buyer — auto-complete the deal
            deal["status"] = "done"
            seller_u = get_user(deal["seller_id"])
            seller_u["deals_count"] = seller_u.get("deals_count", 0) + 1
            sl_done = get_user(uid).get("lang","ru")
            try:
                await ctx.bot.send_message(
                    chat_id=deal["seller_id"],
                    text=tr_raw(sl_done,"deal_done_seller"),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        return MENU_ST

    # ════════════════════════════════════════════════
    # BUYER: confirms receipt of NFT  →  deal done
    # ════════════════════════════════════════════════
    if d.startswith("confirmreceipt_"):
        did  = d[15:]
        deal = deals.get(did)
        if not deal:
            await q.edit_message_text(tr(ctx,"deal_not_found"), parse_mode="Markdown")
            return MENU_ST
        if deal.get("buyer_id") != uid:
            await q.answer("❌ Это не ваша сделка", show_alert=True)
            return BUYER_ST
        if deal["status"] != "nft_sent":
            await q.answer("⚠️ Некорректный статус", show_alert=True)
            return BUYER_ST

        deal["status"] = "done"
        seller_u = get_user(deal["seller_id"])
        seller_u["deals_count"] = seller_u.get("deals_count",0) + 1

        # Buyer: done + review
        await q.edit_message_text(
            tr(ctx,"deal_done_buyer"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⭐1", callback_data=f"rev_1_{deal['seller_id']}"),
                InlineKeyboardButton("⭐2", callback_data=f"rev_2_{deal['seller_id']}"),
                InlineKeyboardButton("⭐3", callback_data=f"rev_3_{deal['seller_id']}"),
                InlineKeyboardButton("⭐4", callback_data=f"rev_4_{deal['seller_id']}"),
                InlineKeyboardButton("⭐5", callback_data=f"rev_5_{deal['seller_id']}"),
            ]]),
            parse_mode="Markdown"
        )

        # Notify seller: deal complete
        sl = get_user(deal["seller_id"]).get("lang","ru")
        try:
            await ctx.bot.send_message(
                chat_id=deal["seller_id"],
                text=tr_raw(sl,"deal_done_seller"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Главное меню", callback_data="menu")
                ]]),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Seller done notify error: {e}")
        return REVIEW_ST

    return MENU_ST


# ════════════════════════════════════════════════════
#                  MESSAGE HANDLER
# ════════════════════════════════════════════════════

async def msg_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    if uid in blocked_users:
        lang = ctx.user_data.get("lang","ru")
        await update.message.reply_text(tr_raw(lang,"blocked"), parse_mode="Markdown")
        return MENU_ST

    text = update.message.text.strip()
    u    = get_user(uid)
    aw   = ctx.user_data.get("await")
    name = update.effective_user.first_name or "User"

    if ctx.user_data.get("is_admin") and ctx.user_data.get("adm_action"):
        return await adm_input_handler(update, ctx)

    if aw == "req":
        cur = ctx.user_data.get("rq_cur")
        if cur:
            u["req"][cur] = text
            ctx.user_data.pop("await", None)
            ctx.user_data.pop("rq_cur", None)
            await update.message.reply_text(
                tr(ctx,"req_saved", cur=CURRENCIES.get(cur,cur)),
                reply_markup=menu_kb(ctx), parse_mode="Markdown"
            )
        return MENU_ST

    if aw == "amount":
        try:
            amount = float(text.replace(",",".").replace(" ",""))
            if amount <= 0:
                raise ValueError
            cur     = ctx.user_data.get("dcur","USDT")
            min_val = MIN_AMOUNTS.get(cur,1)
            if amount < min_val:
                await update.message.reply_text(
                    tr(ctx,"min_amount", min=min_val, cur=CURRENCIES.get(cur,cur)),
                    parse_mode="Markdown"
                )
                return DEAL_AMT_ST
            ctx.user_data["damount"] = amount
            fp  = 0.03
            awf = round(amount * (1 + fp), 2)
            aaf = round(amount * (1 - fp), 2)
            await update.message.reply_text(
                tr(ctx,"fee_choice", amount=amount, cur=CURRENCIES.get(cur,cur),
                   amount_with_fee=awf, amount_after_fee=aaf),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tr(ctx,"btn_fee_buyer"),  callback_data="fee_buyer")],
                    [InlineKeyboardButton(tr(ctx,"btn_fee_seller"), callback_data="fee_seller")],
                    [InlineKeyboardButton(tr(ctx,"back"),           callback_data="create")],
                ]),
                parse_mode="Markdown"
            )
            return DEAL_AMT_ST
        except ValueError:
            await update.message.reply_text(tr(ctx,"bad_amount"), parse_mode="Markdown")
            return DEAL_AMT_ST

    if aw == "gift":
        cur    = ctx.user_data.get("dcur")
        amount = ctx.user_data.get("damount")
        if not cur or not amount:
            await update.message.reply_text(
                tr(ctx,"menu", name=name, rating=u.get("rating",5.0), dc=u.get("deals_count",0)),
                reply_markup=menu_kb(ctx), parse_mode="Markdown"
            )
            return MENU_ST
        fee_mode = ctx.user_data.get("dfee_mode","seller")
        did      = str(uuid.uuid4()).replace("-","")[:12].upper()
        bot_info = await ctx.bot.get_me()
        deals[did] = {
            "seller_id":   uid,
            "seller_name": update.effective_user.full_name or "Seller",
            "currency":    cur,
            "amount":      amount,
            "gift":        text,
            "status":      "active",
            "buyer_id":    None,
            "buyer_name":  None,
            "created":     now_str(),
            "fee_mode":    fee_mode,
        }
        u["deals"].append(did)
        ctx.user_data.pop("await",     None)
        ctx.user_data.pop("dcur",      None)
        ctx.user_data.pop("damount",   None)
        ctx.user_data.pop("dfee_mode", None)
        await update.message.reply_text(
            tr(ctx,"deal_created", gift=text, amount=amount,
               cur=CURRENCIES.get(cur,cur), id=did,
               bot=bot_info.username, date=now_str()),
            reply_markup=menu_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    if aw == "search_deal":
        ctx.user_data.pop("await", None)
        query = text.upper().strip()
        found = [(did,dl) for did,dl in deals.items()
                 if did.upper().startswith(query) and dl["seller_id"] == uid]
        if not found:
            found = [(did,dl) for did,dl in deals.items() if did.upper().startswith(query)]
        if not found:
            await update.message.reply_text(tr(ctx,"search_deal_none"), reply_markup=menu_kb(ctx), parse_mode="Markdown")
        else:
            rows = "".join(
                tr(ctx,"deal_row", icon=status_icon(dl["status"]),
                   id=did[:8], gift=dl["gift"], amount=dl["amount"], cur=dl["currency"])
                for did,dl in found[:10]
            )
            await update.message.reply_text(
                tr(ctx,"search_deal_found", result=rows),
                reply_markup=menu_kb(ctx), parse_mode="Markdown"
            )
        return MENU_ST

    if aw == "support":
        ctx.user_data.pop("await", None)
        sender_username = update.effective_user.username
        sender_mention  = f"@{sender_username}" if sender_username else update.effective_user.full_name or str(uid)
        try:
            await update.message.forward(chat_id=f"@{SUPPORT_USERNAME}")
        except Exception:
            pass
        try:
            await ctx.bot.send_message(
                chat_id=f"@{SUPPORT_USERNAME}",
                text=(
                    f"📩 *Новое сообщение*\n\n"
                    f"👤 ID: `{uid}`\n"
                    f"👤 Имя: {update.effective_user.full_name}\n"
                    f"📱 Username: {sender_mention}\n"
                    f"📝 Сообщение: {text}"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
        await update.message.reply_text(
            tr(ctx,"support_sent"),
            reply_markup=menu_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    await update.message.reply_text(
        tr(ctx,"menu", name=name, rating=u.get("rating",5.0), dc=u.get("deals_count",0)),
        reply_markup=menu_kb(ctx), parse_mode="Markdown"
    )
    return MENU_ST


# ════════════════════════════════════════════════════
#                       MAIN
# ════════════════════════════════════════════════════

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    all_cb  = [CallbackQueryHandler(main_cb)]
    all_msg = [MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler)]

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start",   start),
            CommandHandler("otcteam", otcteam_cmd),
        ],
        states={
            LANG_ST:      all_cb,
            MENU_ST:      all_cb + all_msg,
            REQ_CUR_ST:   all_cb,
            REQ_IN_ST:    all_msg + all_cb,
            DEAL_CUR_ST:  all_cb,
            DEAL_AMT_ST:  all_msg + all_cb,
            DEAL_GIFT_ST: all_msg + all_cb,
            BUYER_ST:     all_cb + all_msg,
            SUPPORT_ST:   all_msg + all_cb,
            ADMIN_ST:     all_msg + all_cb,
            REVIEW_ST:    all_cb,
        },
        fallbacks=[
            CommandHandler("start",   start),
            CommandHandler("otcteam", otcteam_cmd),
        ],
        per_message=False,
        allow_reentry=True,
    )

    app.add_handler(conv)

    async def post_init(application):
        await application.bot.set_my_commands([])

    app.post_init = post_init
    print("✅ OTC NFT Market Bot v3.0 running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
