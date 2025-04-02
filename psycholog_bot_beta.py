import telebot
from telebot import types
from telegram import Update
from telegram.ext import ContextTypes
import sqlite3
from datetime import datetime
import time


token='6041501355:AAGimzY0XK9fhSdvPZAnQmKTepvDMd1dPR0'
bot=telebot.TeleBot(token)
JoinedFile = open('Архив_пользователей.txt','r')
JoinedUsers = set()
for line in JoinedFile:
    JoinedUsers.add(line.strip())
JoinedFile.close()
SUPPORT_CHAT_ID = -1002580483998
ADMIN_CHAT_ID = [300742186, 255733852]


def init_subs_db():
    """Инициализация базы данных SQLite для хранения подписчиков"""
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    
    # Создаем таблицу подписчиков, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forwarded_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            source_chat_id INTEGER,
            target_chat_id INTEGER,
            content_type TEXT,
            forward_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Инициализируем БД при старте
init_subs_db()

# Инициализация базы данных SQLite
def init_db():
    """Создает базу данных и таблицу для хранения тикетов"""
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            ticket_id TEXT,
            question TEXT,
            answer TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
def save_question(user_id, username, ticket_id, question):
    """Сохраняет вопрос пользователя в базу данных"""
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tickets (user_id, username, ticket_id, question)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, ticket_id, question))
    conn.commit()
    conn.close()

def save_answer(ticket_id, answer):
    """Сохраняет ответ на вопрос и закрывает тикет"""
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tickets SET answer = ?, status = 'closed'
        WHERE ticket_id = ?
    ''', (answer, ticket_id))
    conn.commit()
    conn.close()

def get_user_tickets(user_id):
    """Возвращает все тикеты пользователя"""
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ticket_id, question, answer, status, created_at
        FROM tickets WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    tickets = cursor.fetchall()
    conn.close()
    return tickets


@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    
    # Добавляем или активируем пользователя
    cursor.execute('''
        INSERT OR REPLACE INTO subscribers 
        (user_id, username, first_name, last_name, is_active) 
        VALUES (?, ?, ?, ?, 1)
    ''', (user_id, username, first_name, last_name))
    
    conn.commit()
    conn.close()
    
    
    
    bot.send_message(message.chat.id,'Приветствую! Напишите /menu чтобы узнать всю информацию')
    if not str(message.chat.id) in JoinedUsers:
        JoinedFile = open('Архив_пользователей.txt','a')
        JoinedFile.write(str(message.chat.id) + "\n")
        JoinedUsers.add(message.chat.id)
@bot.message_handler(commands=['post'])
def mess(message):
    if message.chat.id not in ADMIN_CHAT_ID:
        bot.reply_to(message, "⛔ Эта команда доступна только администратору")
        return
    for user in JoinedUsers:
        bot.send_message(user,message.text[message.text.find(' '):])
@bot.message_handler(commands=['menu'])
def button_message_me(message):
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1=types.KeyboardButton("О себе")
    item2=types.KeyboardButton("Правила")
    item3=types.KeyboardButton("Прайс")
    item4=types.KeyboardButton("Мероприятия")
    item5 = types.KeyboardButton("🌟Поддержать разработчика🌟")
    item6=types.KeyboardButton("Написать Жанне")
    item7=types.KeyboardButton("📋 Мои вопросы")
    markup.add(item1,item2)
    markup.add(item3,item4)
    markup.add(item6,item7)
    markup.add(item5)
    
    bot.send_message(message.chat.id,'Возможные команды:',reply_markup=markup)

@bot.message_handler(commands=['stats'])
def stats(message):
    """Показывает статистику подписчиков (только для админа)"""
    if message.chat.id not in ADMIN_CHAT_ID:
        bot.reply_to(message, "⛔ Эта команда доступна только администратору")
        return
    
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    
    # Получаем общее количество подписчиков
    cursor.execute('SELECT COUNT(*) FROM subscribers WHERE is_active = 1')
    total = cursor.fetchone()[0]
    
    # Получаем количество новых подписчиков за последние 7 дней
    cursor.execute('''
        SELECT COUNT(*) FROM subscribers 
        WHERE is_active = 1 AND join_date >= datetime('now', '-7 days')
    ''')
    new_last_week = cursor.fetchone()[0]
    
    conn.close()
    
    # Формируем и отправляем отчет
    report = (
        "📊 Статистика подписчиков:\n\n"
        f"• Всего активных подписчиков: {total}\n"
        f"• Новых за последнюю неделю: {new_last_week}\n\n"
        f"• Для ручной рассылки просто напишите что-то в чат\n\n"
        f"• А затем ответьте на ваше сообщение /sendall\n\n"
         "Поддерживаются видео, фото, аудио, документы, а также стикеры Телеграм"
    )
    
    for chat_id in ADMIN_CHAT_ID:
        bot.send_message(chat_id, report)




@bot.message_handler(func=lambda message: message.text in ["О себе", "Правила", "Прайс", "Мероприятия", "🌟Поддержать разработчика🌟"])
def message_reply(message):
    if message.text=="О себе":
        markup = types.InlineKeyboardMarkup()
        btn4 = types.InlineKeyboardButton(text='Телеграм', url='https://t.me/zhanna_vorontsova')
        markup.add(btn4)
        file = open("Информация_о_себе.txt", 'r', encoding='UTF=8')
        bot.send_message(message.chat.id, file.read(), reply_markup=markup)
        file.close()
    elif message.text=="Правила":
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        file = open("Правила.txt", 'r', encoding='UTF=8')
        bot.send_message(message.chat.id, file.read(),reply_markup=markup)
        file.close()
    elif message.text=="Прайс":
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        file = open("Прайс.txt", 'r', encoding='UTF=8')
        bot.send_message(message.chat.id, file.read(),reply_markup=markup)
        file.close()
    elif message.text == "Мероприятия":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        file = open("Мероприятия.txt",'r',encoding='UTF=8')
        bot.send_message(message.chat.id,file.read(), reply_markup=markup)
        file.close()
    elif message.text == "🌟Поддержать разработчика🌟":
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text='ДонейшнАлертс', url='https://www.donationalerts.com/r/chillarium_room')
        btn2 = types.InlineKeyboardButton(text='Бусти',url='https://boosty.to/ondriss')
        markup.add(btn1, btn2)
        file = open("Финансовая_поддержка.txt",'r',encoding='UTF=8')
        bot.send_message(message.chat.id, file.read(), reply_markup=markup)
        file.close()
@bot.message_handler(func=lambda message: message.text == "Написать Жанне")
def ask_question(message):
    """Запрашивает у пользователя описание проблемы"""
    # Убираем клавиатуру для чистого ввода
    markup = types.ReplyKeyboardRemove()
    msg = bot.send_message(
        message.chat.id,
        "✍️ Опишите ваш вопрос максимально подробно:\n\n",
        reply_markup=markup
    )
    # Регистрируем следующий шаг - обработку вопроса
    bot.register_next_step_handler(msg, process_question)

def process_question(message):
    """Обрабатывает вопрос пользователя и создает тикет"""
    # Генерируем ID тикета
    ticket_id = f"T-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    username = message.from_user.username or f"id{message.from_user.id}"
    
    # Сохраняем вопрос в базу данных
    save_question(
        user_id=message.chat.id,
        username=username,
        ticket_id=ticket_id,
        question=message.text
    )
    
    # Создаем клавиатуру для подтверждения
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("✅ Да, отправить"))
    markup.add(types.KeyboardButton("❌ Нет, отменить"))
    
    # Отправляем подтверждение
    bot.send_message(
        message.chat.id,
        f"📝 Ваш вопрос:\n\n{message.text}\n\n"
        "Отправить?",
        reply_markup=markup
    )

# Обработчик подтверждения отправки вопроса
@bot.message_handler(func=lambda message: message.text in ["✅ Да, отправить", "❌ Нет, отменить"])
def confirm_question(message):
    """Обрабатывает подтверждение или отмену отправки вопроса"""
    if message.text == "✅ Да, отправить":
        # Получаем последний открытый тикет пользователя
        tickets = get_user_tickets(message.chat.id)
        if tickets:
            ticket = next((t for t in tickets if t[3] == 'open'), None)
            if ticket:
                ticket_id, question = ticket[0], ticket[1]
                username = message.from_user.username or f"id{message.from_user.id}"
                
                # Отправляем вопрос в чат поддержки
                bot.send_message(
                    SUPPORT_CHAT_ID,
                    f"🆘 НОВОЕ ОБРАЩЕНИЕ #{ticket_id}\n\n"
                    f"👤 От: @{username}\n"
                    f"🆔 ID: {message.chat.id}\n\n"
                    f"❓ Вопрос:\n{question}\n\n"
                    f"Для ответа используйте команду:\n"
                    f"/answer {message.chat.id} ваш_ответ"
                )
                
                # Отправляем подтверждение пользователю
                bot.send_message(
                    message.chat.id,
                    f"✅ Ваш вопрос #{ticket_id} передан Жанне.\n"
                    "Ответ придет так быстро, как сможет",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                return
    
        # Если тикет не найден
        bot.send_message(
            message.chat.id,
            "❌ Не удалось найти ваш вопрос. Пожалуйста, задайте его снова.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        # Если пользователь отменил отправку
        bot.send_message(
            message.chat.id,
            "❌ Отправка вопроса отменена.",
            reply_markup=types.ReplyKeyboardRemove()
        )
@bot.message_handler(func=lambda message: message.text == "📋 Мои вопросы")
def show_user_tickets(message):
    """Показывает историю обращений пользователя"""
    tickets = get_user_tickets(message.chat.id)
    
    if not tickets:
        bot.send_message(
            message.chat.id,
            "📭 У вас пока нет вопросов к Жанне",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    # Формируем сообщение с историей тикетов
    response = "📋 История ваших вопросов:\n\n"
    for ticket in tickets[:5]:  # Показываем последние 5 тикетов
        ticket_id, question, answer, status, created_at = ticket
        date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
        
        response += (
            f"🔢 #{ticket_id}\n"
            f"📅 {date}\n"
            f"🔄 Статус: {'✅ Закрыт' if status == 'closed' else '🟡 В обработке'}\n\n"
        )
    
    bot.send_message(
        message.chat.id,
        response,
        reply_markup=types.ReplyKeyboardRemove()
    )

# Обработчик команды /answer для операторов поддержки
@bot.message_handler(commands=['answer'])
def handle_answer(message):
    """Позволяет операторам отвечать на вопросы пользователей"""
    # Проверяем, что команда отправлена из чата поддержки
    if message.chat.id != SUPPORT_CHAT_ID:
        return
    
    try:
        # Парсим команду: /answer <user_id> <текст ответа>
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            raise ValueError
        
        _, user_id, answer_text = parts
        user_id = int(user_id)
        
        # Ищем открытый тикет пользователя
        conn = sqlite3.connect('support_bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ticket_id FROM tickets 
            WHERE user_id = ? AND status = 'open'
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,))
        ticket = cursor.fetchone()
        conn.close()
        
        if ticket:
            ticket_id = ticket[0]
            # Сохраняем ответ и закрываем тикет
            save_answer(ticket_id, answer_text)
            
            # Отправляем ответ пользователю
            bot.send_message(
                user_id,
                f"📩 Ответ от Жанны по обращению #{ticket_id}:\n\n"
                f"{answer_text}\n\n"
                f"Если вопрос не решен, можете задать новый через меню.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            
            # Подтверждаем оператору
            bot.reply_to(
                message,
                f"✅ Ответ отправлен пользователю (тикет #{ticket_id})."
            )
        else:
            bot.reply_to(
                message,
                "❌ У пользователя нет активных обращений."
            )
    except:
        bot.reply_to(
            message,
            "⚠️ Неверный формат команды. Используйте:\n"
            "/answer <user_id> <текст ответа>"
        )
 
 
 
@bot.message_handler(commands=['stats'])
def stats(message):
    """Показывает статистику подписчиков (только для админа)"""
    if message.chat.id not in ADMIN_CHAT_ID:
        bot.reply_to(message, "⛔ Эта команда доступна только администратору")
        return
    
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    
    # Получаем общее количество подписчиков
    cursor.execute('SELECT COUNT(*) FROM subscribers WHERE is_active = 1')
    total = cursor.fetchone()[0]
    
    # Получаем количество новых подписчиков за последние 7 дней
    cursor.execute('''
        SELECT COUNT(*) FROM subscribers 
        WHERE is_active = 1 AND join_date >= datetime('now', '-7 days')
    ''')
    new_last_week = cursor.fetchone()[0]
    
    conn.close()
    
    # Формируем и отправляем отчет
    report = (
        "📊 Статистика подписчиков:\n\n"
        f"• Всего активных подписчиков: {total}\n"
        f"• Новых за последнюю неделю: {new_last_week}\n\n"
        f"• Для ручной рассылки просто напишите что-то в чат\n\n"
         "Поддерживаются видео, фото, аудио, документы, а также стикеры Телеграм"
    )
    
    for chat_id in ADMIN_CHAT_ID:
        bot.send_message(chat_id, report)

def forward_to_subscribers(message):
    try:
        conn = sqlite3.connect('subscribers.db')
        cursor = conn.cursor()
        
        # Получаем только активных подписчиков
        cursor.execute('SELECT user_id FROM subscribers WHERE is_active = 1')
        subscribers = cursor.fetchall()
        
        success = 0
        content_type = message.content_type
        
        for user in subscribers:
            try:
                user_id = user[0]
                
                # Проверяем, существует ли чат с пользователем
                try:
                    bot.get_chat(user_id)
                except:
                    print(f"Чат {user_id} не найден, пропускаем")
                    continue
                
                if content_type == 'text':
                    bot.send_message(user_id, message.text)
                elif content_type == 'photo':
                    bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
                elif content_type == 'video':
                    bot.send_video(user_id, message.video.file_id, caption=message.caption)
                elif content_type == 'document':
                    bot.send_document(user_id, message.document.file_id, caption=message.caption)
                elif content_type == 'audio':
                    bot.send_audio(user_id, message.audio.file_id, caption=message.caption)
                elif content_type == 'sticker':
                    bot.send_sticker(user_id, message.sticker.file_id)
                
                success += 1
                
                
                # Логируем каждую успешную пересылку
                cursor.execute('''
                    INSERT INTO forwarded_messages 
                    (message_id, source_chat_id, target_chat_id, content_type) 
                    VALUES (?, ?, ?, ?)
                ''', (message.message_id, message.chat.id, user_id, content_type))
                conn.commit()
                
            except Exception as e:
                print(f"Ошибка пересылки для {user_id}: {e}")
        
        conn.close()
        return success
        
    except Exception as e:
        print(f"Ошибка в forward_to_subscribers: {e}")
        return 0

@bot.message_handler(commands=['sendall'])
def handle_sendall_command(message):
    """Обработчик команды /sendall для рассылки контента подписчикам"""
    try:
        # Проверка прав администратора
        if message.from_user.id not in ADMIN_CHAT_ID:
            bot.reply_to(message, "⛔ Только администратор может использовать эту команду.")
            return

        # Получаем активных подписчиков
        conn = sqlite3.connect('subscribers.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM subscribers WHERE is_active = 1')
        subscribers = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not subscribers:
            bot.reply_to(message, "❌ Нет активных подписчиков для рассылки.")
            return

        # Если сообщение - это ответ на другое сообщение
        if message.reply_to_message:
            content = message.reply_to_message
        else:
            content = message

        # Удаляем саму команду /sendall для текстовых сообщений
        if content.content_type == 'text' and content.text.startswith('/sendall'):
            content_text = content.text.replace('/sendall', '').strip()
            if not content_text:
                bot.reply_to(message, "❌ Вы не указали текст для рассылки")
                return
        else:
            content_text = content.text if hasattr(content, 'text') else None

        success = 0
        errors = 0

        for user_id in subscribers:
            try:
                # Пропускаем администраторов и самого бота
                if user_id in ADMIN_CHAT_ID or user_id == bot.get_me().id:
                    continue

                if content.content_type == 'text':
                    bot.send_message(user_id, content_text or content.text)
                elif content.content_type == 'photo':
                    bot.send_photo(user_id, content.photo[-1].file_id, 
                                 caption=content.caption)
                elif content.content_type == 'video':
                    bot.send_video(user_id, content.video.file_id, 
                                 caption=content.caption)
                elif content.content_type == 'document':
                    bot.send_document(user_id, content.document.file_id, 
                                    caption=content.caption)
                elif content.content_type == 'audio':
                    bot.send_audio(user_id, content.audio.file_id, 
                                 caption=content.caption)
                elif content.content_type == 'voice':
                    bot.send_voice(user_id, content.voice.file_id)
                elif content.content_type == 'sticker':
                    bot.send_sticker(user_id, content.sticker.file_id)
                elif content.content_type == 'animation':
                    bot.send_animation(user_id, content.animation.file_id,
                                     caption=content.caption)
                
                success += 1
                time.sleep(0.1)  # Задержка для соблюдения лимитов Telegram

            except Exception as e:
                print(f"Ошибка отправки для {user_id}: {str(e)}")
                errors += 1

        # Отправляем отчет администратору
        report = (
            f"📊 Результат рассылки:\n"
            f"• Тип контента: {content.content_type}\n"
            f"• Всего подписчиков: {len(subscribers)}\n"
            f"• Успешно отправлено: {success}\n"
            f"• Ошибок: {errors}"
        )
        bot.reply_to(message, report)

    except Exception as e:
        bot.reply_to(message, f"❌ Критическая ошибка: {str(e)}")
        print(f"Ошибка в handle_sendall_command: {str(e)}")
 
 
    
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)