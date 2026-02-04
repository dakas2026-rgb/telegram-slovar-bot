"""
Бот "Слово дня - Русский жестовый язык"
На основе учебников И.Ф. Гейльман, А.Е. Харламенкова
Расширенная версия с JSON базой
"""

import os
import json
import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('BOT_TOKEN')

if not TOKEN:
    logger.error("❌ BOT_TOKEN not found!")
    exit(1)

# === ЗАГРУЗКА БАЗЫ ЖЕСТОВ ===

def load_gestures():
    """Загрузка базы из JSON файла"""
    try:
        with open('gestures.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"✅ База жестов загружена: {len(data)} слов.")
            return data
    except FileNotFoundError:
        logger.warning("⚠️ Файл gestures.json не найден! Использую резервную базу.")
        # Маленькая резервная база, чтобы бот не упал
        return {
            "привет": {
                "gesture_name": "Мах рукой",
                "main_meaning": "ПРИВЕТ",
                "alternative_meanings": [],
                "description": "Помашите рукой.",
                "examples": ["Привет!"],
                "category": "Приветствия",
                "difficulty": "Лёгкий",
                "tips": "",
                "common_mistakes": ""
            }
        }
    except json.JSONDecodeError:
        logger.error("❌ Ошибка в формате JSON файла!")
        return {}

GESTURES_DB = load_gestures()

# Генерация категорий динамически на основе загруженной базы
def get_categories():
    cats = {}
    for key, val in GESTURES_DB.items():
        cat_name = val.get('category', 'Разное')
        if cat_name not in cats:
            cats[cat_name] = []
        cats[cat_name].append(key)
    return cats

CATEGORIES = get_categories()


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def get_word_of_day():
    """Получить слово дня на основе даты"""
    if not GESTURES_DB:
        return None
    today = datetime.now().day
    words = list(GESTURES_DB.keys())
    index = today % len(words)
    return words[index]

def format_gesture_full(gesture_key):
    """Полное описание жеста"""
    if gesture_key not in GESTURES_DB:
        return "Ошибка: Жест не найден."
        
    gesture = GESTURES_DB[gesture_key]
    
    message = f"🤟 <b>{gesture['main_meaning']}</b>\n\n"
    message += f"✋ <b>Жест:</b> {gesture['gesture_name']}\n\n"
    
    # Описание
    message += f"📝 <b>Как показать:</b>\n{gesture['description']}\n\n"
    
    # Альтернативные значения (Синонимы к жесту)
    if gesture.get('alternative_meanings'):
        message += f"💭 <b>СИНОНИМЫ ЖЕСТА (ДРУГИЕ ЗНАЧЕНИЯ):</b>\n\n"
        for i, alt in enumerate(gesture['alternative_meanings'], 1):
            message += f"{i}️⃣ <b>{alt['word']}</b>\n"
            if 'context' in alt: message += f"   📌 {alt['context']}\n"
            if 'example' in alt: message += f"   💬 {alt['example']}\n"
            if 'difference' in alt: message += f"   🔍 {alt['difference']}\n\n"
    
    # Примеры
    if gesture.get('examples'):
        message += f"💡 <b>Примеры фраз:</b>\n"
        for example in gesture['examples']:
            message += f"• {example}\n"
    
    if gesture.get('common_mistakes'):
        message += f"\n⚠️ <b>Частая ошибка:</b>\n{gesture['common_mistakes']}\n\n"
        
    if gesture.get('tips'):
        message += f"💡 <b>Совет:</b> {gesture['tips']}\n\n"
        
    message += f"📂 Категория: {gesture.get('category', 'Разное')}\n"
    message += f"⭐ Сложность: {gesture.get('difficulty', 'Нет данных')}"
    
    return message


# === ОБРАБОТЧИКИ ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("📅 Слово дня", callback_data='word_of_day')],
        [InlineKeyboardButton("📚 Категории", callback_data='categories'),
         InlineKeyboardButton("🔍 Поиск", callback_data='search')],
        [InlineKeyboardButton("📖 Все жесты", callback_data='all_gestures'),
         InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"👋 Привет, {user}!\n\nЯ знаю <b>{len(GESTURES_DB)}</b> жестов РЖЯ! 🤟\n\nВыбери, что хочешь изучить:"
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """📚 <b>СПРАВКА</b>
    
Напиши любое слово, и я найду подходящий жест!
Я ищу не только по названию, но и по синонимам.

Например, жест <b>'ДОМ'</b> найдется, если написать:
• Дом
• Здание
• Жилище
"""
    await update.message.reply_text(message, parse_mode='HTML')

async def word_of_day_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word = get_word_of_day()
    if not word:
        await update.message.reply_text("База пуста!")
        return
        
    message = f"📅 <b>СЛОВО ДНЯ</b>\n\n{format_gesture_full(word)}"
    keyboard = [[InlineKeyboardButton("🔄 Случайный жест", callback_data='random_gesture')],
                [InlineKeyboardButton("◀️ В меню", callback_data='back')]]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'word_of_day':
        word = get_word_of_day()
        if word:
            message = f"📅 <b>СЛОВО ДНЯ</b>\n\n{format_gesture_full(word)}"
            keyboard = [[InlineKeyboardButton("🔄 Случайный", callback_data='random_gesture')],
                        [InlineKeyboardButton("◀️ В меню", callback_data='back')]]
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif query.data == 'random_gesture':
        if not GESTURES_DB: return
        word = random.choice(list(GESTURES_DB.keys()))
        message = f"🎲 <b>СЛУЧАЙНЫЙ ЖЕСТ</b>\n\n{format_gesture_full(word)}"
        keyboard = [[InlineKeyboardButton("🔄 Ещё один", callback_data='random_gesture')],
                    [InlineKeyboardButton("◀️ В меню", callback_data='back')]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif query.data == 'categories':
        # Пересчитываем категории (если вдруг база обновилась, хотя в рантайме это редкость)
        cats = get_categories()
        message = "📚 <b>КАТЕГОРИИ ЖЕСТОВ</b>"
        keyboard = []
        for cat in cats.keys():
            keyboard.append([InlineKeyboardButton(f"📁 {cat} ({len(cats[cat])})", callback_data=f'cat_{cat}')])
        keyboard.append([InlineKeyboardButton("◀️ В меню", callback_data='back')])
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif query.data.startswith('cat_'):
        cat_name = query.data[4:]
        cats = get_categories()
        gestures = cats.get(cat_name, [])
        
        message = f"📁 <b>{cat_name.upper()}</b>\nВыберите жест:"
        keyboard = []
        # Пагинация если слишком много кнопок (упрощенно - показываем первые 50)
        for g_key in gestures[:50]:
            g_name = GESTURES_DB[g_key]['main_meaning']
            keyboard.append([InlineKeyboardButton(f"🤟 {g_name}", callback_data=f'show_{g_key}')])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='categories')])
        
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif query.data.startswith('show_'):
        g_key = query.data[5:]
        message = format_gesture_full(g_key)
        keyboard = [[InlineKeyboardButton("🔄 Случайный", callback_data='random_gesture')],
                    [InlineKeyboardButton("◀️ В меню", callback_data='back')]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif query.data == 'all_gestures':
        message = f"📖 <b>ВСЕ ЖЕСТЫ ({len(GESTURES_DB)})</b>\n\nИспользуйте поиск или категории, список слишком длинный!"
        keyboard = [[InlineKeyboardButton("📚 Категории", callback_data='categories')],
                    [InlineKeyboardButton("🔍 Поиск", callback_data='search')],
                    [InlineKeyboardButton("◀️ В меню", callback_data='back')]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif query.data == 'search':
        message = "🔍 <b>ПОИСК</b>\n\nПросто напиши слово в чат. Я найду жест или его синонимы."
        keyboard = [[InlineKeyboardButton("◀️ В меню", callback_data='back')]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif query.data == 'back':
        await start(update, context)

    elif query.data == 'help':
        await help_command(update, context)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Умный поиск по базе"""
    if not update.message or not update.message.text: return
    
    search_text = update.message.text.lower().strip()
    found = []

    for key, val in GESTURES_DB.items():
        # 1. Поиск по ключу или основному значению
        if search_text in key or search_text in val['main_meaning'].lower():
            found.append((key, 'main'))
            continue
        
        # 2. Поиск по синонимам (alternative_meanings)
        if 'alternative_meanings' in val:
            for alt in val['alternative_meanings']:
                if search_text in alt['word'].lower():
                    found.append((key, alt['word']))
                    break
    
    if found:
        # Берем первый результат
        g_key, match_word = found[0]
        if match_word == 'main':
            header = "✅ <b>НАЙДЕНО!</b>"
        else:
            header = f"✅ <b>НАЙДЕНО ПО СИНОНИМУ:</b> '{match_word.upper()}'"
            
        message = f"{header}\n\n{format_gesture_full(g_key)}"
        keyboard = [[InlineKeyboardButton("🔄 Случайный", callback_data='random_gesture')],
                    [InlineKeyboardButton("◀️ В меню", callback_data='back')]]
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    else:
        await update.message.reply_text(f"❌ Жест для '{search_text}' не найден.\nПопробуйте другое слово или переформулируйте.")

def main():
    logger.info(f"🤟 БОТ ЗАПУЩЕН. В базе {len(GESTURES_DB)} слов.")
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("word", word_of_day_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
