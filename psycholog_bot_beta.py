import telebot
from telebot import types
from telegram import Update
from telegram.ext import ContextTypes
import sqlite3
from datetime import datetime


token='6041501355:AAGimzY0XK9fhSdvPZAnQmKTepvDMd1dPR0'
bot=telebot.TeleBot(token)
JoinedFile = open('Архив_пользователей.txt','r')
JoinedUsers = set()
for line in JoinedFile:
    JoinedUsers.add(line.strip())
JoinedFile.close()
SUPPORT_CHAT_ID = -4745976213

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
    bot.send_message(message.chat.id,'Приветствую! Напишите /menu чтобы узнать всю информацию')
    if not str(message.chat.id) in JoinedUsers:
        JoinedFile = open('Архив_пользователей.txt','a')
        JoinedFile.write(str(message.chat.id) + "\n")
        JoinedUsers.add(message.chat.id)
@bot.message_handler(commands=['post'])
def mess(message):
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
    item6=types.KeyboardButton("Задать вопрос")
    item7=types.KeyboardButton("📋 Мои обращения")
    markup.add(item1,item2)
    markup.add(item3,item4)
    markup.add(item6,item7)
    markup.add(item5)
    
    bot.send_message(message.chat.id,'Возможные команды:',reply_markup=markup)


@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text=="О себе":
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text='ВКонтакте', url='https://vk.com/zhannavorontsova')
        btn2 = types.InlineKeyboardButton(text='Instagram', url='https://instagram.com/janna_vorontsova?igshid=YmMyMTA2M2Y=')
        btn3 = types.InlineKeyboardButton(text='Ясно', url='https://yasno.live/therapists/VJRF3NJV-zhanna-vorontsova')
        btn4 = types.InlineKeyboardButton(text='Телеграм', url='https://t.me/zhanna_vorontsova')
        markup.add(btn1,btn2,btn3,btn4)
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
@bot.message_handler(func=lambda message: message.text == "Задать вопрос")
def ask_question(message):
    """Запрашивает у пользователя описание проблемы"""
    # Убираем клавиатуру для чистого ввода
    markup = types.ReplyKeyboardRemove()
    msg = bot.send_message(
        message.chat.id,
        "✍️ Опишите вашу вопрос максимально подробно:\n\n",
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
        f"🔢 Номер обращения: {ticket_id}\n\n"
        "Отправить в поддержку?",
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
                    f"✅ Ваш вопрос #{ticket_id} передан в поддержку.\n"
                    "Мы ответим вам в ближайшее время.",
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
@bot.message_handler(func=lambda message: message.text == "📋 Мои обращения")
def show_user_tickets(message):
    """Показывает историю обращений пользователя"""
    tickets = get_user_tickets(message.chat.id)
    
    if not tickets:
        bot.send_message(
            message.chat.id,
            "📭 У вас пока нет обращений в поддержку.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    # Формируем сообщение с историей тикетов
    response = "📋 История ваших обращений:\n\n"
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
                f"📩 Ответ от специалиста по обращению #{ticket_id}:\n\n"
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
    
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)