import logging
import uuid
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ⚡ ADMIN IDs — впиши свой Telegram ID сюда (узнать у @userinfobot)
ADMIN_IDS = []  # Пример: [123456789, 987654321]

# States
CHOOSING_LANGUAGE = 1
MAIN_MENU = 2
REQUISITES_CHOOSE_CURRENCY = 3
REQUISITES_ENTER_DETAILS = 4
CREATE_DEAL_CURRENCY = 5
CREATE_DEAL_AMOUNT = 6
CREATE_DEAL_GIFT_NAME = 7
JOIN_DEAL = 8
SUPPORT_MESSAGE = 9
ADMIN_PANEL = 10
ADMIN_WAIT_INPUT = 11

# Translations
TEXTS = {
    "uk": {
        "welcome": "🎉 Ласкаво просимо до NFT Deals Bot!\n\n💎 Безпечні угоди з NFT подарунками\n\nОберіть мову:",
        "main_menu": "🏠 *Головне меню*\n\nОберіть дію:",
        "create_deal": "🤝 Створити угоду",
        "my_deals": "📋 Мої угоди",
        "referrals": "👥 Реферали",
        "requisites": "💳 Реквізити",
        "language": "🌐 Мова",
        "support": "🆘 Підтримка",
        "about": "ℹ️ Докладніше",
        "no_requisites": "⚠️ *Помилка!*\n\nСпочатку прив'яжіть свої реквізити!\n\nПерейдіть у розділ 💳 *Реквізити* та додайте платіжні дані.",
        "choose_requisites_currency": "💳 *Реквізити*\n\nОберіть валюту для прив'язки:",
        "enter_requisites": "✏️ Введіть ваші реквізити для *{currency}*:\n\n_(номер картки, гаманець або інші платіжні дані)_",
        "requisites_saved": "✅ Реквізити для *{currency}* успішно збережено!\n\n💡 Тепер ви можете створювати угоди.",
        "choose_deal_currency": "💱 *Створення угоди*\n\nОберіть валюту угоди:",
        "enter_amount": "💰 Введіть суму угоди у *{currency}*:",
        "invalid_amount": "❌ Невірна сума. Введіть число.",
        "enter_gift_name": "🎁 Введіть назву NFT подарунка:",
        "deal_created": "✅ *Угода успішно створена!*\n\n🎁 Подарунок: *{gift}*\n💰 Сума: *{amount} {currency}*\n🆔 ID угоди: `{deal_id}`\n\n🔗 *Посилання для покупця:*\n`https://t.me/{bot_username}?start=deal_{deal_id}`\n\n📤 Надішліть це посилання покупцю!",
        "no_deals": "📭 У вас поки немає угод.",
        "deals_list": "📋 *Ваші угоди:*\n\n{deals}",
        "deal_info": "🆔 `{id}`\n🎁 {gift} | 💰 {amount} {currency} | 📌 {status}",
        "referrals_text": "👥 *Реферальна програма*\n\n🔗 Ваше посилання:\n`https://t.me/{bot_username}?start=ref_{user_id}`\n\n👤 Рефералів: *{count}*\n💎 Бонусів: *{bonus}*",
        "language_changed": "✅ Мову змінено!",
        "choose_language": "🌐 Оберіть мову:",
        "support_text": "🆘 *Підтримка*\n\nНапишіть ваше повідомлення — ми відповімо якнайшвидше:",
        "support_sent": "✅ Повідомлення надіслано до підтримки!\n\nМи відповімо найближчим часом. 🙏",
        "about_text": "ℹ️ *NFT Deals Bot*\n\n💎 Безпечний обмін NFT подарунками\n🔐 Ескроу-система захисту\n🌍 Мультивалютність\n⚡️ Швидкі угоди\n\n📊 Версія: 1.0.0",
        "join_deal_text": "🤝 *Приєднатися до угоди*\n\n🆔 ID: `{deal_id}`\n🎁 Подарунок: *{gift}*\n💰 Сума: *{amount} {currency}*\n👤 Продавець: *{seller}*\n\nПідтвердити участь?",
        "join_confirm": "✅ Підтвердити",
        "join_cancel": "❌ Скасувати",
        "deal_joined": "🎉 Ви приєдналися до угоди!\n\nОчікуйте підтвердження від продавця.",
        "deal_not_found": "❌ Угода не знайдена або вже завершена.",
        "back": "⬅️ Назад",
        "status_active": "🟢 Активна",
        "status_pending": "🟡 Очікування",
        "status_done": "✅ Завершена",
        "greeting": "Привіт",
    },
    "en": {
        "welcome": "🎉 Welcome to NFT Deals Bot!\n\n💎 Secure NFT gift trading\n\nChoose your language:",
        "main_menu": "🏠 *Main Menu*\n\nChoose an action:",
        "create_deal": "🤝 Create Deal",
        "my_deals": "📋 My Deals",
        "referrals": "👥 Referrals",
        "requisites": "💳 Requisites",
        "language": "🌐 Language",
        "support": "🆘 Support",
        "about": "ℹ️ About",
        "no_requisites": "⚠️ *Error!*\n\nPlease link your requisites first!\n\nGo to 💳 *Requisites* section and add payment details.",
        "choose_requisites_currency": "💳 *Requisites*\n\nChoose currency to link:",
        "enter_requisites": "✏️ Enter your requisites for *{currency}*:\n\n_(card number, wallet or other payment details)_",
        "requisites_saved": "✅ Requisites for *{currency}* saved successfully!\n\n💡 Now you can create deals.",
        "choose_deal_currency": "💱 *Create Deal*\n\nChoose deal currency:",
        "enter_amount": "💰 Enter deal amount in *{currency}*:",
        "invalid_amount": "❌ Invalid amount. Please enter a number.",
        "enter_gift_name": "🎁 Enter NFT gift name:",
        "deal_created": "✅ *Deal created successfully!*\n\n🎁 Gift: *{gift}*\n💰 Amount: *{amount} {currency}*\n🆔 Deal ID: `{deal_id}`\n\n🔗 *Link for buyer:*\n`https://t.me/{bot_username}?start=deal_{deal_id}`\n\n📤 Send this link to the buyer!",
        "no_deals": "📭 You have no deals yet.",
        "deals_list": "📋 *Your Deals:*\n\n{deals}",
        "deal_info": "🆔 `{id}`\n🎁 {gift} | 💰 {amount} {currency} | 📌 {status}",
        "referrals_text": "👥 *Referral Program*\n\n🔗 Your link:\n`https://t.me/{bot_username}?start=ref_{user_id}`\n\n👤 Referrals: *{count}*\n💎 Bonuses: *{bonus}*",
        "language_changed": "✅ Language changed!",
        "choose_language": "🌐 Choose language:",
        "support_text": "🆘 *Support*\n\nWrite your message — we'll reply as soon as possible:",
        "support_sent": "✅ Message sent to support!\n\nWe'll reply shortly. 🙏",
        "about_text": "ℹ️ *NFT Deals Bot*\n\n💎 Secure NFT gift exchange\n🔐 Escrow protection system\n🌍 Multi-currency support\n⚡️ Fast deals\n\n📊 Version: 1.0.0",
        "join_deal_text": "🤝 *Join Deal*\n\n🆔 ID: `{deal_id}`\n🎁 Gift: *{gift}*\n💰 Amount: *{amount} {currency}*\n👤 Seller: *{seller}*\n\nConfirm participation?",
        "join_confirm": "✅ Confirm",
        "join_cancel": "❌ Cancel",
        "deal_joined": "🎉 You joined the deal!\n\nWaiting for seller confirmation.",
        "deal_not_found": "❌ Deal not found or already completed.",
        "back": "⬅️ Back",
        "status_active": "🟢 Active",
        "status_pending": "🟡 Pending",
        "status_done": "✅ Done",
        "greeting": "Hello",
    },
    "ru": {
        "welcome": "🎉 Добро пожаловать в NFT Deals Bot!\n\n💎 Безопасные сделки с NFT подарками\n\nВыберите язык:",
        "main_menu": "🏠 *Главное меню*\n\nВыберите действие:",
        "create_deal": "🤝 Создать сделку",
        "my_deals": "📋 Мои сделки",
        "referrals": "👥 Рефералы",
        "requisites": "💳 Реквизиты",
        "language": "🌐 Язык",
        "support": "🆘 Поддержка",
        "about": "ℹ️ Подробнее",
        "no_requisites": "⚠️ *Ошибка!*\n\nСначала привяжите свои реквизиты!\n\nПерейдите в раздел 💳 *Реквизиты* и добавьте платёжные данные.",
        "choose_requisites_currency": "💳 *Реквизиты*\n\nВыберите валюту для привязки:",
        "enter_requisites": "✏️ Введите ваши реквизиты для *{currency}*:\n\n_(номер карты, кошелёк или другие платёжные данные)_",
        "requisites_saved": "✅ Реквизиты для *{currency}* успешно сохранены!\n\n💡 Теперь вы можете создавать сделки.",
        "choose_deal_currency": "💱 *Создание сделки*\n\nВыберите валюту сделки:",
        "enter_amount": "💰 Введите сумму сделки в *{currency}*:",
        "invalid_amount": "❌ Неверная сумма. Введите число.",
        "enter_gift_name": "🎁 Введите название NFT подарка:",
        "deal_created": "✅ *Сделка успешно создана!*\n\n🎁 Подарок: *{gift}*\n💰 Сумма: *{amount} {currency}*\n🆔 ID сделки: `{deal_id}`\n\n🔗 *Ссылка для покупателя:*\n`https://t.me/{bot_username}?start=deal_{deal_id}`\n\n📤 Отправьте эту ссылку покупателю!",
        "no_deals": "📭 У вас пока нет сделок.",
        "deals_list": "📋 *Ваши сделки:*\n\n{deals}",
        "deal_info": "🆔 `{id}`\n🎁 {gift} | 💰 {amount} {currency} | 📌 {status}",
        "referrals_text": "👥 *Реферальная программа*\n\n🔗 Ваша ссылка:\n`https://t.me/{bot_username}?start=ref_{user_id}`\n\n👤 Рефералов: *{count}*\n💎 Бонусов: *{bonus}*",
        "language_changed": "✅ Язык изменён!",
        "choose_language": "🌐 Выберите язык:",
        "support_text": "🆘 *Поддержка*\n\nНапишите ваше сообщение — мы ответим как можно скорее:",
        "support_sent": "✅ Сообщение отправлено в поддержку!\n\nМы ответим в ближайшее время. 🙏",
        "about_text": "ℹ️ *NFT Deals Bot*\n\n💎 Безопасный обмен NFT подарками\n🔐 Эскроу-система защиты\n🌍 Мультивалютность\n⚡️ Быстрые сделки\n\n📊 Версия: 1.0.0",
        "join_deal_text": "🤝 *Присоединиться к сделке*\n\n🆔 ID: `{deal_id}`\n🎁 Подарок: *{gift}*\n💰 Сумма: *{amount} {currency}*\n👤 Продавец: *{seller}*\n\nПодтвердить участие?",
        "join_confirm": "✅ Подтвердить",
        "join_cancel": "❌ Отмена",
        "deal_joined": "🎉 Вы присоединились к сделке!\n\nОжидайте подтверждения от продавца.",
        "deal_not_found": "❌ Сделка не найдена или уже завершена.",
        "back": "⬅️ Назад",
        "status_active": "🟢 Активна",
        "status_pending": "🟡 Ожидание",
        "status_done": "✅ Завершена",
        "greeting": "Привет",
    },
    "ar": {
        "welcome": "🎉 مرحباً بك في NFT Deals Bot!\n\n💎 تداول آمن لهدايا NFT\n\nاختر لغتك:",
        "main_menu": "🏠 *القائمة الرئيسية*\n\nاختر إجراءً:",
        "create_deal": "🤝 إنشاء صفقة",
        "my_deals": "📋 صفقاتي",
        "referrals": "👥 الإحالات",
        "requisites": "💳 المتطلبات",
        "language": "🌐 اللغة",
        "support": "🆘 الدعم",
        "about": "ℹ️ حول",
        "no_requisites": "⚠️ *خطأ!*\n\nالرجاء ربط متطلباتك أولاً!\n\nانتقل إلى قسم 💳 *المتطلبات* وأضف بيانات الدفع.",
        "choose_requisites_currency": "💳 *المتطلبات*\n\nاختر العملة للربط:",
        "enter_requisites": "✏️ أدخل متطلباتك لـ *{currency}*:\n\n_(رقم البطاقة أو المحفظة أو بيانات الدفع الأخرى)_",
        "requisites_saved": "✅ تم حفظ متطلبات *{currency}* بنجاح!\n\n💡 يمكنك الآن إنشاء صفقات.",
        "choose_deal_currency": "💱 *إنشاء صفقة*\n\nاختر عملة الصفقة:",
        "enter_amount": "💰 أدخل مبلغ الصفقة بـ *{currency}*:",
        "invalid_amount": "❌ مبلغ غير صالح. أدخل رقماً.",
        "enter_gift_name": "🎁 أدخل اسم هدية NFT:",
        "deal_created": "✅ *تم إنشاء الصفقة بنجاح!*\n\n🎁 الهدية: *{gift}*\n💰 المبلغ: *{amount} {currency}*\n🆔 معرف الصفقة: `{deal_id}`\n\n🔗 *رابط المشتري:*\n`https://t.me/{bot_username}?start=deal_{deal_id}`\n\n📤 أرسل هذا الرابط للمشتري!",
        "no_deals": "📭 ليس لديك صفقات بعد.",
        "deals_list": "📋 *صفقاتك:*\n\n{deals}",
        "deal_info": "🆔 `{id}`\n🎁 {gift} | 💰 {amount} {currency} | 📌 {status}",
        "referrals_text": "👥 *برنامج الإحالة*\n\n🔗 رابطك:\n`https://t.me/{bot_username}?start=ref_{user_id}`\n\n👤 الإحالات: *{count}*\n💎 المكافآت: *{bonus}*",
        "language_changed": "✅ تم تغيير اللغة!",
        "choose_language": "🌐 اختر اللغة:",
        "support_text": "🆘 *الدعم*\n\nاكتب رسالتك — سنرد في أقرب وقت:",
        "support_sent": "✅ تم إرسال الرسالة للدعم!\n\nسنرد قريباً. 🙏",
        "about_text": "ℹ️ *NFT Deals Bot*\n\n💎 تبادل آمن لهدايا NFT\n🔐 نظام حماية الضمان\n🌍 دعم متعدد العملات\n⚡️ صفقات سريعة\n\n📊 الإصدار: 1.0.0",
        "join_deal_text": "🤝 *الانضمام إلى صفقة*\n\n🆔 المعرف: `{deal_id}`\n🎁 الهدية: *{gift}*\n💰 المبلغ: *{amount} {currency}*\n👤 البائع: *{seller}*\n\nتأكيد المشاركة؟",
        "join_confirm": "✅ تأكيد",
        "join_cancel": "❌ إلغاء",
        "deal_joined": "🎉 انضممت إلى الصفقة!\n\nانتظر تأكيد البائع.",
        "deal_not_found": "❌ الصفقة غير موجودة أو اكتملت.",
        "back": "⬅️ رجوع",
        "status_active": "🟢 نشطة",
        "status_pending": "🟡 معلقة",
        "status_done": "✅ مكتملة",
        "greeting": "مرحباً",
    },
    "zh": {
        "welcome": "🎉 欢迎来到 NFT Deals Bot!\n\n💎 安全的NFT礼品交易\n\n请选择语言:",
        "main_menu": "🏠 *主菜单*\n\n请选择操作:",
        "create_deal": "🤝 创建交易",
        "my_deals": "📋 我的交易",
        "referrals": "👥 推荐",
        "requisites": "💳 收款信息",
        "language": "🌐 语言",
        "support": "🆘 客服",
        "about": "ℹ️ 关于",
        "no_requisites": "⚠️ *错误！*\n\n请先绑定您的收款信息！\n\n前往 💳 *收款信息* 部分添加支付详情。",
        "choose_requisites_currency": "💳 *收款信息*\n\n选择要绑定的货币:",
        "enter_requisites": "✏️ 请输入 *{currency}* 的收款信息:\n\n_(银行卡号、钱包地址或其他支付信息)_",
        "requisites_saved": "✅ *{currency}* 的收款信息已成功保存！\n\n💡 现在您可以创建交易了。",
        "choose_deal_currency": "💱 *创建交易*\n\n选择交易货币:",
        "enter_amount": "💰 输入 *{currency}* 的交易金额:",
        "invalid_amount": "❌ 金额无效，请输入数字。",
        "enter_gift_name": "🎁 输入NFT礼品名称:",
        "deal_created": "✅ *交易创建成功！*\n\n🎁 礼品: *{gift}*\n💰 金额: *{amount} {currency}*\n🆔 交易ID: `{deal_id}`\n\n🔗 *买家链接:*\n`https://t.me/{bot_username}?start=deal_{deal_id}`\n\n📤 将此链接发送给买家！",
        "no_deals": "📭 您还没有交易。",
        "deals_list": "📋 *您的交易:*\n\n{deals}",
        "deal_info": "🆔 `{id}`\n🎁 {gift} | 💰 {amount} {currency} | 📌 {status}",
        "referrals_text": "👥 *推荐计划*\n\n🔗 您的链接:\n`https://t.me/{bot_username}?start=ref_{user_id}`\n\n👤 推荐人数: *{count}*\n💎 奖励: *{bonus}*",
        "language_changed": "✅ 语言已更改！",
        "choose_language": "🌐 选择语言:",
        "support_text": "🆘 *客服*\n\n请写下您的留言，我们会尽快回复:",
        "support_sent": "✅ 消息已发送至客服！\n\n我们会尽快回复。🙏",
        "about_text": "ℹ️ *NFT Deals Bot*\n\n💎 安全的NFT礼品交换\n🔐 托管保护系统\n🌍 多货币支持\n⚡️ 快速交易\n\n📊 版本: 1.0.0",
        "join_deal_text": "🤝 *加入交易*\n\n🆔 ID: `{deal_id}`\n🎁 礼品: *{gift}*\n💰 金额: *{amount} {currency}*\n👤 卖家: *{seller}*\n\n确认参与？",
        "join_confirm": "✅ 确认",
        "join_cancel": "❌ 取消",
        "deal_joined": "🎉 您已加入交易！\n\n等待卖家确认。",
        "deal_not_found": "❌ 交易未找到或已完成。",
        "back": "⬅️ 返回",
        "status_active": "🟢 活跃",
        "status_pending": "🟡 等待中",
        "status_done": "✅ 已完成",
        "greeting": "你好",
    },
    "ja": {
        "welcome": "🎉 NFT Deals Botへようこそ!\n\n💎 安全なNFTギフト取引\n\n言語を選択してください:",
        "main_menu": "🏠 *メインメニュー*\n\nアクションを選択:",
        "create_deal": "🤝 取引を作成",
        "my_deals": "📋 マイ取引",
        "referrals": "👥 紹介",
        "requisites": "💳 支払い情報",
        "language": "🌐 言語",
        "support": "🆘 サポート",
        "about": "ℹ️ 詳細",
        "no_requisites": "⚠️ *エラー！*\n\n先に支払い情報を登録してください！\n\n💳 *支払い情報* セクションに移動して決済情報を追加してください。",
        "choose_requisites_currency": "💳 *支払い情報*\n\n登録する通貨を選択:",
        "enter_requisites": "✏️ *{currency}* の支払い情報を入力してください:\n\n_(カード番号、ウォレットアドレス、その他の決済情報)_",
        "requisites_saved": "✅ *{currency}* の支払い情報が正常に保存されました！\n\n💡 これで取引を作成できます。",
        "choose_deal_currency": "💱 *取引を作成*\n\n取引通貨を選択:",
        "enter_amount": "💰 *{currency}* での取引金額を入力:",
        "invalid_amount": "❌ 無効な金額です。数字を入力してください。",
        "enter_gift_name": "🎁 NFTギフト名を入力:",
        "deal_created": "✅ *取引が正常に作成されました！*\n\n🎁 ギフト: *{gift}*\n💰 金額: *{amount} {currency}*\n🆔 取引ID: `{deal_id}`\n\n🔗 *購入者へのリンク:*\n`https://t.me/{bot_username}?start=deal_{deal_id}`\n\n📤 このリンクを購入者に送ってください！",
        "no_deals": "📭 まだ取引がありません。",
        "deals_list": "📋 *あなたの取引:*\n\n{deals}",
        "deal_info": "🆔 `{id}`\n🎁 {gift} | 💰 {amount} {currency} | 📌 {status}",
        "referrals_text": "👥 *紹介プログラム*\n\n🔗 あなたのリンク:\n`https://t.me/{bot_username}?start=ref_{user_id}`\n\n👤 紹介数: *{count}*\n💎 ボーナス: *{bonus}*",
        "language_changed": "✅ 言語が変更されました！",
        "choose_language": "🌐 言語を選択:",
        "support_text": "🆘 *サポート*\n\nメッセージを入力してください — できるだけ早く返信します:",
        "support_sent": "✅ サポートにメッセージが送信されました！\n\nすぐに返信します。🙏",
        "about_text": "ℹ️ *NFT Deals Bot*\n\n💎 安全なNFTギフト交換\n🔐 エスクロー保護システム\n🌍 マルチ通貨対応\n⚡️ 迅速な取引\n\n📊 バージョン: 1.0.0",
        "join_deal_text": "🤝 *取引に参加*\n\n🆔 ID: `{deal_id}`\n🎁 ギフト: *{gift}*\n💰 金額: *{amount} {currency}*\n👤 売り手: *{seller}*\n\n参加を確認しますか？",
        "join_confirm": "✅ 確認",
        "join_cancel": "❌ キャンセル",
        "deal_joined": "🎉 取引に参加しました！\n\n売り手の確認をお待ちください。",
        "deal_not_found": "❌ 取引が見つからないか、すでに完了しています。",
        "back": "⬅️ 戻る",
        "status_active": "🟢 アクティブ",
        "status_pending": "🟡 保留中",
        "status_done": "✅ 完了",
        "greeting": "こんにちは",
    },
}

CURRENCIES = {
    "UAH": "🇺🇦 UAH (Hryvnia)",
    "RUB": "🇷🇺 RUB (Ruble)",
    "KZT": "🇰🇿 KZT (Tenge)",
    "CNY": "🇨🇳 CNY (Yuan)",
    "USDT": "💵 USDT",
    "STARS": "⭐ Stars",
}

LANGUAGES = {
    "uk": "🇺🇦 Українська",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "ar": "🇸🇦 العربية",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
}

# In-memory storage
user_data_store = {}
deals_store = {}

def get_lang(context):
    return context.user_data.get("lang", "en")

def t(context, key, **kwargs):
    lang = get_lang(context)
    text = TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text

def get_user_store(user_id):
    if user_id not in user_data_store:
        user_data_store[user_id] = {
            "requisites": {},
            "deals": [],
            "referrals": 0,
            "rating": 0,
            "deals_count": 0,
            "balance": {},
        }
    return user_data_store[user_id]

def is_admin(user_id):
    return user_id in ADMIN_IDS

def language_keyboard():
    keyboard = []
    row = []
    for i, (code, name) in enumerate(LANGUAGES.items()):
        row.append(InlineKeyboardButton(name, callback_data=f"lang_{code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def main_menu_keyboard(context):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(context, "create_deal"), callback_data="create_deal"),
         InlineKeyboardButton(t(context, "my_deals"), callback_data="my_deals")],
        [InlineKeyboardButton(t(context, "referrals"), callback_data="referrals"),
         InlineKeyboardButton(t(context, "requisites"), callback_data="requisites")],
        [InlineKeyboardButton(t(context, "language"), callback_data="change_language"),
         InlineKeyboardButton(t(context, "support"), callback_data="support")],
        [InlineKeyboardButton(t(context, "about"), callback_data="about")],
    ])

def back_keyboard(context, callback="main_menu"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(t(context, "back"), callback_data=callback)]])

# ═══════════════════════════════════════════
#            🔐 ADMIN PANEL
# ═══════════════════════════════════════════

def admin_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить сделку", callback_data="adm_pay_deal"),
         InlineKeyboardButton("⭐ Изменить рейтинг", callback_data="adm_set_rating")],
        [InlineKeyboardButton("📊 Изменить кол-во сделок", callback_data="adm_set_deals"),
         InlineKeyboardButton("💰 Изменить баланс", callback_data="adm_set_balance")],
        [InlineKeyboardButton("👥 Список пользователей", callback_data="adm_users"),
         InlineKeyboardButton("📋 Все сделки", callback_data="adm_all_deals")],
        [InlineKeyboardButton("❌ Закрыть панель", callback_data="adm_close")],
    ])

async def otcteam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🔐 *OTC Team — Панель управления*\n\n"
        "👋 Добро пожаловать, администратор!\n\n"
        "Выберите действие:",
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown"
    )
    return ADMIN_PANEL

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id



    # ── Оплатить сделку ──
    if data == "adm_pay_deal":
        if not deals_store:
            await query.edit_message_text(
                "📭 Активных сделок нет.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")]]),
            )
            return ADMIN_PANEL

        keyboard = []
        for deal_id, deal in deals_store.items():
            if deal.get("status") != "done":
                label = f"#{deal_id[:8]} — {deal['gift']} | {deal['amount']} {deal['currency']}"
                keyboard.append([InlineKeyboardButton(label, callback_data=f"adm_pay_{deal_id}")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")])
        await query.edit_message_text(
            "💳 *Выберите сделку для оплаты:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ADMIN_PANEL

    # ── Подтвердить оплату сделки ──
    if data.startswith("adm_pay_"):
        deal_id = data[8:]
        deal = deals_store.get(deal_id)
        if deal:
            deal["status"] = "done"
            seller_id = deal.get("seller_id")
            if seller_id:
                store = get_user_store(seller_id)
                store["deals_count"] = store.get("deals_count", 0) + 1
            await query.edit_message_text(
                f"✅ *Сделка оплачена!*\n\n"
                f"🆔 ID: `{deal_id[:8]}`\n"
                f"🎁 {deal['gift']} | 💰 {deal['amount']} {deal['currency']}\n"
                f"📌 Статус: ✅ Завершена",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")]]),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Сделка не найдена.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")]]))
        return ADMIN_PANEL

    # ── Изменить рейтинг ──
    if data == "adm_set_rating":
        context.user_data["admin_action"] = "set_rating"
        await query.edit_message_text(
            "⭐ *Изменить рейтинг пользователя*\n\n"
            "Введите в формате:\n`ID_пользователя значение`\n\n"
            "Пример: `123456789 4.9`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")]]),
            parse_mode="Markdown"
        )
        return ADMIN_WAIT_INPUT

    # ── Изменить количество сделок ──
    if data == "adm_set_deals":
        context.user_data["admin_action"] = "set_deals"
        await query.edit_message_text(
            "📊 *Изменить количество сделок*\n\n"
            "Введите в формате:\n`ID_пользователя количество`\n\n"
            "Пример: `123456789 150`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")]]),
            parse_mode="Markdown"
        )
        return ADMIN_WAIT_INPUT

    # ── Изменить баланс ──
    if data == "adm_set_balance":
        context.user_data["admin_action"] = "set_balance"
        currencies_str = " | ".join(CURRENCIES.keys())
        await query.edit_message_text(
            "💰 *Изменить баланс пользователя*\n\n"
            "Введите в формате:\n`ID_пользователя ВАЛЮТА сумма`\n\n"
            f"Доступные валюты: `{currencies_str}`\n\n"
            "Пример: `123456789 USDT 500`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")]]),
            parse_mode="Markdown"
        )
        return ADMIN_WAIT_INPUT

    # ── Список пользователей ──
    if data == "adm_users":
        if not user_data_store:
            await query.edit_message_text(
                "📭 Пользователей нет.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")]]),
            )
            return ADMIN_PANEL

        text = "👥 *Пользователи:*\n\n"
        for uid, store in list(user_data_store.items())[:20]:
            rating = store.get("rating", 0)
            deals_c = store.get("deals_count", 0)
            balance = store.get("balance", {})
            bal_str = " | ".join([f"{v} {k}" for k, v in balance.items()]) or "—"
            text += (
                f"👤 ID: `{uid}`\n"
                f"⭐ Рейтинг: *{rating}* | 📊 Сделок: *{deals_c}*\n"
                f"💰 Баланс: {bal_str}\n\n"
            )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")]]),
            parse_mode="Markdown"
        )
        return ADMIN_PANEL

    # ── Все сделки ──
    if data == "adm_all_deals":
        if not deals_store:
            await query.edit_message_text(
                "📭 Сделок нет.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")]]),
            )
            return ADMIN_PANEL

        text = "📋 *Все сделки:*\n\n"
        for deal_id, deal in list(deals_store.items())[:15]:
            status_map = {"active": "🟢", "pending": "🟡", "done": "✅"}
            icon = status_map.get(deal.get("status", "active"), "❓")
            text += (
                f"{icon} `{deal_id[:8]}`\n"
                f"🎁 {deal['gift']} | 💰 {deal['amount']} {deal['currency']}\n"
                f"👤 Продавец: `{deal.get('seller_id', '?')}`\n\n"
            )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="adm_back")]]),
            parse_mode="Markdown"
        )
        return ADMIN_PANEL

    # ── Назад в админ-панель ──
    if data == "adm_back":
        await query.edit_message_text(
            "🔐 *OTC Team — Панель управления*\n\nВыберите действие:",
            reply_markup=admin_main_keyboard(),
            parse_mode="Markdown"
        )
        return ADMIN_PANEL

    # ── Закрыть панель ──
    if data == "adm_close":
        await query.edit_message_text("✅ Панель закрыта.")
        return MAIN_MENU

    return ADMIN_PANEL

async def admin_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id


    text = update.message.text.strip()
    action = context.user_data.get("admin_action")

    def back_btn():
        return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад в панель", callback_data="adm_back")]])

    # ── Установить рейтинг ──
    if action == "set_rating":
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ Формат: `ID_пользователя значение`\nПример: `123456789 4.9`",
                parse_mode="Markdown", reply_markup=back_btn())
            return ADMIN_WAIT_INPUT
        try:
            target_id = int(parts[0])
            rating = float(parts[1])
            store = get_user_store(target_id)
            store["rating"] = rating
            await update.message.reply_text(
                f"✅ *Рейтинг обновлён!*\n\n👤 Пользователь: `{target_id}`\n⭐ Новый рейтинг: *{rating}*",
                parse_mode="Markdown", reply_markup=back_btn()
            )
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Ошибка. Проверьте формат.", reply_markup=back_btn())
        context.user_data.pop("admin_action", None)
        return ADMIN_PANEL

    # ── Установить количество сделок ──
    if action == "set_deals":
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ Формат: `ID_пользователя количество`\nПример: `123456789 150`",
                parse_mode="Markdown", reply_markup=back_btn())
            return ADMIN_WAIT_INPUT
        try:
            target_id = int(parts[0])
            count = int(parts[1])
            store = get_user_store(target_id)
            store["deals_count"] = count
            await update.message.reply_text(
                f"✅ *Количество сделок обновлено!*\n\n👤 Пользователь: `{target_id}`\n📊 Сделок: *{count}*",
                parse_mode="Markdown", reply_markup=back_btn()
            )
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Ошибка. Проверьте формат.", reply_markup=back_btn())
        context.user_data.pop("admin_action", None)
        return ADMIN_PANEL

    # ── Установить баланс ──
    if action == "set_balance":
        parts = text.split()
        if len(parts) != 3:
            await update.message.reply_text(
                "❌ Формат: `ID_пользователя ВАЛЮТА сумма`\nПример: `123456789 USDT 500`",
                parse_mode="Markdown", reply_markup=back_btn()
            )
            return ADMIN_WAIT_INPUT
        try:
            target_id = int(parts[0])
            currency = parts[1].upper()
            amount = float(parts[2])
            if currency not in CURRENCIES:
                await update.message.reply_text(
                    f"❌ Неизвестная валюта. Доступные: `{' | '.join(CURRENCIES.keys())}`",
                    parse_mode="Markdown", reply_markup=back_btn()
                )
                return ADMIN_WAIT_INPUT
            store = get_user_store(target_id)
            if "balance" not in store:
                store["balance"] = {}
            store["balance"][currency] = amount
            await update.message.reply_text(
                f"✅ *Баланс обновлён!*\n\n👤 Пользователь: `{target_id}`\n💰 {currency}: *{amount}*",
                parse_mode="Markdown", reply_markup=back_btn()
            )
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Ошибка. Проверьте формат.", reply_markup=back_btn())
        context.user_data.pop("admin_action", None)
        return ADMIN_PANEL

    return ADMIN_WAIT_INPUT

# ═══════════════════════════════════════════
#            ОСНОВНОЙ БОТ
# ═══════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user_id = update.effective_user.id

    if args and args[0].startswith("deal_"):
        deal_id = args[0][5:]
        return await handle_join_deal(update, context, deal_id)

    if args and args[0].startswith("ref_"):
        try:
            ref_id = int(args[0][4:])
            if ref_id != user_id:
                store = get_user_store(ref_id)
                store["referrals"] = store.get("referrals", 0) + 1
        except ValueError:
            pass

    await update.message.reply_text(
        TEXTS["en"]["welcome"],
        reply_markup=language_keyboard(),
        parse_mode="Markdown"
    )
    return CHOOSING_LANGUAGE

async def handle_join_deal(update: Update, context: ContextTypes.DEFAULT_TYPE, deal_id: str):
    deal = deals_store.get(deal_id)
    if not deal:
        lang = get_lang(context)
        await update.message.reply_text(TEXTS[lang]["deal_not_found"])
        return MAIN_MENU

    lang = get_lang(context)
    seller_name = deal.get("seller_name", "Unknown")
    text = TEXTS[lang]["join_deal_text"].format(
        deal_id=deal_id[:8],
        gift=deal["gift"],
        amount=deal["amount"],
        currency=deal["currency"],
        seller=seller_name
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS[lang]["join_confirm"], callback_data=f"join_confirm_{deal_id}"),
         InlineKeyboardButton(TEXTS[lang]["join_cancel"], callback_data="main_menu")]
    ])
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    return JOIN_DEAL

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("lang_"):
        lang_code = data[5:]
        context.user_data["lang"] = lang_code
        await query.edit_message_text(
            t(context, "main_menu"),
            reply_markup=main_menu_keyboard(context),
            parse_mode="Markdown"
        )
        return MAIN_MENU

    if data == "main_menu":
        await query.edit_message_text(
            t(context, "main_menu"),
            reply_markup=main_menu_keyboard(context),
            parse_mode="Markdown"
        )
        return MAIN_MENU

    if data == "create_deal":
        store = get_user_store(user_id)
        if not store["requisites"]:
            await query.edit_message_text(
                t(context, "no_requisites"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t(context, "requisites"), callback_data="requisites")],
                    [InlineKeyboardButton(t(context, "back"), callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
            return MAIN_MENU

        user_currencies = store["requisites"].keys()
        keyboard = []
        row = []
        for code in user_currencies:
            name = CURRENCIES.get(code, code)
            row.append(InlineKeyboardButton(name, callback_data=f"deal_cur_{code}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton(t(context, "back"), callback_data="main_menu")])

        await query.edit_message_text(
            t(context, "choose_deal_currency"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return CREATE_DEAL_CURRENCY

    if data.startswith("deal_cur_"):
        currency = data[9:]
        context.user_data["deal_currency"] = currency
        context.user_data["awaiting"] = "deal_amount"
        await query.edit_message_text(
            t(context, "enter_amount", currency=CURRENCIES.get(currency, currency)),
            reply_markup=back_keyboard(context, "create_deal"),
            parse_mode="Markdown"
        )
        return CREATE_DEAL_AMOUNT

    if data == "my_deals":
        store = get_user_store(user_id)
        rating = store.get("rating", 0)
        deals_count = store.get("deals_count", 0)
        balance = store.get("balance", {})
        bal_str = "\n".join([f"  💰 {v} {k}" for k, v in balance.items()]) or "  —"

        header = (
            f"👤 *Ваш профиль*\n"
            f"⭐ Рейтинг: *{rating}*\n"
            f"📊 Сделок: *{deals_count}*\n"
            f"💳 Баланс:\n{bal_str}\n\n"
        )

        if not store["deals"]:
            await query.edit_message_text(
                header + t(context, "no_deals"),
                reply_markup=back_keyboard(context),
                parse_mode="Markdown"
            )
        else:
            deals_text = ""
            for deal_id in store["deals"]:
                deal = deals_store.get(deal_id)
                if deal:
                    status_key = f"status_{deal.get('status', 'active')}"
                    status = t(context, status_key)
                    deals_text += t(context, "deal_info",
                        id=deal_id[:8],
                        gift=deal["gift"],
                        amount=deal["amount"],
                        currency=deal["currency"],
                        status=status
                    ) + "\n\n"
            await query.edit_message_text(
                header + t(context, "deals_list", deals=deals_text),
                reply_markup=back_keyboard(context),
                parse_mode="Markdown"
            )
        return MAIN_MENU

    if data == "referrals":
        store = get_user_store(user_id)
        bot_info = await context.bot.get_me()
        await query.edit_message_text(
            t(context, "referrals_text",
                bot_username=bot_info.username,
                user_id=user_id,
                count=store.get("referrals", 0),
                bonus=store.get("referrals", 0) * 5
            ),
            reply_markup=back_keyboard(context),
            parse_mode="Markdown"
        )
        return MAIN_MENU

    if data == "requisites":
        store = get_user_store(user_id)
        keyboard = []
        row = []
        for i, (code, name) in enumerate(CURRENCIES.items()):
            check = "✅ " if code in store["requisites"] else ""
            row.append(InlineKeyboardButton(f"{check}{name}", callback_data=f"req_{code}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton(t(context, "back"), callback_data="main_menu")])
        await query.edit_message_text(
            t(context, "choose_requisites_currency"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return REQUISITES_CHOOSE_CURRENCY

    if data.startswith("req_"):
        currency = data[4:]
        if currency in CURRENCIES:
            context.user_data["req_currency"] = currency
            context.user_data["awaiting"] = "requisites"
            await query.edit_message_text(
                t(context, "enter_requisites", currency=CURRENCIES.get(currency, currency)),
                reply_markup=back_keyboard(context, "requisites"),
                parse_mode="Markdown"
            )
            return REQUISITES_ENTER_DETAILS
        return MAIN_MENU

    if data == "change_language":
        await query.edit_message_text(
            t(context, "choose_language"),
            reply_markup=language_keyboard(),
            parse_mode="Markdown"
        )
        return CHOOSING_LANGUAGE

    if data == "support":
        context.user_data["awaiting"] = "support"
        await query.edit_message_text(
            t(context, "support_text"),
            reply_markup=back_keyboard(context),
            parse_mode="Markdown"
        )
        return SUPPORT_MESSAGE

    if data == "about":
        await query.edit_message_text(
            t(context, "about_text"),
            reply_markup=back_keyboard(context),
            parse_mode="Markdown"
        )
        return MAIN_MENU

    if data.startswith("join_confirm_"):
        deal_id = data[13:]
        deal = deals_store.get(deal_id)
        if deal:
            deal["buyer_id"] = user_id
            deal["status"] = "pending"
            await query.edit_message_text(
                t(context, "deal_joined"),
                reply_markup=back_keyboard(context),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                t(context, "deal_not_found"),
                reply_markup=back_keyboard(context),
                parse_mode="Markdown"
            )
        return MAIN_MENU

    return MAIN_MENU

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if context.user_data.get("awaiting") == "requisites":
        currency = context.user_data.get("req_currency")
        store = get_user_store(user_id)
        store["requisites"][currency] = text
        context.user_data.pop("awaiting", None)
        context.user_data.pop("req_currency", None)
        await update.message.reply_text(
            t(context, "requisites_saved", currency=CURRENCIES.get(currency, currency)),
            reply_markup=main_menu_keyboard(context),
            parse_mode="Markdown"
        )
        return MAIN_MENU

    if context.user_data.get("awaiting") == "deal_amount":
        try:
            amount = float(text.replace(",", "."))
            context.user_data["deal_amount"] = amount
            context.user_data["awaiting"] = "deal_gift"
            await update.message.reply_text(
                t(context, "enter_gift_name"),
                reply_markup=back_keyboard(context, "create_deal"),
                parse_mode="Markdown"
            )
            return CREATE_DEAL_GIFT_NAME
        except ValueError:
            await update.message.reply_text(t(context, "invalid_amount"), parse_mode="Markdown")
            return CREATE_DEAL_AMOUNT

    if context.user_data.get("awaiting") == "deal_gift":
        gift_name = text
        currency = context.user_data.get("deal_currency")
        amount = context.user_data.get("deal_amount")
        deal_id = str(uuid.uuid4())[:12].upper()
        user_name = update.effective_user.full_name
        bot_info = await context.bot.get_me()

        deals_store[deal_id] = {
            "seller_id": user_id,
            "seller_name": user_name,
            "currency": currency,
            "amount": amount,
            "gift": gift_name,
            "status": "active",
        }
        store = get_user_store(user_id)
        store["deals"].append(deal_id)

        context.user_data.pop("awaiting", None)
        context.user_data.pop("deal_currency", None)
        context.user_data.pop("deal_amount", None)

        await update.message.reply_text(
            t(context, "deal_created",
                gift=gift_name,
                amount=amount,
                currency=CURRENCIES.get(currency, currency),
                deal_id=deal_id,
                bot_username=bot_info.username
            ),
            reply_markup=main_menu_keyboard(context),
            parse_mode="Markdown"
        )
        return MAIN_MENU

    if context.user_data.get("awaiting") == "support":
        context.user_data.pop("awaiting", None)
        await update.message.reply_text(
            t(context, "support_sent"),
            reply_markup=main_menu_keyboard(context),
            parse_mode="Markdown"
        )
        return MAIN_MENU

    await update.message.reply_text(
        t(context, "main_menu"),
        reply_markup=main_menu_keyboard(context),
        parse_mode="Markdown"
    )
    return MAIN_MENU

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("otcteam", otcteam_command),
        ],
        states={
            CHOOSING_LANGUAGE: [CallbackQueryHandler(callback_handler)],
            MAIN_MENU: [
                CallbackQueryHandler(callback_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
            ],
            REQUISITES_CHOOSE_CURRENCY: [CallbackQueryHandler(callback_handler)],
            REQUISITES_ENTER_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
                CallbackQueryHandler(callback_handler),
            ],
            CREATE_DEAL_CURRENCY: [CallbackQueryHandler(callback_handler)],
            CREATE_DEAL_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
                CallbackQueryHandler(callback_handler),
            ],
            CREATE_DEAL_GIFT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
                CallbackQueryHandler(callback_handler),
            ],
            JOIN_DEAL: [CallbackQueryHandler(callback_handler)],
            SUPPORT_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
                CallbackQueryHandler(callback_handler),
            ],
            ADMIN_PANEL: [
                CallbackQueryHandler(admin_callback),
            ],
            ADMIN_WAIT_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_input_handler),
                CallbackQueryHandler(admin_callback),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("otcteam", otcteam_command),
        ],
        per_message=False,
    )

    app.add_handler(conv_handler)

    # Скрываем команду /otcteam — не показываем её в меню команд
    async def post_init(application):
        await application.bot.set_my_commands([])  # пустой список = нет видимых команд

    app.post_init = post_init

    print("✅ NFT Deals Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
