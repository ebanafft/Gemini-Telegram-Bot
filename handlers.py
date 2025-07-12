import os
from telebot import TeleBot
from telebot.types import Message
from md2tgmd import escape
import traceback
from config import conf
import gemini

from gemini import (
    get_user_text,
    set_system_prompt, delete_system_prompt, reset_system_prompt, show_system_prompt,
    add_api_key, remove_api_key, list_api_keys, set_current_api_key
)

error_info              =       conf["error_info"]
model_1                 =       conf["model_1"]
model_2                 =       conf["model_2"]

gemini_chat_dict        = gemini.gemini_chat_dict
gemini_pro_chat_dict    = gemini.gemini_pro_chat_dict
default_model_dict      = gemini.default_model_dict
gemini_draw_dict        = gemini.gemini_draw_dict

# A helper function to check the owner ID to avoid repetition
def is_owner(message: Message) -> bool:
    OWNER_ID = os.getenv("OWNER_ID")
    return True if OWNER_ID == -1 else str(message.from_user.id) == str(OWNER_ID)

async def start(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    try:
        welcome_msg = get_user_text(message.from_user.id, "welcome_message")
        await bot.reply_to(message, escape(welcome_msg), parse_mode="MarkdownV2")
    except IndexError:
        error_msg = get_user_text(message.from_user.id, "error_info")
        await bot.reply_to(message, error_msg)

async def gemini_stream_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        help_msg = get_user_text(message.from_user.id, "gemini_prompt_help")
        await bot.reply_to(message, escape(help_msg), parse_mode="MarkdownV2")
        return
    await gemini.gemini_stream(bot, message, m, model_1)

async def gemini_pro_stream_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        help_msg = get_user_text(message.from_user.id, "gemini_pro_prompt_help")
        await bot.reply_to(message, escape(help_msg), parse_mode="MarkdownV2")
        return
    await gemini.gemini_stream(bot, message, m, model_2)

async def clear(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    if str(message.from_user.id) in gemini_chat_dict:
        del gemini_chat_dict[str(message.from_user.id)]
    if str(message.from_user.id) in gemini_pro_chat_dict:
        del gemini_pro_chat_dict[str(message.from_user.id)]
    if str(message.from_user.id) in gemini_draw_dict:
        del gemini_draw_dict[str(message.from_user.id)]
    cleared_msg = get_user_text(message.from_user.id, "history_cleared")
    await bot.reply_to(message, cleared_msg)

async def switch(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    if message.chat.type != "private":
        private_chat_msg = get_user_text(message.from_user.id, "private_chat_only")
        await bot.reply_to(message, private_chat_msg)
        return
    user_id_str = str(message.from_user.id)
    if user_id_str not in default_model_dict:
        default_model_dict[user_id_str] = False
        now_using_msg = get_user_text(user_id_str, "now_using_model")
        await bot.reply_to(message, f"{now_using_msg} {model_2}")
        return
    if default_model_dict[user_id_str]:
        default_model_dict[user_id_str] = False
        now_using_msg = get_user_text(user_id_str, "now_using_model")
        await bot.reply_to(message, f"{now_using_msg} {model_2}")
    else:
        default_model_dict[user_id_str] = True
        now_using_msg = get_user_text(user_id_str, "now_using_model")
        await bot.reply_to(message, f"{now_using_msg} {model_1}")

async def gemini_private_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    if message.content_type == 'photo':
        s = message.caption or ""
        try:
            file_path = await bot.get_file(message.photo[-1].file_id)
            photo_file = await bot.download_file(file_path.file_path)
            await gemini.gemini_image_understand(bot, message, photo_file, prompt=s)
        except Exception:
            traceback.print_exc()
            error_msg = get_user_text(message.from_user.id, "error_info")
            await bot.reply_to(message, error_msg)
        return

    m = message.text.strip()
    user_id_str = str(message.from_user.id)
    if user_id_str not in default_model_dict:
        default_model_dict[user_id_str] = True
    
    if default_model_dict[user_id_str]:
        await gemini.gemini_stream(bot, message, m, model_1)
    else:
        await gemini.gemini_stream(bot, message, m, model_2)

async def gemini_photo_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    s = message.caption or ""
    if message.chat.type == "private" and not s.startswith("/"):
        try:
            file_path = await bot.get_file(message.photo[-1].file_id)
            photo_file = await bot.download_file(file_path.file_path)
            await gemini.gemini_image_understand(bot, message, photo_file, prompt=s)
        except Exception:
            traceback.print_exc()
            error_msg = get_user_text(message.from_user.id, "error_info")
            await bot.reply_to(message, error_msg)
        return
    
    if message.chat.type != "private" or s.startswith("/edit"):
        try:
            m = ""
            if s.startswith("/edit"):
                 m = s.strip().split(maxsplit=1)[1].strip() if len(s.strip().split(maxsplit=1)) > 1 else ""
            else:
                 m = s
            file_path = await bot.get_file(message.photo[-1].file_id)
            photo_file = await bot.download_file(file_path.file_path)
            await gemini.gemini_edit(bot, message, m, photo_file)
        except Exception:
            traceback.print_exc()
            error_msg = get_user_text(message.from_user.id, "error_info")
            await bot.reply_to(message, error_msg)

async def gemini_edit_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    if not message.photo:
        photo_prompt_msg = get_user_text(message.from_user.id, "send_photo_prompt")
        await bot.reply_to(message, photo_prompt_msg)
        return
    s = message.caption or ""
    try:
        m = s.strip().split(maxsplit=1)[1].strip() if len(s.strip().split(maxsplit=1)) > 1 else ""
        file_path = await bot.get_file(message.photo[-1].file_id)
        photo_file = await bot.download_file(file_path.file_path)
    except Exception as e:
        traceback.print_exc()
        error_msg = get_user_text(message.from_user.id, "error_info")
        await bot.reply_to(message, f"{error_msg}. Details: {str(e)}")
        return
    await gemini.gemini_edit(bot, message, m, photo_file)

async def draw_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        draw_help_msg = get_user_text(message.from_user.id, "draw_prompt_help")
        await bot.reply_to(message, escape(draw_help_msg), parse_mode="MarkdownV2")
        return
    
    await gemini.gemini_draw(bot, message, m)

async def system_prompt_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    try:
        prompt = message.text.strip().split(maxsplit=1)[1].strip()
        await set_system_prompt(bot, message, prompt)
    except IndexError:
        help_msg = get_user_text(message.from_user.id, "system_prompt_help")
        await bot.reply_to(message, help_msg)

async def system_prompt_clear_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    await delete_system_prompt(bot, message)

async def system_prompt_reset_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    await reset_system_prompt(bot, message)

async def system_prompt_show_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    await show_system_prompt(bot, message)

async def api_key_add_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    if message.chat.type != "private":
        private_chat_msg = get_user_text(message.from_user.id, "private_chat_only")
        await bot.reply_to(message, private_chat_msg)
        return
    try:
        input_text = message.text.strip().split(maxsplit=1)[1].strip()
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except Exception: pass
        
        keys_input = input_text.split(',')
        added_count, existed_count, invalid_count = 0, 0, 0
        
        for api_key in keys_input:
            api_key = api_key.strip()
            if not api_key: continue
            if not gemini.validate_api_key_format(api_key):
                invalid_count += 1
                continue
            if gemini.add_api_key(api_key):
                added_count += 1
            else:
                if api_key in gemini.api_keys:
                    existed_count += 1
                else:
                    invalid_count += 1
        
        response_parts = []
        if added_count > 0:
            response_parts.append(f"Added {added_count} new API key(s)")
        if existed_count > 0:
            response_parts.append(f"{existed_count} key(s) already existed")
        if invalid_count > 0:
            response_parts.append(f"{invalid_count} key(s) had an invalid format or failed validation")
            
        if not response_parts:
            await bot.send_message(message.chat.id, get_user_text(message.from_user.id, "api_key_invalid_format"))
        else:
            await bot.send_message(message.chat.id, "，".join(response_parts))
            
    except IndexError:
        await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_add_help"))

async def api_key_remove_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    if message.chat.type != "private":
        private_chat_msg = get_user_text(message.from_user.id, "private_chat_only")
        await bot.reply_to(message, private_chat_msg)
        return
    try:
        key_or_index = message.text.strip().split(maxsplit=1)[1].strip()
        try:
            index = int(key_or_index)
            if 0 <= index < len(gemini.api_keys):
                real_key = gemini.api_keys[index]
                remove_api_key(real_key)
                await bot.send_message(message.chat.id, f"{get_user_text(message.from_user.id, 'api_key_removed')} (#{index})")
            else:
                await bot.send_message(message.chat.id, get_user_text(message.from_user.id, "api_key_switch_invalid"))
        except ValueError:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            except Exception: pass
            if remove_api_key(key_or_index):
                await bot.send_message(message.chat.id, get_user_text(message.from_user.id, "api_key_removed"))
            else:
                await bot.send_message(message.chat.id, get_user_text(message.from_user.id, "api_key_not_found"))
    except IndexError:
        await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_remove_help"))

async def api_key_list_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    if message.chat.type != "private":
        private_chat_msg = get_user_text(message.from_user.id, "private_chat_only")
        await bot.reply_to(message, private_chat_msg)
        return
    keys = list_api_keys()
    if keys:
        keys_list = "\n".join([f"{i}. {key}" for i, key in enumerate(keys)])
        title = get_user_text(message.from_user.id, "api_key_list_title")
        await bot.send_message(message.chat.id, f"{title}\n{keys_list}")
    else:
        await bot.send_message(message.chat.id, get_user_text(message.from_user.id, "api_key_list_empty"))

async def api_key_switch_handler(message: Message, bot: TeleBot) -> None:
    if not is_owner(message): return
    if message.chat.type != "private":
        private_chat_msg = get_user_text(message.from_user.id, "private_chat_only")
        await bot.reply_to(message, private_chat_msg)
        return
    try:
        index = int(message.text.strip().split(maxsplit=1)[1].strip())
        if set_current_api_key(index):
            if str(message.from_user.id) in gemini_chat_dict:
                del gemini_chat_dict[str(message.from_user.id)]
            if str(message.from_user.id) in gemini_pro_chat_dict:
                del gemini_pro_chat_dict[str(message.from_user.id)]
            if str(message.from_user.id) in gemini_draw_dict:
                del gemini_draw_dict[str(message.from_user.id)]
            keys = list_api_keys()
            current_key = keys[index] if index < len(keys) else "?"
            switched_msg = get_user_text(message.from_user.id, "api_key_switched")
            await bot.send_message(message.chat.id, f"{switched_msg}: {current_key}")
        else:
            await bot.send_message(message.chat.id, get_user_text(message.from_user.id, "api_key_switch_invalid"))
    except (IndexError, ValueError):
        await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_switch_help"))
