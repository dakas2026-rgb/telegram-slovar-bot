"""
Бот "Слово дня - Русский жестовый язык"
На основе учебников И.Ф. Гейльман, А.Е. Харламенкова
"""

import os
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


# === БАЗА ЖЕСТОВ РЖЯ ===

GESTURES_DB = {
    "привет": {
        "gesture_name": "Рука вверх с махом",
        "main_meaning": "ПРИВЕТ",
        "alternative_meanings": [
            {
                "word": "ЗДРАВСТВУЙ",
                "context": "Формальное приветствие",
                "example": "Здравствуй, как дела?",
                "difference": "Более медленное движение"
            },
            {
                "word": "ПРИВЕТСТВУЮ",
                "context": "Официальное обращение",
                "example": "Приветствую вас!",
                "difference": "Рука выше, движение четче"
            },
            {
                "word": "САЛЮТ",
                "context": "Неформальное, молодёжное",
                "example": "Салют, друзья!",
                "difference": "Быстрое, энергичное движение"
            }
        ],
        "description": "Поднимите правую руку на уровень головы ладонью вперёд. Помашите кистью из стороны в сторону 2-3 раза. Движение свободное, дружелюбное.",
        "examples": [
            "Привет! Как дела?",
            "Здравствуй, рад тебя видеть!",
            "Приветствую вас на встрече!"
        ],
        "category": "Приветствия",
        "difficulty": "Лёгкий",
        "tips": "Улыбайтесь! Зрительный контакт важен. Махи не слишком широкие.",
        "common_mistakes": "Не машите всей рукой от плеча — только кисть!",
        "gif_path": None  # Для будущих GIF
    },
    
    "спасибо": {
        "gesture_name": "Рука от сердца вперёд",
        "main_meaning": "СПАСИБО",
        "alternative_meanings": [
            {
                "word": "БЛАГОДАРЮ",
                "context": "Более формальное",
                "example": "Благодарю за помощь",
                "difference": "Рука дольше у сердца, затем плавно вперёд"
            },
            {
                "word": "БЛАГОДАРНОСТЬ",
                "context": "Существительное",
                "example": "Выражаю благодарность",
                "difference": "Обе руки к сердцу, затем вперёд"
            },
            {
                "word": "ПРИЗНАТЕЛЬНОСТЬ",
                "context": "Глубокая благодарность",
                "example": "Я вам очень признателен",
                "difference": "Движение медленнее, с наклоном головы"
            }
        ],
        "description": "Правую руку прижмите к груди в области сердца (пальцы вместе, ладонь к себе). Затем плавно выведите руку вперёд, раскрывая ладонь вверх, как бы отдавая благодарность от сердца.",
        "examples": [
            "Спасибо за помощь!",
            "Благодарю вас!",
            "Спасибо, очень приятно!"
        ],
        "category": "Вежливость",
        "difficulty": "Лёгкий",
        "tips": "Движение должно быть искренним, от сердца. Можно добавить лёгкий поклон головой.",
        "common_mistakes": "Не делайте резко — движение плавное и душевное.",
        "gif_path": None
    },
    
    "пожалуйста": {
        "gesture_name": "Открытая ладонь вперёд",
        "main_meaning": "ПОЖАЛУЙСТА",
        "alternative_meanings": [
            {
                "word": "ПРОШУ",
                "context": "Вежливая просьба",
                "example": "Прошу вас помочь",
                "difference": "Ладонь чуть наклонена к собе"
            },
            {
                "word": "УГОЩАЙТЕСЬ",
                "context": "Предложение",
                "example": "Угощайтесь, пожалуйста",
                "difference": "Движение ладони в сторону угощения"
            },
            {
                "word": "НЕ ЗА ЧТО",
                "context": "Ответ на спасибо",
                "example": "Не за что, обращайтесь!",
                "difference": "Легкое покачивание ладони"
            }
        ],
        "description": "Вытяните правую руку вперёд ладонью вверх, пальцы вместе. Сделайте плавное приглашающее движение к собеседнику или в сторону предмета.",
        "examples": [
            "Пожалуйста, проходите",
            "Прошу вас",
            "Не за что!"
        ],
        "category": "Вежливость",
        "difficulty": "Лёгкий",
        "tips": "Жест должен быть открытым и приглашающим. Улыбка обязательна!",
        "common_mistakes": "Не держите ладонь вертикально — только горизонтально или чуть вверх.",
        "gif_path": None
    },
    
    "да": {
        "gesture_name": "Кивок головой",
        "main_meaning": "ДА",
        "alternative_meanings": [
            {
                "word": "СОГЛАСЕН",
                "context": "Выражение согласия",
                "example": "Я согласен с вами",
                "difference": "Более энергичный кивок"
            },
            {
                "word": "ПРАВИЛЬНО",
                "context": "Подтверждение правоты",
                "example": "Правильно, именно так!",
                "difference": "Кивок + указательный палец вверх"
            },
            {
                "word": "КОНЕЧНО",
                "context": "Уверенное согласие",
                "example": "Конечно, помогу!",
                "difference": "Быстрые уверенные кивки"
            }
        ],
        "description": "Кивните головой вниз 1-2 раза. Можно дополнить жестом: кулак с поднятым большим пальцем вверх (знак одобрения).",
        "examples": [
            "Да, я согласен",
            "Да, конечно!",
            "Правильно!"
        ],
        "category": "Базовые слова",
        "difficulty": "Лёгкий",
        "tips": "Естественный кивок как в обычной жизни. Зрительный контакт!",
        "common_mistakes": "Не киваёте слишком много раз — 1-2 достаточно.",
        "gif_path": None
    },
    
    "нет": {
        "gesture_name": "Покачивание головой",
        "main_meaning": "НЕТ",
        "alternative_meanings": [
            {
                "word": "НЕ СОГЛАСЕН",
                "context": "Несогласие",
                "example": "Я не согласен с этим",
                "difference": "Более медленное покачивание"
            },
            {
                "word": "НЕПРАВИЛЬНО",
                "context": "Указание на ошибку",
                "example": "Неправильно, так не делается",
                "difference": "Покачивание + палец из стороны в сторону"
            },
            {
                "word": "НЕЛЬЗЯ",
                "context": "Запрет",
                "example": "Нельзя так делать!",
                "difference": "Энергичное покачивание + строгая мимика"
            }
        ],
        "description": "Покачайте головой из стороны в сторону 2-3 раза. Можно усилить жестом: указательный палец двигается из стороны в сторону перед собой.",
        "examples": [
            "Нет, я не могу",
            "Нет, это неправильно",
            "Нельзя!"
        ],
        "category": "Базовые слова",
        "difficulty": "Лёгкий",
        "tips": "Мимика важна! Покажите отрицание на лице.",
        "common_mistakes": "Не кивайте вверх-вниз — только в стороны!",
        "gif_path": None
    },
    
    "понимаю": {
        "gesture_name": "Рука к голове с кивком",
        "main_meaning": "ПОНИМАЮ",
        "alternative_meanings": [
            {
                "word": "ПОНЯЛ",
                "context": "Подтверждение понимания",
                "example": "Понял, сделаю",
                "difference": "Резкое касание лба + кивок"
            },
            {
                "word": "ЯСНО",
                "context": "Понимание объяснения",
                "example": "Ясно, теперь понятно",
                "difference": "Легкое касание + улыбка"
            },
            {
                "word": "ДОГАДАЛСЯ",
                "context": "Осознание",
                "example": "А, догадался!",
                "difference": "Палец к виску + кивок"
            }
        ],
        "description": "Коснитесь указательным пальцем лба или виска и кивните головой. Показывает, что информация 'вошла в голову'.",
        "examples": [
            "Понял, спасибо!",
            "Ясно, теперь понятно",
            "А, догадался!"
        ],
        "category": "Понимание и мышление",
        "difficulty": "Лёгкий",
        "tips": "Кивок головой усиливает понимание. Зрительный контакт обязателен.",
        "common_mistakes": "Не путайте с жестом 'думать' (там круговые движения).",
        "gif_path": None
    },
    
    "думать": {
        "gesture_name": "Круговые движения у головы",
        "main_meaning": "ДУМАТЬ",
        "alternative_meanings": [
            {
                "word": "РАЗМЫШЛЯТЬ",
                "context": "Глубокое обдумывание",
                "example": "Я долго размышлял над этим",
                "difference": "Медленные круговые движения"
            },
            {
                "word": "СООБРАЖАТЬ",
                "context": "Умственная работа",
                "example": "Нужно соображать быстрее",
                "difference": "Быстрые движения у виска"
            },
            {
                "word": "МОЗГИ (работают)",
                "context": "Разговорное",
                "example": "У меня мозги не варят",
                "difference": "Круги указательным пальцем у виска"
            }
        ],
        "description": "Указательным пальцем делайте круговые движения около виска или лба. Движение показывает 'работу мысли' в голове.",
        "examples": [
            "Я думаю над этим",
            "Дай мне подумать",
            "Надо соображать!"
        ],
        "category": "Понимание и мышление",
        "difficulty": "Средний",
        "tips": "Мимика задумчивости. Можно смотреть вверх или в сторону.",
        "common_mistakes": "Не путайте с 'понимаю' — там касание без кругов.",
        "gif_path": None
    },
    
    "хорошо": {
        "gesture_name": "Большой палец вверх",
        "main_meaning": "ХОРОШО",
        "alternative_meanings": [
            {
                "word": "ОТЛИЧНО",
                "context": "Высокая оценка",
                "example": "Отлично сделано!",
                "difference": "Энергичный жест + улыбка"
            },
            {
                "word": "ОК / ОКЕЙ",
                "context": "Согласие, одобрение",
                "example": "Окей, договорились",
                "difference": "Кольцо из пальцев (большой + указательный)"
            },
            {
                "word": "ЗДОРОВО",
                "context": "Восхищение",
                "example": "Здорово получилось!",
                "difference": "Большой палец + кивки головой"
            },
            {
                "word": "МОЛОДЕЦ",
                "context": "Похвала",
                "example": "Молодец, правильно!",
                "difference": "Большой палец вверх + похлопывание"
            }
        ],
        "description": "Сожмите руку в кулак, большой палец поднимите вверх. Жест энергичный, уверенный. Универсальный знак одобрения.",
        "examples": [
            "Как дела? — Хорошо!",
            "Отлично, так и сделаем",
            "Здорово получилось!"
        ],
        "category": "Эмоции и оценки",
        "difficulty": "Лёгкий",
        "tips": "Улыбка делает жест дружелюбнее. Можно добавить кивок.",
        "common_mistakes": "Не опускайте палец вниз — только вверх означает 'хорошо'!",
        "gif_path": None
    },
    
    "плохо": {
        "gesture_name": "Большой палец вниз",
        "main_meaning": "ПЛОХО",
        "alternative_meanings": [
            {
                "word": "УЖАСНО",
                "context": "Сильная негативная оценка",
                "example": "Ужасно получилось",
                "difference": "Резкое движение вниз + гримаса"
            },
            {
                "word": "НЕ НРАВИТСЯ",
                "context": "Неодобрение",
                "example": "Мне это не нравится",
                "difference": "Покачивание головой + палец вниз"
            },
            {
                "word": "ПРОВАЛ",
                "context": "Неудача",
                "example": "Полный провал",
                "difference": "Палец резко вниз + мимика разочарования"
            }
        ],
        "description": "Сожмите руку в кулак, большой палец направьте вниз. Мимика недовольства. Показывает негативную оценку.",
        "examples": [
            "Дела плохо",
            "Это ужасно",
            "Не нравится мне это"
        ],
        "category": "Эмоции и оценки",
        "difficulty": "Лёгкий",
        "tips": "Мимика важна — покажите недовольство на лице.",
        "common_mistakes": "Не путайте с другими жестами — палец строго вниз.",
        "gif_path": None
    },
    
    "любовь": {
        "gesture_name": "Рука к сердцу",
        "main_meaning": "ЛЮБОВЬ",
        "alternative_meanings": [
            {
                "word": "ЛЮБИТЬ",
                "context": "Глагол, чувство",
                "example": "Я тебя люблю",
                "difference": "Круговое движение рукой на сердце"
            },
            {
                "word": "НРАВИТЬСЯ (сильно)",
                "context": "Сильная симпатия",
                "example": "Мне это очень нравится",
                "difference": "Легкое касание + улыбка"
            },
            {
                "word": "ДОРОГОЙ",
                "context": "О близком человеке",
                "example": "Ты мне очень дорог",
                "difference": "Рука задерживается на сердце"
            },
            {
                "word": "ДУШЕВНЫЙ",
                "context": "Об эмоциональной близости",
                "example": "Душевный разговор",
                "difference": "Плавное круговое движение"
            }
        ],
        "description": "Прижмите правую руку (или обе руки) к груди в области сердца. Можно сделать мягкое круговое движение. Выражение лица тёплое, искреннее.",
        "examples": [
            "Я тебя люблю",
            "Люблю свою семью",
            "Это мне по душе"
        ],
        "category": "Эмоции и чувства",
        "difficulty": "Средний",
        "tips": "Искренность — главное. Мимика должна показывать тепло.",
        "common_mistakes": "Не путайте с 'спасибо' — там рука движется вперёд.",
        "gif_path": None
    }
}

# Категории для навигации
CATEGORIES = {
    "Приветствия": ["привет"],
    "Вежливость": ["спасибо", "пожалуйста"],
    "Базовые слова": ["да", "нет"],
    "Понимание и мышление": ["понимаю", "думать"],
    "Эмоции и оценки": ["хорошо", "плохо"],
    "Эмоции и чувства": ["любовь"]
}

# Для "слова дня" — меняется каждый день
def get_word_of_day():
    """Получить слово дня на основе даты"""
    today = datetime.now().day
    words = list(GESTURES_DB.keys())
    index = today % len(words)
    return words[index]


# === ФОРМАТИРОВАНИЕ СООБЩЕНИЙ ===

def format_gesture_full(gesture_key):
    """Полное описание жеста"""
    gesture = GESTURES_DB[gesture_key]
    
    message = f"🤟 <b>{gesture['main_meaning']}</b>\n\n"
    message += f"✋ <b>Жест:</b> {gesture['gesture_name']}\n\n"
    
    # Описание
    message += f"📝 <b>Как показать:</b>\n{gesture['description']}\n\n"
    
    # Альтернативные значения
    if gesture['alternative_meanings']:
        message += f"💭 <b>ДРУГИЕ ЗНАЧЕНИЯ ЭТОГО ЖЕСТА:</b>\n\n"
        for i, alt in enumerate(gesture['alternative_meanings'], 1):
            message += f"{i}️⃣ <b>{alt['word']}</b>\n"
            message += f"   📌 {alt['context']}\n"
            message += f"   💬 {alt['example']}\n"
            message += f"   🔍 {alt['difference']}\n\n"
    
    # Примеры
    message += f"💡 <b>Примеры фраз:</b>\n"
    for example in gesture['examples']:
        message += f"• {example}\n"
    
    message += f"\n⚠️ <b>Частая ошибка:</b>\n{gesture['common_mistakes']}\n\n"
    message += f"💡 <b>Совет:</b> {gesture['tips']}\n\n"
    message += f"📂 Категория: {gesture['category']}\n"
    message += f"⭐ Сложность: {gesture['difficulty']}"
    
    return message


def format_gesture_short(gesture_key):
    """Краткое описание жеста"""
    gesture = GESTURES_DB[gesture_key]
    
    message = f"🤟 <b>{gesture['main_meaning']}</b>\n\n"
    message += f"✋ {gesture['gesture_name']}\n\n"
    message += f"📝 {gesture['description'][:100]}...\n\n"
    message += f"💭 Также: {', '.join([alt['word'] for alt in gesture['alternative_meanings'][:2]])}"
    
    return message


# === ОБРАБОТЧИКИ КОМАНД ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("📅 Слово дня", callback_data='word_of_day')],
        [
            InlineKeyboardButton("📚 Категории", callback_data='categories'),
            InlineKeyboardButton("🔍 Поиск", callback_data='search')
        ],
        [
            InlineKeyboardButton("📖 Все жесты", callback_data='all_gestures'),
            InlineKeyboardButton("❓ Помощь", callback_data='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""👋 Привет, {user}!

Я помогу изучить <b>Русский жестовый язык</b>! 🤟

📚 <b>На основе учебников:</b>
• И.Ф. Гейльман
• А.Е. Харламенкова

<b>Что я умею:</b>

📅 Слово дня — каждый день новый жест
📚 Категории — жесты по темам
🔍 Поиск — найти нужный жест
💭 Варианты значений — один жест, много смыслов

<b>Выбери что хочешь изучить:</b>"""
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    message = """📚 <b>КАК ПОЛЬЗОВАТЬСЯ БОТОМ</b>

<b>Команды:</b>
/start - главное меню
/word - слово дня
/help - эта справка

<b>Кнопки:</b>
📅 Слово дня - ежедневный жест
📚 Категории - жесты по темам
🔍 Поиск - найти жест по слову
📖 Все жесты - полный список

<b>Что показывается:</b>
• Основное значение жеста
• Другие значения этого же жеста
• Как различить значения
• Подробное описание
• Примеры использования
• Частые ошибки
• Полезные советы

<b>Категории жестов:</b>
• Приветствия
• Вежливость
• Базовые слова
• Понимание и мышление
• Эмоции и оценки
• Эмоции и чувства

💡 <b>Совет:</b> Изучайте по 1-2 жеста в день, практикуйте перед зеркалом!"""
    
    await update.message.reply_text(message, parse_mode='HTML')


async def word_of_day_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /word - показать слово дня"""
    word = get_word_of_day()
    message = f"📅 <b>СЛОВО ДНЯ</b>\n\n{format_gesture_full(word)}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Случайный жест", callback_data='random_gesture')],
        [InlineKeyboardButton("◀️ В меню", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


# === ОБРАБОТЧИК КНОПОК ===

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'word_of_day':
        word = get_word_of_day()
        message = f"📅 <b>СЛОВО ДНЯ</b>\n\n{format_gesture_full(word)}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Случайный жест", callback_data='random_gesture')],
            [InlineKeyboardButton("◀️ В меню", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data == 'random_gesture':
        word = random.choice(list(GESTURES_DB.keys()))
        message = f"🎲 <b>СЛУЧАЙНЫЙ ЖЕСТ</b>\n\n{format_gesture_full(word)}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Ещё один", callback_data='random_gesture')],
            [InlineKeyboardButton("◀️ В меню", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data == 'categories':
        message = "📚 <b>КАТЕГОРИИ ЖЕСТОВ</b>\n\nВыберите категорию:"
        
        keyboard = []
        for category in CATEGORIES.keys():
            keyboard.append([InlineKeyboardButton(
                f"📁 {category}",
                callback_data=f'cat_{category}'
            )])
        keyboard.append([InlineKeyboardButton("◀️ В меню", callback_data='back')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data.startswith('cat_'):
        category = query.data[4:]
        gestures = CATEGORIES.get(category, [])
        
        message = f"📁 <b>{category.upper()}</b>\n\n"
        message += "Выберите жест для изучения:"
        
        keyboard = []
        for gesture_key in gestures:
            gesture = GESTURES_DB[gesture_key]
            keyboard.append([InlineKeyboardButton(
                f"🤟 {gesture['main_meaning']}",
                callback_data=f'show_{gesture_key}'
            )])
        keyboard.append([InlineKeyboardButton("◀️ К категориям", callback_data='categories')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data.startswith('show_'):
        gesture_key = query.data[5:]
        message = format_gesture_full(gesture_key)
        
        keyboard = [
            [InlineKeyboardButton("🔄 Случайный", callback_data='random_gesture')],
            [InlineKeyboardButton("◀️ В меню", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data == 'all_gestures':
        message = "📖 <b>ВСЕ ЖЕСТЫ</b>\n\n"
        
        for key, gesture in GESTURES_DB.items():
            message += f"🤟 <b>{gesture['main_meaning']}</b>\n"
            message += f"   {gesture['gesture_name']}\n\n"
        
        message += f"Всего жестов: {len(GESTURES_DB)}\n\n"
        message += "Выберите жест из категорий или используйте поиск!"
        
        keyboard = [
            [InlineKeyboardButton("📚 Категории", callback_data='categories')],
            [InlineKeyboardButton("◀️ В меню", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data == 'search':
        message = """🔍 <b>ПОИСК ЖЕСТА</b>

Просто напишите слово, и я найду жест!

<b>Например:</b>
• привет
• спасибо
• хорошо
• любовь

Я найду не только точное слово, но и похожие значения одного жеста!"""
        
        keyboard = [[InlineKeyboardButton("◀️ В меню", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data == 'help':
        await help_command(update, context)
    
    elif query.data == 'back':
        keyboard = [
            [InlineKeyboardButton("📅 Слово дня", callback_data='word_of_day')],
            [
                InlineKeyboardButton("📚 Категории", callback_data='categories'),
                InlineKeyboardButton("🔍 Поиск", callback_data='search')
            ],
            [
                InlineKeyboardButton("📖 Все жесты", callback_data='all_gestures'),
                InlineKeyboardButton("❓ Помощь", callback_data='help')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """📚 <b>ГЛАВНОЕ МЕНЮ</b>

Выберите раздел для изучения жестов:"""
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )


# === ПОИСК ПО ТЕКСТУ ===

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений (поиск)"""
    search_text = update.message.text.lower().strip()
    
    # Поиск по основному значению
    found_gestures = []
    
    for key, gesture in GESTURES_DB.items():
        # Поиск в основном значении
        if search_text in gesture['main_meaning'].lower():
            found_gestures.append((key, 'main'))
            continue
        
        # Поиск в альтернативных значениях
        for alt in gesture['alternative_meanings']:
            if search_text in alt['word'].lower():
                found_gestures.append((key, 'alt'))
                break
    
    if found_gestures:
        # Показываем первый найденный жест
        gesture_key, match_type = found_gestures[0]
        
        if match_type == 'main':
            message = f"✅ <b>НАЙДЕНО!</b>\n\n{format_gesture_full(gesture_key)}"
        else:
            message = f"✅ <b>НАЙДЕНО!</b>\n\n"
            message += f"Слово '{search_text}' — это одно из значений жеста:\n\n"
            message += format_gesture_full(gesture_key)
        
        keyboard = [
            [InlineKeyboardButton("🔄 Случайный", callback_data='random_gesture')],
            [InlineKeyboardButton("◀️ В меню", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        message = f"❌ Жест для слова '<b>{search_text}</b>' пока не найден.\n\n"
        message += "Попробуйте:\n"
        message += "• Другое слово\n"
        message += "• Посмотреть все жесты\n"
        message += "• Выбрать категорию"
        
        keyboard = [
            [InlineKeyboardButton("📖 Все жесты", callback_data='all_gestures')],
            [InlineKeyboardButton("📚 Категории", callback_data='categories')],
            [InlineKeyboardButton("◀️ В меню", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )


# === ГЛАВНАЯ ФУНКЦИЯ ===

def main():
    """Запуск бота"""
    logger.info("=" * 60)
    logger.info("🤟 БОТ 'СЛОВО ДНЯ - РЖЯ'")
    logger.info("=" * 60)
    
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Команды
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("word", word_of_day_command))
        
        # Кнопки
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Поиск по тексту
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        ))
        
        logger.info("✅ Handlers registered")
        logger.info(f"📚 База: {len(GESTURES_DB)} жестов")
        logger.info("⏳ Starting polling...")
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        exit(1)


if __name__ == '__main__':
    main()
