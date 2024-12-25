from telebot import TeleBot, types
import telebot
import random
import string
import smtplib
from email.mime.text import MIMEText
from telebot import types
from pytube import YouTube
import time
import threading
import os
from threading import Thread

API_TOKEN = '' #YOUR BOT TOKEN 

bot = telebot.TeleBot(API_TOKEN)

# Bot owner ID (replace with your actual Telegram chat ID)
OWNER_ID = 5756495153

users = {}
otp_storage = {}

# Generate a random OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_email(gmail_id, otp):
    try:
        msg = MIMEText(f'Your OTP is: {otp}')
        msg['Subject'] = 'Your OTP Code'
        msg['From'] = '' #YOUR MAIL ID HERE 
        msg['To'] = gmail_id

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login('#YOUR MAIL ID HERE ', '# YOUR MAIL APP PASSWORD')
            server.sendmail('#YOUR MAIL ID HERE', gmail_id, msg.as_string())
    except Exception as e:
        print("Error sending email:", e)

    @bot.message_handler(func=lambda msg: True)
    def get_gmail(msg):
        gmail_id = msg.text
        
        # Check if Gmail ID is already used
        if gmail_id in [user_info['gmail'] for user_info in users.values()]:
            bot.send_message(chat_id, "This Gmail ID is already used. Please use a different Gmail ID:")
            return
        
        otp = generate_otp()
        otp_storage[gmail_id] = otp
        send_email(gmail_id, otp)
        bot.send_message(message.chat.id, "An OTP has been sent to your Gmail. Please enter the OTP:")

        
        @bot.message_handler(func=lambda otp_msg: True)
        def verify_otp(otp_msg):
            if otp_msg.text == otp_storage[gmail_id]:
                users[chat_id] = {
                    'gmail': gmail_id,
                    'username': f'user_{chat_id}',  # Replace with actual logic if needed
                    'first_name': message.from_user.first_name,
                    'last_name': message.from_user.last_name,
                    'phone': 'Not provided'  # Add logic to collect phone if necessary
                }
                bot.send_message(chat_id, "Registration successful!")
                del otp_storage[gmail_id]  # Remove OTP after successful login
            else:
                bot.send_message(chat_id, "Invalid OTP. Please try again.")

@bot.message_handler(commands=['users'])
def show_all_users(message):
    if message.chat.id != OWNER_ID:
        bot.send_message(message.chat.id, "Only owner can run this command.")
        return

    if not users:
        bot.send_message(message.chat.id, "No users found.")
        return

    all_users_info = "*User Profiles:*"
    for user_id, user_info in users.items():
        username = user_info.get('username', 'Not available')
        first_name = user_info.get('first_name', 'Not available')
        last_name = user_info.get('last_name', 'Not available')
        user_phone = user_info.get('phone', 'Not provided')
        user_gmail = user_info.get('gmail', 'Not provided')

        all_users_info += f"""
        \n*Username:* {username}
        *First Name:* {first_name}
        *Last Name:* {last_name}
        *User ID:* {user_id}
        *User Phone Number:* {user_phone}
        *User Gmail:* {user_gmail}
        """
    
    bot.send_message(message.chat.id, all_users_info, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Welcome! Please log in or sign up using /login or /signup.")


@bot.message_handler(commands=['signup'])
def signup(message):
    bot.send_message(message.chat.id, "Please send your Gmail ID.")
    bot.register_next_step_handler(message, get_gmail)

def get_gmail(message):
    gmail_id = message.text
    otp = generate_otp()
    otp_storage[gmail_id] = otp
    send_email(gmail_id, otp)  # Send the OTP here
    bot.send_message(message.chat.id, f"OTP sent to {gmail_id}. Please enter the OTP.")
    bot.register_next_step_handler(message, verify_otp, gmail_id)

def verify_otp(message, gmail_id):
    if message.text == otp_storage[gmail_id]:
        bot.send_message(message.chat.id, "OTP verified! Enter your new password.")
        bot.register_next_step_handler(message, set_password, gmail_id)
    else:
        bot.send_message(message.chat.id, "Incorrect OTP. Please restart the signup process using /signup.")

def set_password(message, gmail_id):
    password = message.text
    users[message.from_user.id] = {'gmail': gmail_id, 'password': password}
    bot.send_message(message.chat.id, "Successfully signed up! Please log in using /login.")

@bot.message_handler(commands=['login'])
def login(message):
    bot.send_message(message.chat.id, "Please send your email and password in the format: gmail,password.")
    bot.register_next_step_handler(message, handle_login)

def handle_login(message):
    try:
        gmail, password = message.text.split(",")
        user = users.get(message.from_user.id)
        if user and user['gmail'] == gmail and user['password'] == password:
            bot.send_message(message.chat.id, "Logged in successfully!")
        else:
            bot.send_message(message.chat.id, "Login failed. Please check your credentials.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid format. Please use: gmail,password.")

@bot.message_handler(commands=['mute'])
def mute_user(message):
    # Check if the bot is an admin
    chat_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
    
    if chat_member.status not in ["administrator", "creator"]:
        bot.send_message(message.chat.id, "I don't have permission to use this command.")
        return

    # Check if the command issuer is an admin
    if chat_member.status != "administrator":
        bot.send_message(message.chat.id, "This command can only be used by group admins.")
        return

    # Mute the user (if replying to a message)
    if message.reply_to_message:
        user_to_mute = message.reply_to_message.from_user.id
        try:
            # Mute the user by restricting all their permissions
            bot.restrict_chat_member(
                message.chat.id,
                user_to_mute,
                permissions=types.ChatPermissions(can_send_messages=False,
                                                  can_send_media_messages=False,
                                                  can_send_other_messages=False,
                                                  can_send_voice_messages=False,
                                                  can_invite_to_channels=False,
                                                  can_pinish_meaning=False,
                                                  can_share_location=False)
            )
            bot.send_message(message.chat.id, f"User {message.reply_to_message.from_user.username} has been muted.")
        except Exception as e:
            bot.send_message(message.chat.id, "An error occurred while muting the user.")
            print(f"Error: {e}")
    else:
        bot.send_message(message.chat.id, "Please reply to a user's message to mute them.")



@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    # Check if the bot is an admin
    chat_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
    
    if chat_member.status not in ["administrator", "creator"]:
        bot.send_message(message.chat.id, "I don't have permission to use this command.")
        return

    # Check if the command issuer is an admin
    if chat_member.status != "administrator":
        bot.send_message(message.chat.id, "This command can only be used by group admins.")
        return

    # Unmute the user (if replying to a message)
    if message.reply_to_message:
        user_to_unmute = message.reply_to_message.from_user.id
        try:
            # Unmute the user by restoring their permissions
            bot.restrict_chat_member(
                message.chat.id,
                user_to_unmute,
                permissions=types.ChatPermissions(can_send_messages=True,
                                                  can_send_media_messages=True,
                                                  can_send_other_messages=True,
                                                  can_send_voice_messages=True,
                                                  can_invite_to_channels=True,
                                                  can_pin_messages=True,   # Fixed variable name
                                                  can_share_location=True)
            )
            bot.send_message(message.chat.id, f"User {message.reply_to_message.from_user.username} has been unmuted.")
        except Exception as e:
            bot.send_message(message.chat.id, "An error occurred while unmuting the user.")
            print(f"Error: {e}")
    else:
        bot.send_message(message.chat.id, "Please reply to a user's message to unmute them.")


@bot.message_handler(commands=['ban'])
def ban_user(message):
    # Check if the bot is an admin
    bot_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
    
    if bot_member.status not in ["administrator", "creator"]:
        bot.send_message(message.chat.id, "I don't have permission to use this command.")
        return

    # Check if the command issuer is an admin
    if message.from_user.id not in [member.user.id for member in bot.get_chat_administrators(message.chat.id)]:
        bot.send_message(message.chat.id, "This command can only be used by group admins.")
        return

    user_id_to_ban = None

    # Check if the command is used with a username or user_id
    if len(message.text.split()) == 2:
        user_input = message.text.split()[1]
        
        # If the input is a username
        if user_input.startswith('@'):
            username = user_input[1:]  # Remove the '@'
            try:
                user = bot.get_chat_member(message.chat.id, username)
                user_id_to_ban = user.user.id
            except Exception:
                bot.send_message(message.chat.id, "User not found.")
                return
            
        # If the input is a user ID
        else:
            try:
                user_id_to_ban = int(user_input)  # Convert to integer
            except ValueError:
                bot.send_message(message.chat.id, "Invalid user ID.")
                return
    
    # If the command is used by replying to a user's message
    elif message.reply_to_message:
        user_id_to_ban = message.reply_to_message.from_user.id

    if user_id_to_ban:
        try:
            # Ban the user
            bot.ban_chat_member(message.chat.id, user_id_to_ban)
            bot.send_message(message.chat.id, f"User has been banned.")
        except Exception as e:
            bot.send_message(message.chat.id, "An error occurred while banning the user.")
            print(f"Error: {e}")
    else:
        bot.send_message(message.chat.id, "Please use the format: /ban <username or user_id> or reply to a user.")

        
# Start polling
bot.polling()
