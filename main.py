import asyncio
import os
import sys
import telebot
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv

load_dotenv()

import handlers
import gemini
from config import conf

TG_TOKEN = os.getenv("TG_TOKEN")
GOOGLE_GEMINI_KEY = os.getenv("GOOGLE_GEMINI_KEY")
OWNER_ID = os.getenv("OWNER_ID")

if not TG_TOKEN or not GOOGLE_GEMINI_KEY or not OWNER_ID:
    print("Error: Environment variables TG_TOKEN, GOOGLE_GEMINI_KEY, and OWNER_ID must be set.")
    sys.exit(1)

# Populate API keys in the gemini module
if GOOGLE_GEMINI_KEY:
    keys = [key.strip() for key in GOOGLE_GEMINI_KEY.split(',') if key.strip()]
    gemini.api_keys.extend(keys)

# Initialize the Gemini client now that keys are loaded
gemini.initialize_client()

print("Environment variables and API keys loaded.")

async def main():
    # Init bot
    bot = AsyncTeleBot(TG_TOKEN)
    
    bot_commands = [
        telebot.types.BotCommand("start", "Start using the bot"),
        telebot.types.BotCommand("gemini", f"Use {conf['model_1']}"),
        telebot.types.BotCommand("gemini_pro", f"Use {conf['model_2']}"),
        telebot.types.BotCommand("draw", "Draw a picture"),
        telebot.types.BotCommand("edit", "Edit a photo"),
        telebot.types.BotCommand("clear", "Clear chat history"),
        telebot.types.BotCommand("switch", "Switch default text model"),
        telebot.types.BotCommand("system", "Set a custom system prompt"),
        telebot.types.BotCommand("system_clear", "Delete the system prompt"),
        telebot.types.BotCommand("system_reset", "Reset the system prompt"),
        telebot.types.BotCommand("system_show", "Show the current system prompt"),
        telebot.types.BotCommand("api_add", "Add API key(s)"),
        telebot.types.BotCommand("api_remove", "Remove an API key"),
        telebot.types.BotCommand("api_list", "List all API keys"),
        telebot.types.BotCommand("api_switch", "Switch the current API key")
    ]
    
    # Set bot commands
    await bot.delete_my_commands(scope=None, language_code=None)
    await bot.set_my_commands(bot_commands)
    print("Bot commands set.")

    # Register all handlers
    bot.register_message_handler(handlers.start,                         commands=['start'],         pass_bot=True)
    bot.register_message_handler(handlers.gemini_stream_handler,         commands=['gemini'],        pass_bot=True)
    bot.register_message_handler(handlers.gemini_pro_stream_handler,     commands=['gemini_pro'],    pass_bot=True)
    bot.register_message_handler(handlers.draw_handler,                  commands=['draw'],          pass_bot=True)
    bot.register_message_handler(handlers.gemini_edit_handler,           commands=['edit'],          pass_bot=True)
    bot.register_message_handler(handlers.clear,                         commands=['clear'],         pass_bot=True)
    bot.register_message_handler(handlers.switch,                        commands=['switch'],        pass_bot=True)
    bot.register_message_handler(handlers.system_prompt_handler,         commands=['system'],        pass_bot=True)
    bot.register_message_handler(handlers.system_prompt_clear_handler,   commands=['system_clear'],  pass_bot=True)
    bot.register_message_handler(handlers.system_prompt_reset_handler,   commands=['system_reset'],  pass_bot=True)
    bot.register_message_handler(handlers.system_prompt_show_handler,    commands=['system_show'],   pass_bot=True)
    bot.register_message_handler(handlers.api_key_add_handler,           commands=['api_add'],       pass_bot=True)
    bot.register_message_handler(handlers.api_key_remove_handler,        commands=['api_remove'],    pass_bot=True)
    bot.register_message_handler(handlers.api_key_list_handler,          commands=['api_list'],      pass_bot=True)
    bot.register_message_handler(handlers.api_key_switch_handler,        commands=['api_switch'],    pass_bot=True)
    bot.register_message_handler(handlers.gemini_photo_handler,          content_types=["photo"],    pass_bot=True)
    bot.register_message_handler(
        handlers.gemini_private_handler,
        func=lambda message: message.chat.type == "private",
        content_types=['text'],
        pass_bot=True)

    print("Starting Gemini_Telegram_Bot...")
    await bot.polling(none_stop=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred while running the bot: {e}")
