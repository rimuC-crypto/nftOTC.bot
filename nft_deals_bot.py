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

# States
LANG_ST = 1
MENU_ST = 2
REQ_CUR_ST = 3
REQ_IN_ST = 4
DEAL_CUR_ST = 5
DEAL_AMT_ST = 6
DEAL_GIFT_ST = 7
BUYER_ST = 8
SUPPORT_ST = 9
ADMIN_ST = 10
REVIEW_ST = 11

# Storage
users = {}
deals = {}
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
    "UAH": "🇺🇦 UAH",
    "RUB": "🇷🇺 RUB",
    "KZT": "🇰🇿 KZT",
    "CNY": "🇨🇳 CNY",
    "USDT": "💵 USDT",
    "STARS": "⭐ Stars",
}

# ══════════════════════════════════════════════════
#                  TRANSLATIONS
# ══════════════════════════════════════════════════
T = {}

T["ru"] = {
    "welcome": (
        "💎 *OTC NFT Market*\n\n"
        "Добро пожаловать на *самую безопасную* площадку\n"
        "для торговли NFT подарками в Telegram!\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🔐 *Эскроу-защита* каждой сделки\n"
        "⚡️ Подтверждение транзакций в реальном времени\n"
        "🛡️ Верификация продавцов и покупателей\n"
        "🌍 Поддержка 6 валют\n"
        "💬 Поддержка 24/7\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Выберите язык:"
    ),
    "blocked": "⛔ Ваш аккаунт заблокирован. Обратитесь в поддержку: @{support}",
    "menu": (
        "🏠 *OTC NFT Market*\n\n"
        "👤 {name}\n"
        "⭐ Рейтинг: *{rating}* | 📊 Сделок: *{dc}*\n\n"
        "Выберите действие:"
    ),
    "btn_create": "➕ Создать сделку",
    "btn_deals": "📂 Мои сделки",
    "btn_refs": "👥 Рефералы",
    "btn_req": "💳 Реквизиты",
    "btn_lang": "🌐 Язык",
    "btn_support": "💬 Поддержка",
    "btn_about": "ℹ️ О маркете",
    "no_req": (
        "⚠️ *Реквизиты не привязаны*\n\n"
        "Для создания сделки необходимо сначала\n"
        "привязать платёжные реквизиты.\n\n"
        "Это нужно чтобы покупатели знали\n"
        "куда переводить оплату.\n\n"
        "👇 Перейдите в раздел *Реквизиты*"
    ),
    "req_menu": "💳 *Реквизиты*\n\nВыберите валюту для привязки.\n✅ — уже привязано:",
    "req_enter": (
        "✏️ *Привязка реквизитов — {cur}*\n\n"
        "Введите ваши платёжные данные:\n\n"
        "• Для карт: номер карты\n"
        "• Для USDT: адрес TRC20/ERC20\n"
        "• Для Stars: username в Telegram\n\n"
        "_(Эти данные увидит покупатель для оплаты)_"
    ),
    "req_saved": "✅ *Реквизиты сохранены!*\n\nВалюта: *{cur}*\n\nТеперь вы можете создавать сделки в этой валюте.",
    "deal_cur": "💱 *Создание сделки — Шаг 1/3*\n\nВыберите валюту расчёта.\nДоступны валюты с привязанными реквизитами:",
    "deal_amount": "💰 *Создание сделки — Шаг 2/3*\n\nВведите сумму сделки в *{cur}*:\n\n_(Именно столько заплатит покупатель)_",
    "deal_gift": "🎁 *Создание сделки — Шаг 3/3*\n\nВведите название NFT подарка:\n\n_(Например: «Плюшевый мишка», «Торт», «Сердце»)_",
    "bad_amount": "❌ Неверный формат суммы. Введите число, например: `1500` или `25.5`",
    "deal_created": (
        "✅ *Сделка успешно создана!*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🎁 NFT подарок: *{gift}*\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "🆔 ID сделки: `{id}`\n"
        "📅 Создана: {date}\n"
        "📌 Статус: 🟡 Ожидает покупателя\n"
        "💸 Комиссия маркета: 3%\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "🔗 *Ссылка для покупателя:*\n"
        "`https://t.me/{bot}?start=deal_{id}`\n\n"
        "📤 Отправьте эту ссылку покупателю.\n"
        "Как только он оплатит — вы получите уведомление."
    ),
    "no_deals": "📭 У вас пока нет сделок.\n\nСоздайте первую сделку!",
    "deals_list": "📂 *Ваши сделки:*\n\n{list}",
    "deal_row": "{icon} `{id}` — 🎁 *{gift}* | 💰 {amount} {cur}\n",
    "deal_cancel_confirm": (
        "🗑 *Отменить сделку?*\n\n"
        "🆔 `{id}`\n"
        "🎁 {gift} | 💰 {amount} {cur}\n\n"
        "⚠️ Отменить можно только если покупатель\n"
        "ещё не внёс оплату."
    ),
    "deal_cancelled": "✅ Сделка `{id}` отменена.",
    "deal_cancel_fail": "❌ Нельзя отменить — покупатель уже оплатил.\nОбратитесь в поддержку: @{support}",
    "refs": (
        "👥 *Реферальная программа*\n\n"
        "Приглашайте друзей и зарабатывайте *0.5 USDT*\n"
        "за каждого активного реферала!\n\n"
        "🔗 *Ваша реферальная ссылка:*\n"
        "`https://t.me/{bot}?start=ref_{uid}`\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "👤 Приглашено: *{count}* чел.\n"
        "💎 Заработано: *{bonus}* USDT\n"
        "━━━━━━━━━━━━━━━━"
    ),
    "support": (
        "💬 *Служба поддержки OTC NFT Market*\n\n"
        "Мы работаем *24/7* и готовы помочь\n"
        "с любым вопросом!\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📩 Менеджер: @{support}\n"
        "⏱ Время ответа: до 15 минут\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Или напишите сообщение прямо здесь:"
    ),
    "support_sent": "✅ *Сообщение отправлено!*\n\nНаш менеджер @{support}\nответит вам в течение 15 минут.\n\nСпасибо за обращение! 🙏",
    "about": (
        "ℹ️ *OTC NFT Market — Официальная площадка*\n\n"
        "💎 Самый надёжный способ покупать и продавать\n"
        "NFT подарки в Telegram\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🔐 *Система безопасности:*\n\n"
        "• *Эскроу-защита* — средства блокируются\n"
        "  до подтверждения передачи NFT\n"
        "• *Верификация* — каждый пользователь\n"
        "  проходит проверку личности\n"
        "• *Рейтинговая система* — история сделок\n"
        "  и отзывы для каждого продавца\n"
        "• *Арбитраж* — решение спорных ситуаций\n"
        "  нашими модераторами в течение 24ч\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📊 *Как работает платформа:*\n\n"
        "1️⃣ Продавец создаёт сделку\n"
        "2️⃣ Покупатель получает ссылку\n"
        "3️⃣ Покупатель оплачивает через эскроу\n"
        "4️⃣ Продавец передаёт NFT подарок\n"
        "5️⃣ Покупатель подтверждает получение\n"
        "6️⃣ Средства разблокированы ✅\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💬 Поддержка: @{support}\n"
        "📊 Версия: 2.1"
    ),
    "lang_pick": "🌐 *Выберите язык интерфейса:*",
    "back": "⬅️ Назад",
    "s_active": "🟡 Ожидает",
    "s_paid": "🟠 Оплачено",
    "s_done": "✅ Завершена",
    "s_cancelled": "❌ Отменена",
    "buyer_welcome": (
        "👋 *Добро пожаловать в OTC NFT Market!*\n\n"
        "Вас пригласили к участию в защищённой сделке.\n\n"
        "🔐 Все транзакции на нашей платформе\n"
        "проходят через систему эскроу-защиты.\n\n"
        "Выберите язык:"
    ),
    "buyer_viewing": (
        "👁 *Покупатель просматривает вашу сделку*\n\n"
        "🆔 `{id}`\n"
        "🎁 {gift} | 💰 {amount} {cur}\n\n"
        "Ожидайте оплаты..."
    ),
    "buyer_deal": (
        "🤝 *Предложение о сделке*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🎁 NFT подарок: *{gift}*\n"
        "💰 Сумма к оплате: *{amount} {cur}*\n"
        "👤 Продавец: *{seller}*\n"
        "⭐ Рейтинг продавца: *{rating}*\n"
        "📊 Сделок завершено: *{dc}*\n"
        "🆔 ID сделки: `{id}`\n"
        "📌 Статус: 🟡 Ожидает оплаты\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "🔐 *Гарантия безопасности:*\n"
        "Ваши средства будут заблокированы\n"
        "в эскроу до момента передачи NFT.\n"
        "В случае проблем — @{support}"
    ),
    "btn_pay": "💳 Перейти к оплате",
    "btn_cancel_deal": "❌ Отменить",
    "btn_dispute": "⚖️ Открыть спор",
    "buyer_pay_info": (
        "💳 *Реквизиты для оплаты*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🎁 Подарок: *{gift}*\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "📋 Реквизиты продавца:\n"
        "`{req}`\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "⚠️ *Важно:*\n"
        "• Переведите *точную* сумму\n"
        "• Сохраните чек об оплате\n"
        "• После перевода нажмите «Подтвердить»\n\n"
        "👇 Нажмите после оплаты:"
    ),
    "btn_confirm_pay": "✅ Я оплатил — Подтвердить",
    "buyer_paid": (
        "⏳ *Оплата получена и проверяется*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "📌 Статус: 🟠 Обрабатывается\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "✅ Продавец получил уведомление.\n"
        "NFT подарок будет передан в ближайшее время.\n\n"
        "🔔 Вы получите уведомление о передаче.\n\n"
        "⚠️ Если продавец не отвечает более 30 минут —\n"
        "откройте спор или напишите @{support}"
    ),
    "seller_notif": (
        "🔔 *НОВАЯ ОПЛАТА ПО ВАШЕЙ СДЕЛКЕ!*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🎁 Подарок: *{gift}*\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "👤 Покупатель: *{buyer}*\n"
        "🆔 ID: `{id}`\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "✅ Покупатель подтвердил оплату.\n\n"
        "👉 Передайте NFT подарок покупателю\n"
        "и нажмите кнопку ниже:"
    ),
    "btn_nft_sent": "✅ NFT подарок передан",
    "deal_done_seller": (
        "🎉 *Сделка успешно завершена!*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "✅ NFT подарок передан покупателю\n"
        "💰 Средства разблокированы\n"
        "📊 Ваш счётчик сделок обновлён\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Спасибо за использование OTC NFT Market! 💎"
    ),
    "deal_done_buyer": (
        "🎉 *NFT подарок получен!*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "✅ Сделка успешно завершена\n"
        "🔐 Эскроу-защита снята\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Пожалуйста, оцените продавца:"
    ),
    "review_prompt": "⭐ *Оцените продавца*\n\nВыберите оценку от 1 до 5:",
    "review_thanks": "✅ Спасибо за отзыв!\n\nВаша оценка учтена. Это помогает другим пользователям.",
    "dispute_opened": (
        "⚖️ *Спор открыт*\n\n"
        "Ваш запрос передан модераторам.\n\n"
        "🆔 ID сделки: `{id}`\n\n"
        "Наш специалист @{support} свяжется с вами\n"
        "в течение 30 минут для решения вопроса."
    ),
    "dispute_notif": (
        "⚖️ *ОТКРЫТ СПОР ПО СДЕЛКЕ!*\n\n"
        "🆔 ID: `{id}`\n"
        "👤 Покупатель: {buyer}\n"
        "💰 {amount} {cur}\n\n"
        "Обратитесь к покупателю или в поддержку @{support}"
    ),
    "deal_not_found": (
        "❌ *Сделка не найдена*\n\n"
        "Возможные причины:\n"
        "• Сделка уже завершена\n"
        "• Неверная ссылка\n"
        "• Сделка была отменена\n\n"
        "По вопросам обращайтесь: @{support}"
    ),
    "admin_granted": "🔐 *Права администратора активированы*\n\nИспользуйте кнопки ниже для управления:",
    # Commission choice for buyer
    "fee_choice": (
        "💸 *Кто покрывает комиссию маркета (3%)?*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💰 Базовая сумма: *{amount} {cur}*\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "• *Покупатель платит комиссию* — вы получаете {amount} {cur}, покупатель платит {amount_with_fee} {cur}\n"
        "• *Продавец покрывает комиссию* — покупатель платит {amount} {cur}, вы получаете {amount_after_fee} {cur}\n\n"
        "Выберите:"
    ),
    "btn_fee_buyer": "👤 Покупатель платит комиссию (+3%)",
    "btn_fee_seller": "🏪 Я покрываю комиссию (-3%)",
    # Minimum amount
    "min_amount": "❌ Минимальная сумма сделки: *{min} {cur}*\n\nВведите большую сумму:",
    # Deal search
    "search_deal_prompt": "🔍 *Поиск сделки по ID*\n\nВведите ID сделки (или первые символы):",
    "search_deal_found": "🔍 *Результаты поиска:*\n\n{result}",
    "search_deal_none": "❌ Сделка с таким ID не найдена.",
    "btn_search": "🔍 Найти сделку",
    # Seller stats
    "seller_stats": (
        "📊 *Статистика продавца*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📋 Всего сделок создано: *{total}*\n"
        "✅ Завершено: *{done}*\n"
        "🟡 Активных: *{active}*\n"
        "❌ Отменено: *{cancelled}*\n"
        "━━━━━━━━━━━━━━━━\n"
        "💰 *Оборот по валютам:*\n"
        "{turnover}"
        "━━━━━━━━━━━━━━━━\n"
        "💵 Средний чек: *{avg_deal}*\n"
        "⭐ Рейтинг: *{rating}* / 5.0\n"
        "━━━━━━━━━━━━━━━━"
    ),
    "btn_stats": "📊 Статистика",
    # Buyer left notification
    "buyer_left": (
        "👤 *Покупатель покинул сделку*\n\n"
        "🆔 `{id}`\n"
        "🎁 {gift} | 💰 {amount} {cur}\n\n"
        "Сделка снова доступна для покупателей."
    ),
    # Deal detail card
    "deal_detail": (
        "📋 *Детали сделки*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🆔 ID: `{id}`\n"
        "🎁 Подарок: *{gift}*\n"
        "💰 Сумма: *{amount} {cur}*\n"
        "📌 Статус: {status_icon} {status}\n"
        "📅 Создана: {date}\n"
        "{buyer_line}"
        "━━━━━━━━━━━━━━━━"
    ),
    "btn_deal_detail": "🔎 Детали",
    "seller_reminder": (
        "⏰ *Напоминание!*\n\n"
        "Покупатель оплатил сделку `{id}`, но вы ещё не отправили NFT.\n\n"
        "🎁 {gift} | 💰 {amount} {cur}\n\n"
        "Пожалуйста, передайте подарок или откройте поддержку: @{support}"
    ),
}

T["uk"] = {
    "welcome": "💎 *OTC NFT Market*\n\nЛаскаво просимо на *найбезпечніший* майданчик для торгівлі NFT подарунками у Telegram!\n\n━━━━━━━━━━━━━━━━\n🔐 *Ескроу-захист* кожної угоди\n⚡️ Підтвердження транзакцій у реальному часі\n🛡️ Верифікація продавців та покупців\n🌍 Підтримка 6 валют\n💬 Підтримка 24/7\n━━━━━━━━━━━━━━━━\n\nОберіть мову:",
    "blocked": "⛔ Ваш акаунт заблоковано. Зверніться до підтримки: @{support}",
    "menu": "🏠 *OTC NFT Market*\n\n👤 {name}\n⭐ Рейтинг: *{rating}* | 📊 Угод: *{dc}*\n\nОберіть дію:",
    "btn_create": "➕ Створити угоду", "btn_deals": "📂 Мої угоди", "btn_refs": "👥 Реферали",
    "btn_req": "💳 Реквізити", "btn_lang": "🌐 Мова", "btn_support": "💬 Підтримка", "btn_about": "ℹ️ Про маркет",
    "no_req": "⚠️ *Реквізити не прив'язані*\n\nДля створення угоди необхідно спочатку прив'язати платіжні реквізити.\n\n👇 Перейдіть у розділ *Реквізити*",
    "req_menu": "💳 *Реквізити*\n\nОберіть валюту для прив'язки.\n✅ — вже прив'язано:",
    "req_enter": "✏️ *Прив'язка реквізитів — {cur}*\n\nВведіть ваші платіжні дані:\n\n• Для карт: номер картки\n• Для USDT: адреса TRC20/ERC20\n• Для Stars: username у Telegram",
    "req_saved": "✅ *Реквізити збережено!*\n\nВалюта: *{cur}*\n\nТепер можна створювати угоди.",
    "deal_cur": "💱 *Створення угоди — Крок 1/3*\n\nОберіть валюту розрахунку:",
    "deal_amount": "💰 *Створення угоди — Крок 2/3*\n\nВведіть суму угоди у *{cur}*:",
    "deal_gift": "🎁 *Створення угоди — Крок 3/3*\n\nВведіть назву NFT подарунка:",
    "bad_amount": "❌ Невірний формат суми. Введіть число.",
    "deal_created": "✅ *Угода успішно створена!*\n\n━━━━━━━━━━━━━━━━\n🎁 NFT подарунок: *{gift}*\n💰 Сума: *{amount} {cur}*\n🆔 ID: `{id}`\n📅 Створено: {date}\n📌 Статус: 🟡 Очікує покупця\n💸 Комісія маркету: 3%\n━━━━━━━━━━━━━━━━\n\n🔗 *Посилання для покупця:*\n`https://t.me/{bot}?start=deal_{id}`\n\n📤 Надішліть це посилання покупцю.",
    "no_deals": "📭 У вас поки немає угод.\n\nСтворіть першу угоду!",
    "deals_list": "📂 *Ваші угоди:*\n\n{list}",
    "deal_row": "{icon} `{id}` — 🎁 *{gift}* | 💰 {amount} {cur}\n",
    "deal_cancel_confirm": "🗑 *Скасувати угоду?*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\n⚠️ Можна скасувати лише якщо покупець ще не оплатив.",
    "deal_cancelled": "✅ Угоду `{id}` скасовано.",
    "deal_cancel_fail": "❌ Не можна скасувати — покупець вже оплатив.\nЗверніться до підтримки: @{support}",
    "refs": "👥 *Реферальна програма*\n\n🔗 *Ваше посилання:*\n`https://t.me/{bot}?start=ref_{uid}`\n\n━━━━━━━━━━━━━━━━\n👤 Запрошено: *{count}* чол.\n💎 Зароблено: *{bonus}* USDT\n━━━━━━━━━━━━━━━━",
    "support": "💬 *Служба підтримки OTC NFT Market*\n\n📩 Менеджер: @{support}\n⏱ Час відповіді: до 15 хвилин\n\nАбо напишіть повідомлення тут:",
    "support_sent": "✅ *Повідомлення надіслано!*\n\nМенеджер @{support} відповість протягом 15 хвилин. 🙏",
    "about": "ℹ️ *OTC NFT Market*\n\n💎 Найнадійніший спосіб торгувати NFT подарунками у Telegram\n\n🔐 *Безпека:*\n• Ескроу-захист\n• Верифікація\n• Рейтингова система\n• Арбітраж спорів\n\n💬 Підтримка: @{support}",
    "lang_pick": "🌐 *Оберіть мову інтерфейсу:*",
    "back": "⬅️ Назад",
    "s_active": "🟡 Очікує", "s_paid": "🟠 Оплачено", "s_done": "✅ Завершено", "s_cancelled": "❌ Скасовано",
    "buyer_welcome": "👋 *Ласкаво просимо до OTC NFT Market!*\n\nВас запросили до захищеної угоди.\n\n🔐 Всі транзакції захищені системою ескроу.\n\nОберіть мову:",
    "buyer_viewing": "👁 *Покупець переглядає вашу угоду*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\nОчікуйте оплати...",
    "buyer_deal": "🤝 *Пропозиція угоди*\n\n━━━━━━━━━━━━━━━━\n🎁 NFT подарунок: *{gift}*\n💰 Сума до оплати: *{amount} {cur}*\n👤 Продавець: *{seller}*\n⭐ Рейтинг: *{rating}*\n📊 Угод: *{dc}*\n🆔 ID: `{id}`\n━━━━━━━━━━━━━━━━\n\n🔐 Ваші кошти будуть захищені ескроу до передачі NFT.",
    "btn_pay": "💳 Перейти до оплати", "btn_cancel_deal": "❌ Скасувати", "btn_dispute": "⚖️ Відкрити спір",
    "buyer_pay_info": "💳 *Реквізити для оплати*\n\n━━━━━━━━━━━━━━━━\n🎁 Подарунок: *{gift}*\n💰 Сума: *{amount} {cur}*\n📋 Реквізити:\n`{req}`\n━━━━━━━━━━━━━━━━\n\n⚠️ Переведіть *точну* суму та збережіть чек.\n\n👇 Після оплати натисніть:",
    "btn_confirm_pay": "✅ Я оплатив — Підтвердити",
    "buyer_paid": "⏳ *Оплату отримано!*\n\n💰 Сума: *{amount} {cur}*\n\n✅ Продавець отримав сповіщення.\n\n⚠️ Якщо продавець не відповідає — @{support}",
    "seller_notif": "🔔 *НОВА ОПЛАТА ПО УГОДІ!*\n\n━━━━━━━━━━━━━━━━\n🎁 Подарунок: *{gift}*\n💰 Сума: *{amount} {cur}*\n👤 Покупець: *{buyer}*\n🆔 ID: `{id}`\n━━━━━━━━━━━━━━━━\n\n✅ Покупець підтвердив оплату.\nПередайте NFT подарунок!",
    "btn_nft_sent": "✅ NFT подарунок передано",
    "deal_done_seller": "🎉 *Угода завершена!*\n\n✅ NFT передано покупцю\n💰 Кошти розблоковано\n\nДякуємо за використання OTC NFT Market! 💎",
    "deal_done_buyer": "🎉 *NFT отримано!*\n\n✅ Угода завершена\n\nОцініть продавця:",
    "review_prompt": "⭐ *Оцініть продавця*\n\nОберіть оцінку від 1 до 5:",
    "review_thanks": "✅ Дякуємо за відгук!\n\nВашу оцінку враховано.",
    "dispute_opened": "⚖️ *Спір відкрито*\n\n🆔 `{id}`\n\nНаш спеціаліст @{support} зв'яжеться з вами протягом 30 хвилин.",
    "dispute_notif": "⚖️ *ВІДКРИТО СПІР ПО УГОДІ!*\n\n🆔 `{id}`\n👤 Покупець: {buyer}\n\nЗверніться до покупця або @{support}",
    "deal_not_found": "❌ *Угода не знайдена*\n\nПо питаннях: @{support}",
    "admin_granted": "🔐 *Права адміністратора активовано*\n\nВикористовуйте кнопки нижче:",
    "fee_choice": "💸 *Хто покриває комісію маркету (3%)?*\n\n━━━━━━━━━━━━━━━━\n💰 Базова сума: *{amount} {cur}*\n━━━━━━━━━━━━━━━━\n\n• *Покупець платить комісію* — ви отримуєте {amount} {cur}, покупець платить {amount_with_fee} {cur}\n• *Продавець покриває комісію* — покупець платить {amount} {cur}, ви отримуєте {amount_after_fee} {cur}\n\nОберіть:",
    "btn_fee_buyer": "👤 Покупець платить комісію (+3%)",
    "btn_fee_seller": "🏪 Я покриваю комісію (-3%)",
    "min_amount": "❌ Мінімальна сума угоди: *{min} {cur}*\n\nВведіть більшу суму:",
    "search_deal_prompt": "🔍 *Пошук угоди за ID*\n\nВведіть ID угоди:",
    "search_deal_found": "🔍 *Результати пошуку:*\n\n{result}",
    "search_deal_none": "❌ Угоду з таким ID не знайдено.",
    "btn_search": "🔍 Знайти угоду",
    "seller_stats": "📊 *Статистика продавця*\n\n━━━━━━━━━━━━━━━━\n📋 Усього угод: *{total}*\n✅ Завершено: *{done}*\n🟡 Активних: *{active}*\n❌ Скасовано: *{cancelled}*\n━━━━━━━━━━━━━━━━\n💰 *Оборот:*\n{turnover}━━━━━━━━━━━━━━━━\n💵 Середній чек: *{avg_deal}*\n⭐ Рейтинг: *{rating}* / 5.0\n━━━━━━━━━━━━━━━━",
    "btn_stats": "📊 Статистика",
    "buyer_left": "👤 *Покупець покинув угоду*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\nУгода знову доступна.",
    "deal_detail": "📋 *Деталі угоди*\n\n━━━━━━━━━━━━━━━━\n🆔 ID: `{id}`\n🎁 Подарунок: *{gift}*\n💰 Сума: *{amount} {cur}*\n📌 Статус: {status_icon} {status}\n📅 Створено: {date}\n{buyer_line}━━━━━━━━━━━━━━━━",
    "btn_deal_detail": "🔎 Деталі",
    "seller_reminder": "⏰ *Нагадування!*\n\nПокупець оплатив угоду `{id}`, але ви ще не відправили NFT.\n\n🎁 {gift} | 💰 {amount} {cur}\n\nПередайте подарунок або зверніться до підтримки: @{support}",
}

T["en"] = {
    "welcome": "💎 *OTC NFT Market*\n\nWelcome to the *safest platform* for trading NFT gifts in Telegram!\n\n━━━━━━━━━━━━━━━━\n🔐 *Escrow protection* for every deal\n⚡️ Real-time transaction confirmation\n🛡️ Seller & buyer verification\n🌍 6 currencies supported\n💬 24/7 support\n━━━━━━━━━━━━━━━━\n\nChoose your language:",
    "blocked": "⛔ Your account is blocked. Contact support: @{support}",
    "menu": "🏠 *OTC NFT Market*\n\n👤 {name}\n⭐ Rating: *{rating}* | 📊 Deals: *{dc}*\n\nChoose an action:",
    "btn_create": "➕ Create Deal", "btn_deals": "📂 My Deals", "btn_refs": "👥 Referrals",
    "btn_req": "💳 Requisites", "btn_lang": "🌐 Language", "btn_support": "💬 Support", "btn_about": "ℹ️ About",
    "no_req": "⚠️ *Requisites not linked*\n\nTo create a deal you need to link your payment requisites first.\n\n👇 Go to *Requisites* section",
    "req_menu": "💳 *Requisites*\n\nChoose currency to link.\n✅ — already linked:",
    "req_enter": "✏️ *Link requisites — {cur}*\n\nEnter your payment details:\n\n• For cards: card number\n• For USDT: TRC20/ERC20 address\n• For Stars: Telegram username",
    "req_saved": "✅ *Requisites saved!*\n\nCurrency: *{cur}*\n\nYou can now create deals in this currency.",
    "deal_cur": "💱 *Create Deal — Step 1/3*\n\nChoose payment currency:",
    "deal_amount": "💰 *Create Deal — Step 2/3*\n\nEnter deal amount in *{cur}*:",
    "deal_gift": "🎁 *Create Deal — Step 3/3*\n\nEnter NFT gift name:",
    "bad_amount": "❌ Invalid amount format. Enter a number.",
    "deal_created": "✅ *Deal created successfully!*\n\n━━━━━━━━━━━━━━━━\n🎁 NFT Gift: *{gift}*\n💰 Amount: *{amount} {cur}*\n🆔 Deal ID: `{id}`\n📅 Created: {date}\n📌 Status: 🟡 Awaiting buyer\n💸 Market fee: 3%\n━━━━━━━━━━━━━━━━\n\n🔗 *Buyer link:*\n`https://t.me/{bot}?start=deal_{id}`\n\n📤 Send this link to the buyer.",
    "no_deals": "📭 You have no deals yet.\n\nCreate your first deal!",
    "deals_list": "📂 *Your Deals:*\n\n{list}",
    "deal_row": "{icon} `{id}` — 🎁 *{gift}* | 💰 {amount} {cur}\n",
    "deal_cancel_confirm": "🗑 *Cancel deal?*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\n⚠️ Can only cancel if buyer hasn't paid yet.",
    "deal_cancelled": "✅ Deal `{id}` cancelled.",
    "deal_cancel_fail": "❌ Cannot cancel — buyer already paid.\nContact support: @{support}",
    "refs": "👥 *Referral Program*\n\n🔗 *Your link:*\n`https://t.me/{bot}?start=ref_{uid}`\n\n━━━━━━━━━━━━━━━━\n👤 Invited: *{count}* users\n💎 Earned: *{bonus}* USDT\n━━━━━━━━━━━━━━━━",
    "support": "💬 *OTC NFT Market Support*\n\n📩 Manager: @{support}\n⏱ Response time: up to 15 minutes\n\nOr leave a message here:",
    "support_sent": "✅ *Message sent!*\n\n@{support} will reply within 15 minutes. 🙏",
    "about": "ℹ️ *OTC NFT Market*\n\n💎 The most reliable way to buy and sell NFT gifts in Telegram\n\n🔐 *Security:*\n• Escrow protection\n• User verification\n• Rating system\n• Dispute arbitration\n\n💬 Support: @{support}",
    "lang_pick": "🌐 *Choose interface language:*",
    "back": "⬅️ Back",
    "s_active": "🟡 Pending", "s_paid": "🟠 Paid", "s_done": "✅ Done", "s_cancelled": "❌ Cancelled",
    "buyer_welcome": "👋 *Welcome to OTC NFT Market!*\n\nYou've been invited to a secured deal.\n\n🔐 All transactions are protected by escrow.\n\nChoose language:",
    "buyer_viewing": "👁 *A buyer is viewing your deal*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\nAwaiting payment...",
    "buyer_deal": "🤝 *Deal Offer*\n\n━━━━━━━━━━━━━━━━\n🎁 NFT Gift: *{gift}*\n💰 Amount: *{amount} {cur}*\n👤 Seller: *{seller}*\n⭐ Rating: *{rating}*\n📊 Deals: *{dc}*\n🆔 ID: `{id}`\n━━━━━━━━━━━━━━━━\n\n🔐 Funds held in escrow until NFT is transferred.",
    "btn_pay": "💳 Proceed to Payment", "btn_cancel_deal": "❌ Cancel", "btn_dispute": "⚖️ Open Dispute",
    "buyer_pay_info": "💳 *Payment Details*\n\n━━━━━━━━━━━━━━━━\n🎁 Gift: *{gift}*\n💰 Amount: *{amount} {cur}*\n📋 Requisites:\n`{req}`\n━━━━━━━━━━━━━━━━\n\n⚠️ Transfer *exact* amount and save your receipt.\n\n👇 After payment click:",
    "btn_confirm_pay": "✅ I've paid — Confirm",
    "buyer_paid": "⏳ *Payment received!*\n\n💰 Amount: *{amount} {cur}*\n\n✅ Seller notified.\n\n⚠️ If seller doesn't respond — @{support}",
    "seller_notif": "🔔 *NEW PAYMENT ON YOUR DEAL!*\n\n━━━━━━━━━━━━━━━━\n🎁 Gift: *{gift}*\n💰 Amount: *{amount} {cur}*\n👤 Buyer: *{buyer}*\n🆔 ID: `{id}`\n━━━━━━━━━━━━━━━━\n\n✅ Buyer confirmed payment.\nTransfer the NFT gift!",
    "btn_nft_sent": "✅ NFT Gift Transferred",
    "deal_done_seller": "🎉 *Deal completed!*\n\n✅ NFT transferred to buyer\n💰 Funds unlocked\n\nThank you for using OTC NFT Market! 💎",
    "deal_done_buyer": "🎉 *NFT received!*\n\n✅ Deal completed\n\nPlease rate the seller:",
    "review_prompt": "⭐ *Rate the seller*\n\nChoose rating from 1 to 5:",
    "review_thanks": "✅ Thank you for your review!\n\nYour rating has been recorded.",
    "dispute_opened": "⚖️ *Dispute opened*\n\n🆔 `{id}`\n\nOur specialist @{support} will contact you within 30 minutes.",
    "dispute_notif": "⚖️ *DISPUTE OPENED ON DEAL!*\n\n🆔 `{id}`\n👤 Buyer: {buyer}\n\nContact buyer or @{support}",
    "deal_not_found": "❌ *Deal not found*\n\nContact support: @{support}",
    "admin_granted": "🔐 *Admin rights activated*\n\nUse the buttons below:",
    "fee_choice": "💸 *Who covers the market fee (3%)?*\n\n━━━━━━━━━━━━━━━━\n💰 Base amount: *{amount} {cur}*\n━━━━━━━━━━━━━━━━\n\n• *Buyer pays the fee* — you receive {amount} {cur}, buyer pays {amount_with_fee} {cur}\n• *Seller covers the fee* — buyer pays {amount} {cur}, you receive {amount_after_fee} {cur}\n\nChoose:",
    "btn_fee_buyer": "👤 Buyer pays fee (+3%)",
    "btn_fee_seller": "🏪 I cover the fee (-3%)",
    "min_amount": "❌ Minimum deal amount: *{min} {cur}*\n\nEnter a larger amount:",
    "search_deal_prompt": "🔍 *Search deal by ID*\n\nEnter the deal ID (or first characters):",
    "search_deal_found": "🔍 *Search results:*\n\n{result}",
    "search_deal_none": "❌ No deal found with that ID.",
    "btn_search": "🔍 Find Deal",
    "seller_stats": "📊 *Seller Statistics*\n\n━━━━━━━━━━━━━━━━\n📋 Total deals: *{total}*\n✅ Completed: *{done}*\n🟡 Active: *{active}*\n❌ Cancelled: *{cancelled}*\n━━━━━━━━━━━━━━━━\n💰 *Turnover:*\n{turnover}━━━━━━━━━━━━━━━━\n💵 Avg deal: *{avg_deal}*\n⭐ Rating: *{rating}* / 5.0\n━━━━━━━━━━━━━━━━",
    "btn_stats": "📊 Statistics",
    "buyer_left": "👤 *Buyer left the deal*\n\n🆔 `{id}`\n🎁 {gift} | 💰 {amount} {cur}\n\nDeal is available again.",
    "deal_detail": "📋 *Deal Details*\n\n━━━━━━━━━━━━━━━━\n🆔 ID: `{id}`\n🎁 Gift: *{gift}*\n💰 Amount: *{amount} {cur}*\n📌 Status: {status_icon} {status}\n📅 Created: {date}\n{buyer_line}━━━━━━━━━━━━━━━━",
    "btn_deal_detail": "🔎 Details",
    "seller_reminder": "⏰ *Reminder!*\n\nBuyer paid deal `{id}` but you haven't sent the NFT yet.\n\n🎁 {gift} | 💰 {amount} {cur}\n\nPlease transfer the gift or contact support: @{support}",
}

for code in ["ar", "zh", "ja"]:
    T[code] = T["en"].copy()

T["ar"]["welcome"] = "💎 *OTC NFT Market*\n\nمرحباً! أكثر منصة أمانًا لتداول هدايا NFT!\n\n🔐 حماية الضمان\n⚡️ تأكيد فوري\n💬 دعم 24/7\n\nاختر لغتك:"
T["zh"]["welcome"] = "💎 *OTC NFT Market*\n\n最安全的NFT礼品交易平台！\n\n🔐 托管保护\n⚡️ 实时确认\n💬 24/7支持\n\n请选择语言:"
T["ja"]["welcome"] = "💎 *OTC NFT Market*\n\n最も安全なNFTギフト取引プラットフォーム！\n\n🔐 エスクロー保護\n⚡️ リアルタイム確認\n💬 24時間サポート\n\n言語を選択してください:"


# ══════════════════════════════════════════════════
#                    HELPERS
# ══════════════════════════════════════════════════

def get_user(uid):
    if uid not in users:
        users[uid] = {
            "lang": "en", "req": {}, "deals": [],
            "refs": 0, "rating": 5.0, "rating_count": 0,
            "deals_count": 0, "balance": {},
        }
    return users[uid]

def ulang(ctx):
    return ctx.user_data.get("lang", "en")

def tr(ctx, key, **kw):
    l = ulang(ctx)
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
    rows = []
    items = list(LANGS.items())
    for i in range(0, len(items), 2):
        row = [InlineKeyboardButton(items[i][1], callback_data=f"lang_{items[i][0]}")]
        if i + 1 < len(items):
            row.append(InlineKeyboardButton(items[i+1][1], callback_data=f"lang_{items[i+1][0]}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def menu_kb(ctx):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(tr(ctx,"btn_create"), callback_data="create"),
         InlineKeyboardButton(tr(ctx,"btn_deals"), callback_data="mydeals")],
        [InlineKeyboardButton(tr(ctx,"btn_refs"), callback_data="refs"),
         InlineKeyboardButton(tr(ctx,"btn_req"), callback_data="req")],
        [InlineKeyboardButton(tr(ctx,"btn_lang"), callback_data="changelang"),
         InlineKeyboardButton(tr(ctx,"btn_support"), callback_data="support")],
        [InlineKeyboardButton(tr(ctx,"btn_stats"), callback_data="seller_stats"),
         InlineKeyboardButton(tr(ctx,"btn_about"), callback_data="about")],
    ])

def back_kb(ctx, cb="menu"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(tr(ctx,"back"), callback_data=cb)]])

def status_icon(status):
    return {"active":"🟡","paid":"🟠","done":"✅","cancelled":"❌"}.get(status,"❓")

def now_str():
    return datetime.now().strftime("%d.%m.%Y %H:%M")


# ══════════════════════════════════════════════════
#                  ADMIN PANEL
# ══════════════════════════════════════════════════

def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить сделку", callback_data="adm_pay"),
         InlineKeyboardButton("⭐ Рейтинг", callback_data="adm_rating")],
        [InlineKeyboardButton("📊 Кол-во сделок", callback_data="adm_dc"),
         InlineKeyboardButton("💰 Баланс", callback_data="adm_bal")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="adm_users"),
         InlineKeyboardButton("📋 Все сделки", callback_data="adm_alldeals")],
        [InlineKeyboardButton("🚫 Блокировка", callback_data="adm_block"),
         InlineKeyboardButton("📊 Статистика", callback_data="adm_stats")],
        [InlineKeyboardButton("❌ Закрыть панель", callback_data="adm_close")],
    ])

async def otcteam_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["is_admin"] = True
    await update.message.reply_text(
        tr_raw("ru", "admin_granted"),
        reply_markup=admin_kb(),
        parse_mode="Markdown"
    )

async def adm_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    back_adm = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В панель", callback_data="adm_back")]])

    if d == "adm_stats":
        total_deals = len(deals)
        active = sum(1 for dl in deals.values() if dl["status"] == "active")
        paid = sum(1 for dl in deals.values() if dl["status"] == "paid")
        done = sum(1 for dl in deals.values() if dl["status"] == "done")
        cancelled = sum(1 for dl in deals.values() if dl["status"] == "cancelled")
        total_users = len(users)
        blocked_count = len(blocked_users)
        await q.edit_message_text(
            f"📊 *Статистика OTC NFT Market*\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👥 Пользователей: *{total_users}*\n"
            f"🚫 Заблокировано: *{blocked_count}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📋 Всего сделок: *{total_deals}*\n"
            f"🟡 Ожидают: *{active}*\n"
            f"🟠 Оплачено: *{paid}*\n"
            f"✅ Завершено: *{done}*\n"
            f"❌ Отменено: *{cancelled}*\n"
            f"━━━━━━━━━━━━━━━━",
            reply_markup=back_adm, parse_mode="Markdown"
        )

    elif d == "adm_pay":
        active_deals = [(did, dl) for did, dl in deals.items() if dl["status"] in ("active","paid")]
        if not active_deals:
            await q.edit_message_text("📭 Нет активных сделок.", reply_markup=back_adm)
            return
        kb = []
        for did, dl in active_deals[:15]:
            icon = status_icon(dl["status"])
            kb.append([InlineKeyboardButton(
                f"{icon} #{did[:8]} — {dl['gift']} | {dl['amount']} {dl['currency']}",
                callback_data=f"adm_dopay_{did}"
            )])
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")])
        await q.edit_message_text("💳 *Выберите сделку для завершения:*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif d.startswith("adm_dopay_"):
        did = d[10:]
        deal = deals.get(did)
        if deal:
            deal["status"] = "done"
            u = get_user(deal["seller_id"])
            u["deals_count"] = u.get("deals_count", 0) + 1
            try:
                sl = u.get("lang", "ru")
                await ctx.bot.send_message(chat_id=deal["seller_id"], text=tr_raw(sl, "deal_done_seller"), parse_mode="Markdown")
            except Exception:
                pass
            if deal.get("buyer_id"):
                try:
                    bl = get_user(deal["buyer_id"]).get("lang", "ru")
                    await ctx.bot.send_message(
                        chat_id=deal["buyer_id"],
                        text=tr_raw(bl, "deal_done_buyer"),
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⭐1", callback_data=f"rev_1_{deal['seller_id']}"),
                            InlineKeyboardButton("⭐2", callback_data=f"rev_2_{deal['seller_id']}"),
                            InlineKeyboardButton("⭐3", callback_data=f"rev_3_{deal['seller_id']}"),
                            InlineKeyboardButton("⭐4", callback_data=f"rev_4_{deal['seller_id']}"),
                            InlineKeyboardButton("⭐5", callback_data=f"rev_5_{deal['seller_id']}"),
                        ]]),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
            await q.edit_message_text(
                f"✅ *Сделка завершена!*\n\n🆔 `{did[:8]}`\n🎁 {deal['gift']}\n💰 {deal['amount']} {deal['currency']}\n\nУведомления отправлены.",
                reply_markup=back_adm, parse_mode="Markdown"
            )
        else:
            await q.edit_message_text("❌ Сделка не найдена.", reply_markup=back_adm)

    elif d == "adm_block":
        ctx.user_data["adm_action"] = "block"
        await q.edit_message_text(
            "🚫 *Блокировка / разблокировка*\n\nВведите ID пользователя:\n`123456789`\n\nЕсли заблокирован — разблокирует.\nЕсли нет — заблокирует.",
            reply_markup=back_adm, parse_mode="Markdown"
        )

    elif d == "adm_rating":
        ctx.user_data["adm_action"] = "rating"
        await q.edit_message_text("⭐ *Изменить рейтинг*\n\nФормат: `ID значение`\nПример: `123456789 4.9`", reply_markup=back_adm, parse_mode="Markdown")

    elif d == "adm_dc":
        ctx.user_data["adm_action"] = "deals_count"
        await q.edit_message_text("📊 *Изменить количество сделок*\n\nФормат: `ID количество`\nПример: `123456789 250`", reply_markup=back_adm, parse_mode="Markdown")

    elif d == "adm_bal":
        ctx.user_data["adm_action"] = "balance"
        curs = " | ".join(CURRENCIES.keys())
        await q.edit_message_text(f"💰 *Изменить баланс*\n\nФормат: `ID ВАЛЮТА сумма`\nВалюты: `{curs}`\nПример: `123456789 USDT 1000`", reply_markup=back_adm, parse_mode="Markdown")

    elif d == "adm_users":
        if not users:
            await q.edit_message_text("📭 Нет пользователей.", reply_markup=back_adm)
            return
        txt = "👥 *Пользователи:*\n\n"
        for uid, u in list(users.items())[:20]:
            block_mark = "🚫 " if uid in blocked_users else ""
            bal = " | ".join(f"{v} {k}" for k,v in u.get("balance",{}).items()) or "—"
            txt += f"{block_mark}👤 `{uid}`\n⭐ {u.get('rating',5.0)} | 📊 {u.get('deals_count',0)} | 💰 {bal}\n\n"
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
        await q.edit_message_text(tr_raw("ru", "admin_granted"), reply_markup=admin_kb(), parse_mode="Markdown")

    elif d == "adm_close":
        ctx.user_data.pop("is_admin", None)
        await q.edit_message_text("✅ Панель закрыта.")

async def adm_input_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    action = ctx.user_data.get("adm_action")
    text = update.message.text.strip()
    back_adm = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В панель", callback_data="adm_back")]])

    try:
        parts = text.split()
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
                await update.message.reply_text(f"❌ Неизвестная валюта.", reply_markup=back_adm)
                return ADMIN_ST
            val = float(parts[2])
            get_user(target).setdefault("balance", {})[cur] = val
            await update.message.reply_text(f"✅ Баланс `{target}`: {cur} → *{val}*", parse_mode="Markdown", reply_markup=back_adm)

    except Exception:
        await update.message.reply_text("❌ Ошибка формата.", reply_markup=back_adm)

    ctx.user_data.pop("adm_action", None)
    return ADMIN_ST


# ══════════════════════════════════════════════════
#                  MAIN HANDLERS
# ══════════════════════════════════════════════════

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid in blocked_users:
        await update.message.reply_text(tr_raw(ctx.user_data.get("lang", "ru"), "blocked"), parse_mode="Markdown")
        return MENU_ST

    args = ctx.args or []

    if args and args[0].startswith("ref_"):
        try:
            ref = int(args[0][4:])
            if ref != uid:
                get_user(ref)["refs"] = get_user(ref).get("refs", 0) + 1
        except Exception:
            pass

    if args and args[0].startswith("deal_"):
        did = args[0][5:]
        deal = deals.get(did)
        if not deal or deal["status"] in ("done", "cancelled", "paid"):
            await update.message.reply_text(tr_raw("en", "deal_not_found"), parse_mode="Markdown")
            return LANG_ST
        ctx.user_data["pending_deal"] = did
        ctx.user_data["flow"] = "buyer"
        await update.message.reply_text(T["en"]["buyer_welcome"], reply_markup=lang_kb(), parse_mode="Markdown")
        return LANG_ST

    ctx.user_data["flow"] = "seller"
    await update.message.reply_text(T["en"]["welcome"], reply_markup=lang_kb(), parse_mode="Markdown")
    return LANG_ST


async def main_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    uid = update.effective_user.id
    name = update.effective_user.first_name or "User"
    u = get_user(uid)

    if uid in blocked_users and not d.startswith("adm_"):
        await q.edit_message_text(tr_raw(ctx.user_data.get("lang", "ru"), "blocked"), parse_mode="Markdown")
        return MENU_ST

    # Admin
    if d.startswith("adm_"):
        return await adm_cb(update, ctx)

    # Review
    if d.startswith("rev_"):
        parts = d.split("_")
        stars = int(parts[1])
        seller_id = int(parts[2])
        su = get_user(seller_id)
        rc = su.get("rating_count", 0)
        old_rating = su.get("rating", 5.0)
        su["rating"] = round((old_rating * rc + stars) / (rc + 1), 1)
        su["rating_count"] = rc + 1
        await q.edit_message_text(tr(ctx, "review_thanks"), parse_mode="Markdown")
        return MENU_ST

    # Lang selection
    if d.startswith("lang_"):
        code = d[5:]
        ctx.user_data["lang"] = code
        u["lang"] = code

        if ctx.user_data.get("flow") == "buyer":
            did = ctx.user_data.get("pending_deal")
            deal = deals.get(did)
            if not deal or deal["status"] in ("done","cancelled","paid"):
                await q.edit_message_text(tr(ctx, "deal_not_found"), parse_mode="Markdown")
                return MENU_ST
            su = get_user(deal["seller_id"])
            # Calculate buyer-facing amount based on fee mode
            buyer_amount = deal["amount"]
            if deal.get("fee_mode") == "buyer":
                buyer_amount = round(deal["amount"] * 1.03, 2)
            await q.edit_message_text(
                tr(ctx, "buyer_deal",
                   gift=deal["gift"], amount=buyer_amount,
                   cur=CURRENCIES.get(deal["currency"], deal["currency"]),
                   seller=deal["seller_name"],
                   rating=su.get("rating", 5.0),
                   dc=su.get("deals_count", 0),
                   id=did[:8]),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tr(ctx,"btn_pay"), callback_data=f"pay_{did}")],
                    [InlineKeyboardButton(tr(ctx,"btn_cancel_deal"), callback_data="buyer_cancel")],
                ]),
                parse_mode="Markdown"
            )
            # Notify seller that buyer opened the deal
            try:
                sl = su.get("lang", "ru")
                await ctx.bot.send_message(
                    chat_id=deal["seller_id"],
                    text=tr_raw(sl, "buyer_viewing",
                                id=did[:8], gift=deal["gift"],
                                amount=deal["amount"],
                                cur=CURRENCIES.get(deal["currency"], deal["currency"])),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
            return BUYER_ST

        await q.edit_message_text(
            tr(ctx, "menu", name=name, rating=u.get("rating",5.0), dc=u.get("deals_count",0)),
            reply_markup=menu_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    if d == "menu":
        ctx.user_data["flow"] = "seller"
        ctx.user_data.pop("await", None)
        await q.edit_message_text(
            tr(ctx, "menu", name=name, rating=u.get("rating",5.0), dc=u.get("deals_count",0)),
            reply_markup=menu_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    if d == "create":
        if not u["req"]:
            await q.edit_message_text(
                tr(ctx, "no_req"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tr(ctx,"btn_req"), callback_data="req")],
                    [InlineKeyboardButton(tr(ctx,"back"), callback_data="menu")],
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
        ctx.user_data["dcur"] = cur
        ctx.user_data["await"] = "amount"
        await q.edit_message_text(
            tr(ctx, "deal_amount", cur=CURRENCIES.get(cur,cur)),
            reply_markup=back_kb(ctx, "create"), parse_mode="Markdown"
        )
        return DEAL_AMT_ST

    # Fee choice callbacks (after amount entered)
    if d in ("fee_buyer", "fee_seller"):
        amount = ctx.user_data.get("damount")
        cur = ctx.user_data.get("dcur")
        if not amount or not cur:
            await q.edit_message_text(tr(ctx, "menu", name=name, rating=u.get("rating",5.0), dc=u.get("deals_count",0)), reply_markup=menu_kb(ctx), parse_mode="Markdown")
            return MENU_ST
        fee_pct = 0.03
        if d == "fee_buyer":
            # Buyer pays extra: seller receives full amount
            ctx.user_data["dfee_mode"] = "buyer"
            ctx.user_data["dfee_pct"] = fee_pct
        else:
            # Seller absorbs fee: seller receives amount*(1-fee)
            ctx.user_data["dfee_mode"] = "seller"
            ctx.user_data["dfee_pct"] = fee_pct
        ctx.user_data["await"] = "gift"
        await q.edit_message_text(
            tr(ctx, "deal_gift"),
            reply_markup=back_kb(ctx, "create"), parse_mode="Markdown"
        )
        return DEAL_GIFT_ST

    # Seller stats
    if d == "seller_stats":
        my_deals = [deals[did] for did in u.get("deals", []) if did in deals]
        total = len(my_deals)
        done_count = sum(1 for dl in my_deals if dl["status"] == "done")
        active_count = sum(1 for dl in my_deals if dl["status"] == "active")
        cancelled_count = sum(1 for dl in my_deals if dl["status"] == "cancelled")
        # Turnover per currency
        turnover_map = {}
        for dl in my_deals:
            if dl["status"] == "done":
                c = dl["currency"]
                turnover_map[c] = turnover_map.get(c, 0) + dl["amount"]
        turnover_str = ""
        for c, v in turnover_map.items():
            turnover_str += f"  • {round(v,2)} {c}\n"
        if not turnover_str:
            turnover_str = "  • —\n"
        done_deals = [dl for dl in my_deals if dl["status"] == "done"]
        avg = round(sum(dl["amount"] for dl in done_deals) / len(done_deals), 2) if done_deals else 0
        avg_deal_str = f"{avg}" if avg else "—"
        await q.edit_message_text(
            tr(ctx, "seller_stats", total=total, done=done_count, active=active_count,
               cancelled=cancelled_count, turnover=turnover_str,
               avg_deal=avg_deal_str, rating=u.get("rating", 5.0)),
            reply_markup=back_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    # Deal detail
    if d.startswith("detail_"):
        did = d[7:]
        deal = deals.get(did)
        if not deal:
            await q.answer("❌ Не найдена", show_alert=True)
            return MENU_ST
        status_names = {"active": "Ожидает", "paid": "Оплачено", "done": "Завершена", "cancelled": "Отменена"}
        buyer_line = f"👤 Покупатель: *{deal['buyer_name']}*\n" if deal.get("buyer_name") else ""
        await q.edit_message_text(
            tr(ctx, "deal_detail", id=did[:8], gift=deal["gift"],
               amount=deal["amount"], cur=CURRENCIES.get(deal["currency"], deal["currency"]),
               status_icon=status_icon(deal["status"]),
               status=status_names.get(deal["status"], deal["status"]),
               date=deal.get("created", "—"),
               buyer_line=buyer_line),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(tr(ctx,"back"), callback_data="mydeals")]
            ]),
            parse_mode="Markdown"
        )
        return MENU_ST

    # Search deal
    if d == "search_deal":
        ctx.user_data["await"] = "search_deal"
        await q.edit_message_text(
            tr(ctx, "search_deal_prompt"),
            reply_markup=back_kb(ctx, "mydeals"), parse_mode="Markdown"
        )
        return MENU_ST

    if d == "mydeals":
        rating = u.get("rating", 5.0)
        dc = u.get("deals_count", 0)
        bal_lines = "\n".join(f"  • {v} {k}" for k,v in u.get("balance",{}).items())
        bal_str = bal_lines or "  • —"
        header = f"👤 *Профиль*\n⭐ Рейтинг: *{rating}* из 5.0\n📊 Завершено сделок: *{dc}*\n💳 Баланс:\n{bal_str}\n\n"

        active_deals_kb = []
        detail_kb = []

        # Seller deals section
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
                            f"🗑 Отменить #{did[:8]}",
                            callback_data=f"cancel_deal_{did}"
                        )])
                    detail_kb.append([InlineKeyboardButton(
                        f"🔎 #{did[:8]} {dl['gift'][:15]}",
                        callback_data=f"detail_{did}"
                    )])
            seller_section = "📤 *Мои продажи:*\n" + rows
        else:
            seller_section = tr(ctx,"no_deals")

        # Buyer deals section
        buyer_section = ""
        buyer_deals = u.get("buyer_deals", [])
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
            + detail_kb[:5]  # Show up to 5 detail buttons
            + [[InlineKeyboardButton(tr(ctx,"btn_search"), callback_data="search_deal")]]
            + [[InlineKeyboardButton(tr(ctx,"back"), callback_data="menu")]]
        )
        await q.edit_message_text(
            header + seller_section + buyer_section,
            reply_markup=InlineKeyboardMarkup(kb_rows),
            parse_mode="Markdown"
        )
        return MENU_ST

    # Cancel deal by seller
    if d.startswith("cancel_deal_"):
        did = d[12:]
        deal = deals.get(did)
        if not deal:
            await q.answer("❌ Сделка не найдена", show_alert=True)
            return MENU_ST
        if deal["seller_id"] != uid:
            await q.answer("❌ Это не ваша сделка", show_alert=True)
            return MENU_ST
        await q.edit_message_text(
            tr(ctx, "deal_cancel_confirm", id=did[:8], gift=deal["gift"],
               amount=deal["amount"], cur=deal["currency"]),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да, отменить", callback_data=f"confirm_cancel_{did}"),
                 InlineKeyboardButton("❌ Нет", callback_data="mydeals")],
            ]),
            parse_mode="Markdown"
        )
        return MENU_ST

    if d.startswith("confirm_cancel_"):
        did = d[15:]
        deal = deals.get(did)
        if deal:
            if deal["status"] in ("paid", "done"):
                await q.edit_message_text(tr(ctx,"deal_cancel_fail"), reply_markup=back_kb(ctx,"mydeals"), parse_mode="Markdown")
            else:
                deal["status"] = "cancelled"
                await q.edit_message_text(tr(ctx,"deal_cancelled", id=did[:8]), reply_markup=back_kb(ctx,"mydeals"), parse_mode="Markdown")
        return MENU_ST

    if d == "refs":
        bot_info = await ctx.bot.get_me()
        await q.edit_message_text(
            tr(ctx,"refs", bot=bot_info.username, uid=uid,
               count=u.get("refs",0), bonus=round(u.get("refs",0)*0.5,2)),
            reply_markup=back_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

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
            ctx.user_data["await"] = "req"
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

    # Buyer: pay
    if d.startswith("pay_"):
        did = d[4:]
        deal = deals.get(did)
        if not deal or deal["status"] in ("done","cancelled"):
            await q.edit_message_text(tr(ctx,"deal_not_found"), parse_mode="Markdown")
            return MENU_ST
        # Anti-duplicate lock: if deal already locked by another buyer
        if deal.get("locked_by") and deal["locked_by"] != uid:
            await q.answer("⚠️ Сделка уже открыта другим покупателем. Попробуйте позже.", show_alert=True)
            return BUYER_ST
        # Lock the deal for this buyer
        deal["locked_by"] = uid
        req = get_user(deal["seller_id"])["req"].get(deal["currency"], "—")
        # Show amount depending on fee mode
        fee_mode = deal.get("fee_mode", "seller")
        display_amount = deal["amount"]
        if fee_mode == "buyer":
            display_amount = round(deal["amount"] * 1.03, 2)
        await q.edit_message_text(
            tr(ctx,"buyer_pay_info", gift=deal["gift"], amount=display_amount,
               cur=CURRENCIES.get(deal["currency"], deal["currency"]), req=req),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(tr(ctx,"btn_confirm_pay"), callback_data=f"confirmpay_{did}")],
                [InlineKeyboardButton(tr(ctx,"btn_dispute"), callback_data=f"dispute_{did}")],
                [InlineKeyboardButton(tr(ctx,"btn_cancel_deal"), callback_data=f"buyer_cancel_{did}")],
            ]),
            parse_mode="Markdown"
        )
        return BUYER_ST

    # Buyer: confirm payment
    if d.startswith("confirmpay_"):
        did = d[11:]
        deal = deals.get(did)
        if not deal:
            await q.edit_message_text(tr(ctx,"deal_not_found"), parse_mode="Markdown")
            return MENU_ST
        # Prevent seller from paying their own deal
        if deal["seller_id"] == uid:
            await q.answer("❌ Нельзя оплатить собственную сделку", show_alert=True)
            return BUYER_ST
        if deal["status"] == "paid":
            await q.answer("⚠️ Оплата уже подтверждена.", show_alert=True)
            return BUYER_ST
        deal["status"] = "paid"
        deal["buyer_id"] = uid
        deal["buyer_name"] = update.effective_user.full_name or "Buyer"
        # Track in buyer's deal list
        u.setdefault("buyer_deals", [])
        if did not in u["buyer_deals"]:
            u["buyer_deals"].append(did)
        # Determine display amount
        fee_mode = deal.get("fee_mode", "seller")
        display_amount = deal["amount"]
        if fee_mode == "buyer":
            display_amount = round(deal["amount"] * 1.03, 2)
        await q.edit_message_text(
            tr(ctx,"buyer_paid", amount=display_amount,
               cur=CURRENCIES.get(deal["currency"], deal["currency"])),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(tr(ctx,"btn_dispute"), callback_data=f"dispute_{did}")],
                [InlineKeyboardButton(tr(ctx,"btn_support"), callback_data="support")],
            ]),
            parse_mode="Markdown"
        )
        sl = get_user(deal["seller_id"]).get("lang","ru")
        try:
            await ctx.bot.send_message(
                chat_id=deal["seller_id"],
                text=tr_raw(sl,"seller_notif", gift=deal["gift"], amount=display_amount,
                            cur=CURRENCIES.get(deal["currency"],deal["currency"]),
                            buyer=deal["buyer_name"], id=did[:8]),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(tr_raw(sl,"btn_nft_sent"), callback_data=f"nftsent_{did}")
                ]]),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Seller notify error: {e}")
        # Schedule seller reminder after 15 minutes
        async def seller_reminder_job(context):
            deal_now = deals.get(did)
            if deal_now and deal_now["status"] == "paid":
                seller_lang = get_user(deal_now["seller_id"]).get("lang", "ru")
                try:
                    await context.bot.send_message(
                        chat_id=deal_now["seller_id"],
                        text=tr_raw(seller_lang, "seller_reminder",
                                    id=did[:8], gift=deal_now["gift"],
                                    amount=display_amount,
                                    cur=CURRENCIES.get(deal_now["currency"], deal_now["currency"])),
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(tr_raw(seller_lang, "btn_nft_sent"), callback_data=f"nftsent_{did}")
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

    # Buyer: open dispute
    if d.startswith("dispute_"):
        did = d[8:]
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

    if d == "buyer_cancel" or d.startswith("buyer_cancel_"):
        did = d[13:] if d.startswith("buyer_cancel_") else ctx.user_data.get("pending_deal")
        if did:
            deal = deals.get(did)
            if deal and deal.get("status") == "active":
                deal.pop("locked_by", None)  # Release lock
                # Notify seller
                sl = get_user(deal["seller_id"]).get("lang", "ru")
                try:
                    await ctx.bot.send_message(
                        chat_id=deal["seller_id"],
                        text=tr_raw(sl, "buyer_left", id=did[:8],
                                    gift=deal["gift"], amount=deal["amount"],
                                    cur=CURRENCIES.get(deal["currency"], deal["currency"])),
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

    # Seller: NFT sent
    if d.startswith("nftsent_"):
        did = d[8:]
        deal = deals.get(did)
        if not deal:
            await q.answer("❌ Сделка не найдена", show_alert=True)
            return MENU_ST
        # Security: only the actual seller can mark NFT as sent
        if deal["seller_id"] != uid:
            await q.answer("❌ Это не ваша сделка", show_alert=True)
            return MENU_ST
        if deal["status"] == "done":
            await q.answer("ℹ️ Сделка уже завершена", show_alert=True)
            return MENU_ST
        deal["status"] = "done"
        u2 = get_user(uid)
        u2["deals_count"] = u2.get("deals_count", 0) + 1
        await q.edit_message_text(tr(ctx,"deal_done_seller"), reply_markup=menu_kb(ctx), parse_mode="Markdown")
        if deal.get("buyer_id"):
            bl = get_user(deal["buyer_id"]).get("lang","ru")
            try:
                await ctx.bot.send_message(
                    chat_id=deal["buyer_id"],
                    text=tr_raw(bl,"deal_done_buyer"),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⭐1", callback_data=f"rev_1_{deal['seller_id']}"),
                        InlineKeyboardButton("⭐2", callback_data=f"rev_2_{deal['seller_id']}"),
                        InlineKeyboardButton("⭐3", callback_data=f"rev_3_{deal['seller_id']}"),
                        InlineKeyboardButton("⭐4", callback_data=f"rev_4_{deal['seller_id']}"),
                        InlineKeyboardButton("⭐5", callback_data=f"rev_5_{deal['seller_id']}"),
                    ]]),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Buyer notify error: {e}")
        return MENU_ST

    return MENU_ST


async def msg_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in blocked_users:
        await update.message.reply_text(tr_raw(ctx.user_data.get("lang", "ru"), "blocked"), parse_mode="Markdown")
        return MENU_ST

    text = update.message.text.strip()
    u = get_user(uid)
    aw = ctx.user_data.get("await")
    name = update.effective_user.first_name or "User"

    # Admin input
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
            # Minimum amount check (1 unit of any currency)
            MIN_AMOUNTS = {"UAH": 10, "RUB": 50, "KZT": 500, "CNY": 5, "USDT": 1, "STARS": 10}
            cur = ctx.user_data.get("dcur", "USDT")
            min_val = MIN_AMOUNTS.get(cur, 1)
            if amount < min_val:
                await update.message.reply_text(
                    tr(ctx, "min_amount", min=min_val, cur=CURRENCIES.get(cur, cur)),
                    parse_mode="Markdown"
                )
                return DEAL_AMT_ST
            ctx.user_data["damount"] = amount
            # Show fee choice step
            fee_pct = 0.03
            amount_with_fee = round(amount * (1 + fee_pct), 2)
            amount_after_fee = round(amount * (1 - fee_pct), 2)
            cur_label = CURRENCIES.get(cur, cur)
            await update.message.reply_text(
                tr(ctx, "fee_choice", gift="",
                   amount=amount, cur=cur_label,
                   amount_with_fee=amount_with_fee,
                   amount_after_fee=amount_after_fee),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tr(ctx, "btn_fee_buyer"), callback_data="fee_buyer")],
                    [InlineKeyboardButton(tr(ctx, "btn_fee_seller"), callback_data="fee_seller")],
                    [InlineKeyboardButton(tr(ctx, "back"), callback_data="create")],
                ]),
                parse_mode="Markdown"
            )
            return DEAL_AMT_ST
        except ValueError:
            await update.message.reply_text(tr(ctx,"bad_amount"), parse_mode="Markdown")
            return DEAL_AMT_ST

    if aw == "gift":
        cur = ctx.user_data.get("dcur")
        amount = ctx.user_data.get("damount")
        if not cur or not amount:
            await update.message.reply_text(
                tr(ctx,"menu", name=name, rating=u.get("rating",5.0), dc=u.get("deals_count",0)),
                reply_markup=menu_kb(ctx), parse_mode="Markdown"
            )
            return MENU_ST
        did = str(uuid.uuid4()).replace("-","")[:12].upper()
        bot_info = await ctx.bot.get_me()
        fee_mode = ctx.user_data.get("dfee_mode", "seller")
        deals[did] = {
            "seller_id": uid,
            "seller_name": update.effective_user.full_name or "Seller",
            "currency": cur,
            "amount": amount,
            "gift": text,
            "status": "active",
            "buyer_id": None,
            "buyer_name": None,
            "created": now_str(),
            "fee_mode": fee_mode,
        }
        u["deals"].append(did)
        fee_note = "👤 Комиссию платит покупатель (+3%)" if fee_mode == "buyer" else "🏪 Вы покрываете комиссию (-3%)"
        ctx.user_data.pop("await", None)
        ctx.user_data.pop("dcur", None)
        ctx.user_data.pop("damount", None)
        ctx.user_data.pop("dfee_mode", None)
        ctx.user_data.pop("dfee_pct", None)
        await update.message.reply_text(
            tr(ctx,"deal_created", gift=text, amount=amount,
               cur=CURRENCIES.get(cur,cur), id=did,
               bot=bot_info.username, date=now_str()) + f"\n💸 _{fee_note}_",
            reply_markup=menu_kb(ctx), parse_mode="Markdown"
        )
        return MENU_ST

    if aw == "search_deal":
        ctx.user_data.pop("await", None)
        query = text.upper().strip()
        found = [(did, dl) for did, dl in deals.items()
                 if did.upper().startswith(query) and dl["seller_id"] == uid]
        if not found:
            # Also search all deals if no seller match
            found = [(did, dl) for did, dl in deals.items() if did.upper().startswith(query)]
        if not found:
            await update.message.reply_text(tr(ctx, "search_deal_none"), reply_markup=menu_kb(ctx), parse_mode="Markdown")
        else:
            rows = ""
            for did, dl in found[:10]:
                rows += tr(ctx, "deal_row", icon=status_icon(dl["status"]),
                           id=did[:8], gift=dl["gift"], amount=dl["amount"], cur=dl["currency"])
            await update.message.reply_text(
                tr(ctx, "search_deal_found", result=rows),
                reply_markup=menu_kb(ctx), parse_mode="Markdown"
            )
        return MENU_ST

    if aw == "support":
        ctx.user_data.pop("await", None)
        # Forward message to support manager
        sender_username = update.effective_user.username
        sender_mention = f"@{sender_username}" if sender_username else update.effective_user.full_name or str(uid)
        try:
            await update.message.forward(chat_id=f"@{SUPPORT_USERNAME}")
        except Exception:
            pass
        try:
            await ctx.bot.send_message(
                chat_id=f"@{SUPPORT_USERNAME}",
                text=f"📩 *Новое сообщение от пользователя*\n\n"
                     f"👤 ID: `{uid}`\n"
                     f"👤 Имя: {update.effective_user.full_name}\n"
                     f"📱 Username: {sender_mention}\n"
                     f"📝 Сообщение: {text}",
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


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    all_cb = [CallbackQueryHandler(main_cb)]
    all_msg = [MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler)]

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
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
            CommandHandler("start", start),
            CommandHandler("otcteam", otcteam_cmd),
        ],
        per_message=False,
        allow_reentry=True,
    )

    app.add_handler(conv)

    async def post_init(application):
        await application.bot.set_my_commands([])

    app.post_init = post_init
    print("✅ OTC NFT Market Bot v2.1 running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
