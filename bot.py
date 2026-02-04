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

# === ЗАГРУЗКА БАЗЫ ===

def load_gestures():
    """Загрузка базы из JSON файла"""
    try:
        with open('gestures.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"✅ База жестов загружена: {len(data)} слов.")
            return data
    except FileNotFoundError:
        logger.warning("⚠️ Файл gestures.json не найден! Использую резервную базу.")
        return {
            "привет": {
                "gesture_name": "Мах рукой",
                "main_meaning": "ПРИВЕТ",
                "alternative_meanings": [],
                "description": "Помашите рукой.",
                "examples": ["Привет!"],
                "category": "Приветствия",
                "difficulty": "Лёгкий"
            }
        }
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка в формате JSON файла: {e}")
        return {}

GESTURES_DB = load_gestures()

def get_categories():
    """Группировка жестов по категориям"""
    cats = {}
    for key, val in GESTURES_DB.items():
        cat_name = val.get('category', 'Разное')
        if cat_name not in cats:
            cats[cat_name] = []
        cats[cat_name].append(key)
    return cats

# === ФОРМАТИРОВАНИЕ ===

def format_gesture_full(gesture_key):
    """Полное описание жеста"""
    if gesture_key not in GESTURES_DB:
        return "⚠️ Ошибка: Жест не найден в базе."
        
    gesture = GESTURES_DB[gesture_key]
    
    message = f"🤟 <b>{gesture['main_meaning']}</b>\n\n"
    message += f"✋ <b>Жест:</b> {gesture['gesture_name']}\n\n"
    message += f"📝 <b>Как показать:</b>\n{gesture['description']}\n\n"
    
    if gesture.get('alternative_meanings'):
        message += f"💭 <b>Синонимы:</b>\n"
        for alt in gesture['alternative_meanings']:
            message += f"• {alt['word']}\n"
        message += "\n"
    
    if gesture.get('examples'):
        message += f"💡 <b>Примеры:</b>\n"
        for ex in gesture['examples']:
            message += f"• {ex}\n"
            
    return message

def get_keyboard_for_gesture(gesture_key):
    """Создает клавиатуру для жеста (с GIF если есть)"""
    keyboard = []
    
    # Кнопка GIF
    if gesture_key in GESTURES_DB and 'gif' in GESTURES_DB[gesture_key]:
        keyboard.append([InlineKeyboardButton("🎬 Смотреть GIF", callback_data=f'gif_{gesture_key}')])
    
    # Стандартные кнопки
    keyboard.append([InlineKeyboardButton("🔄 Случайный", callback_data='random_gesture')])
    keyboard.append([InlineKeyboardButton("◀️ В меню", callback_data='back')])
    
    return InlineKeyboardMarkup(keyboard)

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
    
    message = f"👋 Привет, {user}!\n\nЯ знаю <b>{len(GESTURES_DB)}</b> жестов РЖЯ! 🤟\n\nВыбери действие:"
    
    # Если это callback (нажатие кнопки "В меню"), редактируем старое сообщение
    if update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🔍 <b>Поиск:</b> Просто напиши слово в чат.\n\n📚 <b>База:</b> Я понимаю синонимы (например, 'дом' и 'жилище')."
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ В меню", callback_data='back')]]), parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # ВАЖНО: Всегда отвечать на callback, иначе кнопка будет вечно грузиться
    try:
        await query.answer()
    except Exception:
        pass # Игнорируем ошибки сети при ответе

    data = query.data

    if data == 'back':
        await start(update, context)

    elif data == 'word_of_day':
        if not GESTURES_DB: return
        # Слово дня от числа месяца
        today = datetime.now().day
        keys = list(GESTURES_DB.keys())
        word = keys[today % len(keys)]
        
        await query.edit_message_text(
            format_gesture_full(word),
            reply_markup=get_keyboard_for_gesture(word),
            parse_mode='HTML'
        )

    elif data == 'random_gesture':
        if not GESTURES_DB: return
        word = random.choice(list(GESTURES_DB.keys()))
        
        await query.edit_message_text(
            f"🎲 <b>СЛУЧАЙНЫЙ ЖЕСТ</b>\n\n{format_gesture_full(word)}",
            reply_markup=get_keyboard_for_gesture(word),
            parse_mode='HTML'
        )

    elif data == 'categories':
        cats = get_categories()
        keyboard = []
        for cat in cats.keys():
            # Кол-во слов в категории
            count = len(cats[cat])
            keyboard.append([InlineKeyboardButton(f"📁 {cat} ({count})", callback_data=f'cat_{cat}')])
        keyboard.append([InlineKeyboardButton("◀️ В меню", callback_data='back')])
        
        await query.edit_message_text("📚 <b>КАТЕГОРИИ:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif data.startswith('cat_'):
        cat_name = data[4:]
        cats = get_categories()
        gestures = cats.get(cat_name, [])
        
        keyboard = []
        # Показываем максимум 30 кнопок, чтобы не перегрузить телеграм
        for g_key in gestures[:30]:
            name = GESTURES_DB[g_key]['main_meaning']
            keyboard.append([InlineKeyboardButton(f"🤟 {name}", callback_data=f'show_{g_key}')])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='categories')])
        
        await query.edit_message_text(f"📁 <b>{cat_name.upper()}</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif data.startswith('show_'):
        g_key = data[5:]
        await query.edit_message_text(
            format_gesture_full(g_key),
            reply_markup=get_keyboard_for_gesture(g_key),
            parse_mode='HTML'
        )

    elif data.startswith('gif_'):
        g_key = data[4:]
        gesture = GESTURES_DB.get(g_key)
        if gesture and 'gif' in gesture:
            try:
                await query.message.reply_animation(
                    animation=gesture['gif'],
                    caption=f"🤟 {gesture['main_meaning']}"
                )
            except Exception as e:
                await query.message.reply_text("❌ Не удалось загрузить GIF. Ссылка недоступна.")
                logger.error(f"GIF Error: {e}")
        else:
            await query.message.reply_text("🤷‍♂️ Для этого жеста нет GIF.")

    elif data == 'search':
        await query.edit_message_text(
            "🔍 <b>ПОИСК</b>\n\nНапиши любое слово в чат, я найду жест.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ В меню", callback_data='back')]]),
            parse_mode='HTML'
        )
        
    elif data == 'all_gestures':
        await query.edit_message_text(
            f"Всего жестов в базе: {len(GESTURES_DB)}.\nИспользуйте категории для просмотра.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📚 Категории", callback_data='categories')], [InlineKeyboardButton("◀️ В меню", callback_data='back')]])
        )
    
    elif data == 'help':
        await help_command(update, context)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по тексту"""
    if not update.message or not update.message.text: return
    search = update.message.text.lower().strip()
    
    found_key = None
    
    # Поиск
    for key, val in GESTURES_DB.items():
        # 1. По названию
        if search in key or search in val['main_meaning'].lower():
            found_key = key
            break
        # 2. По синонимам
        if 'alternative_meanings' in val:
            for alt in val['alternative_meanings']:
                if search in alt['word'].lower():
                    found_key = key
                    break
        if found_key: break
    
    if found_key:
        await update.message.reply_text(
            f"✅ <b>НАЙДЕНО!</b>\n\n{format_gesture_full(found_key)}",
            reply_markup=get_keyboard_for_gesture(found_key),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"❌ Жест '{search}' не найден.\nПопробуйте синоним или загляните в категории.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📚 Категории", callback_data='categories')]])
        )

def main():
    logger.info("🚀 Бот запускается...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler)) # <-- Самое важное для кнопок
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
