import telebot
from telebot import types
from config import settings
import sqlite3

client = telebot.TeleBot(settings['TOKEN'])
connection = sqlite3.connect('server.db', check_same_thread=False) #creating database file
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    name TEXT,
    button_name TEXT,
    url TEXT,
    channel_id TEXT,
    message_id TEXT
)""")
connection.commit()
print("Bot connected")

@client.message_handler(commands=['start']) #command start
def start(message):
    if message.from_user.username in settings['admin_id']: 

        if cursor.execute(f"SELECT name FROM users WHERE name = '{message.from_user.username}'").fetchone() is None:
            cursor.execute(f"INSERT INTO users (name) VALUES ('{message.from_user.username}')")
            connection.commit()
        client.send_message(message.chat.id, "To create post enter /post")
    else: client.send_message(message.chat.id, "You have not rights to use this command")

@client.message_handler(commands=['post'])
def post(message):
    if message.from_user.username in settings['admin_id']:
        if cursor.execute(f"SELECT name FROM users WHERE name = '{message.from_user.username}'").fetchone() is None:
            cursor.execute(f"INSERT INTO users (name) VALUES ('{message.from_user.username}')")
            connection.commit()
        markup = types.ReplyKeyboardMarkup(row_width=1,one_time_keyboard=True)
        ru =  types.KeyboardButton("Channel 1")
        en = types.KeyboardButton("Channel 2")
        an = types.KeyboardButton("Another channel")
        markup.add(ru,en,an)
        client.send_message(message.chat.id, "Choose channel", reply_markup=markup)
        client.register_next_step_handler(message, set_channel)
    else: client.send_message(message.chat.id, "You have not rights to use this command")

@client.message_handler(content_types = ['text'])
def get_text(message):
    client.send_message(message.chat.id, "To talk with bot use commands")

def set_channel(message):
    if message.text == "Channel 1" or message.text == "Channel 2":
        if message.text == "Channel 1":
            cursor.execute("UPDATE users SET channel_id = '{}' WHERE name = '{}'".format(settings['id_1'], message.from_user.username))
            client.send_message(message.chat.id, "Choosed Channel 1")
        elif message.text == "Channel 2":
            cursor.execute("UPDATE users SET channel_id = '{}' WHERE name = '{}'".format(settings['id_2'], message.from_user.username))
            client.send_message(message.chat.id, "Choosed Channel 2")
        connection.commit()
        client.send_message(message.chat.id, "Enter name of button")
        client.register_next_step_handler(message, url_name)
    if message.text == "Другой канал":
        client.send_message(message.chat.id,"Forward the message from the telegram channel where you want to post")
        client.register_next_step_handler(message, id_setter)

def url_name(message): #receiving url
    cursor.execute("UPDATE users SET button_name = '{}' WHERE name = '{}'".format(message.text , message.from_user.username))
    connection.commit()
    client.send_message(message.chat.id, "Enter url")
    client.register_next_step_handler(message, add_post)

def add_post(message): #receiving post
    cursor.execute("UPDATE users SET url = '{}' WHERE name = '{}'".format(message.text, message.from_user.username))
    connection.commit()
    client.send_message(message.chat.id, "Enter post")
    client.register_next_step_handler(message, final_post)

def final_post(message): #checking result
    button_name = cursor.execute(f"SELECT button_name FROM users WHERE name = '{message.from_user.username}'").fetchone()[0]
    your_url = cursor.execute(f"SELECT url FROM users WHERE name = '{message.from_user.username}'").fetchone()[0]
    markup = types.InlineKeyboardMarkup()
    mk =  types.InlineKeyboardButton(text= button_name, url= your_url)
    markup.add(mk)
    client.copy_message(message.chat.id, message.chat.id, message.id, reply_markup = markup)
    cursor.execute("UPDATE users SET message_id = '{}' WHERE name = '{}'".format(message.id, message.from_user.username))
    connection.commit()
    markup2 = types.ReplyKeyboardMarkup(row_width= 1, one_time_keyboard=True)
    yes =  types.KeyboardButton("Yes")
    no = types.KeyboardButton("No")
    markup2.add(yes,no)
    client.send_message(message.chat.id, "Do you want to send this post?", reply_markup=markup2)
    client.register_next_step_handler(message, check_post)

def check_post(message): 
    if message.text == "Yes":
        button_name = cursor.execute(f"SELECT button_name FROM users WHERE name = '{message.from_user.username}'").fetchone()[0]
        your_url = cursor.execute(f"SELECT url FROM users WHERE name = '{message.from_user.username}'").fetchone()[0]
        channel_id = cursor.execute(f"SELECT channel_id FROM users WHERE name = '{message.from_user.username}'").fetchone()[0]
        message_id = cursor.execute(f"SELECT message_id FROM users WHERE name = '{message.from_user.username}'").fetchone()[0]
        markup = types.InlineKeyboardMarkup()
        mk =  types.InlineKeyboardButton(text= button_name, url= your_url)
        markup.add(mk)
        client.copy_message(channel_id, message.chat.id, message_id, reply_markup = markup) #sending post
    else:
        client.send_message(message.chat.id, "posting cancelled") #cancelling post
        pass

@client.message_handler(func=lambda message: True)
def id_setter(message):
    if message.forward_from_chat is not None:
        client.send_message(message.chat.id, "channel id received successfully!")
        print(message.forward_from_chat.id)
        cursor.execute("UPDATE users SET channel_id = '{}' WHERE name = '{}'".format(message.forward_from_chat.id, message.from_user.username))
        connection.commit()
        client.send_message(message.chat.id, "Enter name of button")
        client.register_next_step_handler(message, url_name)
    else:
        client.send_message(message.chat.id,"Error getting id")

client.polling(none_stop = True) #running bot