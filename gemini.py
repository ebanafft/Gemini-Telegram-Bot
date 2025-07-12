import io
import time
import traceback
from PIL import Image
from telebot.types import Message
from md2tgmd import escape
from telebot import TeleBot
from config import conf, generation_config, draw_generation_config, lang_settings, DEFAULT_SYSTEM_PROMPT, safety_settings
from google import genai
from google.genai import types


api_keys = []  # To be populated from main.py
current_api_key_index = 0 

gemini_draw_dict = {}
gemini_chat_dict = {}
gemini_pro_chat_dict = {}
default_model_dict = {}
user_system_prompt_dict = {}  # User system prompts dictionary

model_1                 =       conf["model_1"]
model_2                 =       conf["model_2"]
model_3                 =       conf["model_3"]
default_language        =       conf["default_language"]
error_info              =       conf["error_info"]
before_generate_info    =       conf["before_generate_info"]
download_pic_notify     =       conf["download_pic_notify"]

search_tool = {'google_search': {}}

# Client will be initialized in main.py
client = None

def initialize_client():
    """Initializes the genai client after keys are loaded."""
    global client
    if api_keys:
        try:
            client = genai.Client(api_key=api_keys[current_api_key_index])
            print("Gemini client initialized successfully.")
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")

# API KEY management functions
def get_current_api_key():
    """Get the currently used API key"""
    if not api_keys:
        return None
    return api_keys[current_api_key_index]

def switch_to_next_api_key():
    """Switch to the next available API key"""
    global current_api_key_index, client
    if len(api_keys) <= 1:
        return False
    
    original_index = current_api_key_index
    current_api_key_index = (current_api_key_index + 1) % len(api_keys)
    
    if current_api_key_index == original_index:
        return False
    
    try:
        client = genai.Client(api_key=api_keys[current_api_key_index])
        print(f"Successfully switched to API key #{current_api_key_index}")
        return True
    except Exception as e:
        print(f"Error switching to next API key: {e}")
        return switch_to_next_api_key()

def validate_api_key_format(key):
    """Validate API key format (simple check)"""
    if not key or len(key) < 8:
        return False
    valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-.")
    return all(c in valid_chars for c in key)

def add_api_key(key):
    """Add a new API key"""
    global client
    key = key.strip()
    if not validate_api_key_format(key):
        return False
    if key not in api_keys:
        api_keys.append(key)
        if len(api_keys) == 1:
            try:
                client = genai.Client(api_key=key)
                return True
            except Exception as e:
                print(f"Error initializing client with new API key: {e}")
                api_keys.pop()
                return False
        return True
    return False

def remove_api_key(key):
    """Remove a specified API key"""
    global current_api_key_index, client
    if key in api_keys:
        index = api_keys.index(key)
        api_keys.remove(key)
        if not api_keys:
            current_api_key_index = 0
            client = None
            return True
        if index == current_api_key_index:
            if index >= len(api_keys):
                current_api_key_index = len(api_keys) - 1
            client = genai.Client(api_key=api_keys[current_api_key_index])
        elif index < current_api_key_index:
            current_api_key_index -= 1
        return True
    return False

def list_api_keys():
    """List all API keys (masked)"""
    masked_keys = []
    for i, key in enumerate(api_keys):
        if len(key) > 8:
            visible_part = len(key) // 4
            if visible_part < 2:
                visible_part = 2
            masked_key = key[:visible_part] + "*" * (len(key) - visible_part*2) + key[-visible_part:]
        else:
            masked_key = key[0] + "*" * (max(len(key) - 2, 1)) + (key[-1] if len(key) > 1 else "")
        if i == current_api_key_index:
            masked_key = f"[Current] {masked_key}"
        masked_keys.append(masked_key)
    return masked_keys

def set_current_api_key(index):
    """Set the current API key by index"""
    global current_api_key_index, client
    if 0 <= index < len(api_keys):
        try:
            old_index = current_api_key_index
            test_client = genai.Client(api_key=api_keys[index])
            current_api_key_index = index
            client = test_client
            return True
        except Exception as e:
            print(f"Error switching to API key at index {index}: {e}")
            return False
    return False

# Since there is only one language, these are simplified
def get_user_lang(user_id):
    return default_language

def get_user_text(user_id, text_key):
    return lang_settings[default_language].get(text_key, "")

# System Prompt Management
def get_system_prompt(user_id):
    return user_system_prompt_dict.get(str(user_id), DEFAULT_SYSTEM_PROMPT)

async def set_system_prompt(bot: TeleBot, message: Message, prompt: str):
    user_id_str = str(message.from_user.id)
    user_system_prompt_dict[user_id_str] = prompt
    if user_id_str in gemini_chat_dict:
        del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict:
        del gemini_pro_chat_dict[user_id_str]
    confirmation_msg = f"{get_user_text(message.from_user.id, 'system_prompt_set')}\n{prompt}"
    await bot.reply_to(message, confirmation_msg)

async def delete_system_prompt(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    if user_id_str in user_system_prompt_dict:
        del user_system_prompt_dict[user_id_str]
    if user_id_str in gemini_chat_dict:
        del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict:
        del gemini_pro_chat_dict[user_id_str]
    await bot.reply_to(message, get_user_text(message.from_user.id, 'system_prompt_deleted'))

async def reset_system_prompt(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    user_system_prompt_dict[user_id_str] = DEFAULT_SYSTEM_PROMPT
    if user_id_str in gemini_chat_dict:
        del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict:
        del gemini_pro_chat_dict[user_id_str]
    await bot.reply_to(message, get_user_text(message.from_user.id, 'system_prompt_reset'))

async def show_system_prompt(bot: TeleBot, message: Message):
    user_id = message.from_user.id
    prompt = get_system_prompt(user_id)
    await bot.reply_to(message, f"{get_user_text(user_id, 'system_prompt_current')}\n{prompt}")

# Safe message editing
async def safe_edit_message(bot, text, chat_id, message_id, parse_mode=None):
    try:
        kwargs = {"text": text, "chat_id": chat_id, "message_id": message_id}
        if parse_mode:
            kwargs["parse_mode"] = parse_mode
        await bot.edit_message_text(**kwargs)
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"Error editing message: {e}")

async def gemini_stream(bot:TeleBot, message:Message, m:str, model_type:str):
    sent_message = None
    try:
        if client is None:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
            return
        sent_message = await bot.reply_to(message, "🤖 Generating answers...")
        chat_dict = gemini_chat_dict if model_type == model_1 else gemini_pro_chat_dict
        if str(message.from_user.id) not in chat_dict:
            system_prompt = get_system_prompt(message.from_user.id)
            try:
                chat = client.aio.chats.create(
                    model=model_type,
                    config=types.GenerateContentConfig(system_instruction=system_prompt, tools=[search_tool])
                )
                chat_dict[str(message.from_user.id)] = chat
            except Exception as e:
                print(f"Failed to set system prompt in chat creation: {e}")
                chat = client.aio.chats.create(
                    model=model_type, 
                    config=types.GenerateContentConfig(tools=[search_tool])
                )
                chat_dict[str(message.from_user.id)] = chat
        else:
            chat = chat_dict[str(message.from_user.id)]

        max_retry_attempts = len(api_keys)
        retry_count = 0
        while retry_count < max_retry_attempts:
            try:
                response = await chat.send_message_stream(m)
                full_response = ""
                last_update = time.time()
                update_interval = conf["streaming_update_interval"]
                async for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        full_response += chunk.text
                        current_time = time.time()
                        if current_time - last_update >= update_interval:
                            try:
                                await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                            except Exception as e:
                                if "parse markdown" in str(e).lower():
                                    await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                                elif "message is not modified" not in str(e).lower():
                                    print(f"Error updating message: {e}")
                            last_update = current_time
                try:
                    await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception as e:
                    if "parse markdown" in str(e).lower():
                        await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                break
            except Exception as e:
                error_str = str(e)
                if (hasattr(e, 'status_code') and e.status_code == 429) or ("429 RESOURCE_EXHAUSTED" in error_str and "You exceeded your current quota" in error_str):
                    if switch_to_next_api_key():
                        try:
                            await safe_edit_message(bot, get_user_text(message.from_user.id, "api_quota_exhausted"), sent_message.chat.id, sent_message.message_id)
                        except Exception: pass
                        system_prompt = get_system_prompt(message.from_user.id)
                        chat = client.aio.chats.create(model=model_type, config=types.GenerateContentConfig(system_instruction=system_prompt, tools=[search_tool]))
                        chat_dict[str(message.from_user.id)] = chat
                        retry_count += 1
                        continue
                    else:
                        await safe_edit_message(bot, f"{error_info}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}", sent_message.chat.id, sent_message.message_id)
                        break
                else:
                    await safe_edit_message(bot, f"{error_info}\nError details: {str(e)}", sent_message.chat.id, sent_message.message_id)
                    break
            retry_count += 1
    except Exception as e:
        if sent_message:
            await safe_edit_message(bot, f"{error_info}\nError details: {str(e)}", sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, f"{error_info}\nError details: {str(e)}")

async def gemini_edit(bot: TeleBot, message: Message, m: str, photo_file: bytes):
    if client is None:
        await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
        return
    sent_message = await bot.reply_to(message, download_pic_notify)
    max_retry_attempts = len(api_keys)
    retry_count = 0
    while retry_count < max_retry_attempts:
        try:
            try:
                image = Image.open(io.BytesIO(photo_file))
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG")
                image_bytes = buffer.getvalue()
            except Exception as img_error:
                await safe_edit_message(bot, f"{error_info}\nImage processing error: {str(img_error)}", sent_message.chat.id, sent_message.message_id)
                return
            
            text_part = types.Part.from_text(text=m)
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            
            response = await client.aio.models.generate_content(
                model=model_3,
                contents=[text_part, image_part],
                config=types.GenerateContentConfig(**draw_generation_config)
            )
            
            if not hasattr(response, 'candidates') or not response.candidates:
                await safe_edit_message(bot, f"{error_info}\nNo candidates generated", sent_message.chat.id, sent_message.message_id)
                return
            
            text = ""
            img = None
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text += part.text
                    if hasattr(part, 'inline_data') and part.inline_data:
                        img = part.inline_data.data
            
            if img:
                with io.BytesIO(img) as bio:
                    await bot.send_photo(message.chat.id, bio)
            if text:
                if len(text) > 4000:
                    await bot.send_message(message.chat.id, escape(text[:4000]), parse_mode="MarkdownV2")
                    await bot.send_message(message.chat.id, escape(text[4000:]), parse_mode="MarkdownV2")
                else:
                    await bot.send_message(message.chat.id, escape(text), parse_mode="MarkdownV2")
            
            await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)
            break
            
        except Exception as e:
            error_str = str(e)
            if (hasattr(e, 'status_code') and e.status_code == 429) or ("429 RESOURCE_EXHAUSTED" in error_str and "You exceeded your current quota" in error_str):
                if switch_to_next_api_key():
                    try:
                        await safe_edit_message(bot, get_user_text(message.from_user.id, "api_quota_exhausted"), sent_message.chat.id, sent_message.message_id)
                    except Exception: pass
                    retry_count += 1
                    continue
                else:
                    await safe_edit_message(bot, f"{error_info}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}", sent_message.chat.id, sent_message.message_id)
                    break
            else:
                await safe_edit_message(bot, f"{error_info}\nError details: {str(e)}", sent_message.chat.id, sent_message.message_id)
                break
        retry_count += 1

async def gemini_image_understand(bot: TeleBot, message: Message, photo_file: bytes, prompt: str = ""):
    sent_message = None
    try:
        if client is None:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
            return
            
        sent_message = await bot.reply_to(message, download_pic_notify)

        if not prompt:
            prompt = "Describe this image"

        max_retry_attempts = len(api_keys)
        retry_count = 0
        while retry_count < max_retry_attempts:
            try:
                user_id = str(message.from_user.id)
                is_model_1_default = default_model_dict.get(user_id, True)
                active_chat_dict = gemini_chat_dict if is_model_1_default else gemini_pro_chat_dict
                current_model_name = model_1 if is_model_1_default else model_2
                
                image_obj = Image.open(io.BytesIO(photo_file))
                buffer = io.BytesIO()
                image_obj.save(buffer, format="JPEG")
                image_bytes = buffer.getvalue()

                system_prompt = get_system_prompt(message.from_user.id)
                image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                text_part = types.Part.from_text(text=prompt)
                
                if user_id not in active_chat_dict:
                    try:
                        chat = client.aio.chats.create(
                            model=current_model_name,
                            config=types.GenerateContentConfig(system_instruction=system_prompt, tools=[search_tool])
                        )
                        active_chat_dict[user_id] = chat
                    except Exception as e:
                        print(f"Failed to create chat with system prompt: {e}")
                        chat = client.aio.chats.create(
                            model=current_model_name,
                            config=types.GenerateContentConfig(tools=[search_tool])
                        )
                        active_chat_dict[user_id] = chat
                else:
                    chat = active_chat_dict[user_id]
                
                try:
                    parts = [text_part, image_part]
                    response_stream = await chat.send_message_stream(parts)
                    full_response = ""
                    last_update = time.time()
                    update_interval = conf["streaming_update_interval"]
                    async for chunk in response_stream:
                        if hasattr(chunk, 'text') and chunk.text:
                            full_response += chunk.text
                            current_time = time.time()
                            if current_time - last_update >= update_interval:
                                try:
                                    await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                                except Exception as e_stream:
                                    if "parse markdown" in str(e_stream).lower():
                                        await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                                    elif "message is not modified" not in str(e_stream).lower():
                                        print(f"Image understanding stream update error: {e_stream}")
                                last_update = current_time
                    try:
                        await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                    except Exception:
                        await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                    break
                except Exception as chat_error:
                    print(f"Sending image via chat session failed: {chat_error}. Falling back to direct model call.")
                    response_stream = await client.aio.models.generate_content_stream(
                        model=current_model_name,
                        contents=[text_part, image_part],
                        config=types.GenerateContentConfig(system_instruction=system_prompt, **generation_config)
                    )
                    full_response = ""
                    last_update = time.time()
                    update_interval = conf["streaming_update_interval"]
                    async for chunk in response_stream:
                        if hasattr(chunk, 'text') and chunk.text:
                            full_response += chunk.text
                            current_time = time.time()
                            if current_time - last_update >= update_interval:
                                try:
                                    await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                                except Exception as e_stream:
                                    if "parse markdown" in str(e_stream).lower():
                                        await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                                    elif "message is not modified" not in str(e_stream).lower():
                                        print(f"Image understanding stream update error: {e_stream}")
                                last_update = current_time
                    try:
                        await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                    except Exception:
                        await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                    
                    try:
                        user_content = types.Content.from_parts([text_part, image_part], role="user")
                        model_content = types.Content.from_parts([types.Part.from_text(full_response)], role="model")
                        if not hasattr(chat, 'history'):
                            chat.history = []
                        chat.history.append(user_content)
                        chat.history.append(model_content)
                    except Exception as history_error:
                        print(f"Failed to manually update chat history: {history_error}")
                    break
            except Exception as e:
                error_str = str(e)
                if (hasattr(e, 'status_code') and e.status_code == 429) or ("429 RESOURCE_EXHAUSTED" in error_str and "You exceeded your current quota" in error_str):
                    if switch_to_next_api_key():
                        try:
                            await safe_edit_message(bot, get_user_text(message.from_user.id, "api_quota_exhausted"), sent_message.chat.id, sent_message.message_id)
                        except Exception: pass
                        retry_count += 1
                        continue
                    else:
                        await safe_edit_message(bot, f"{error_info}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}", sent_message.chat.id, sent_message.message_id)
                        break
                else:
                    error_message = f"{get_user_text(message.from_user.id, 'error_info')}\nError details: {error_str}"
                    if sent_message:
                        await safe_edit_message(bot, error_message, sent_message.chat.id, sent_message.message_id)
                    else:
                        await bot.reply_to(message, error_message)
                    break
            retry_count += 1
    except Exception as e:
        if sent_message:
            await safe_edit_message(bot, f"{error_info}\nError details: {str(e)}", sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, f"{error_info}\nError details: {str(e)}")

async def gemini_draw(bot:TeleBot, message:Message, m:str):
    sent_message = None
    try:
        if client is None:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
            return
            
        sent_message = await bot.reply_to(message, get_user_text(message.from_user.id, "drawing_message"))
            
        max_retry_attempts = len(api_keys)
        retry_count = 0
        while retry_count < max_retry_attempts:
            try:
                response = await client.aio.models.generate_content(
                    model=model_3,
                    contents=m,
                    config=types.GenerateContentConfig(**draw_generation_config)
                )
                
                if not hasattr(response, 'candidates') or not response.candidates:
                    error_msg = get_user_text(message.from_user.id, "error_info")
                    await safe_edit_message(bot, f"{error_msg}\nNo candidates generated", sent_message.chat.id, sent_message.message_id)
                    break
                
                text = ""
                img = None
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text += part.text
                        if hasattr(part, 'inline_data') and part.inline_data:
                            img = part.inline_data.data
                
                if img:
                    with io.BytesIO(img) as bio:
                        await bot.send_photo(message.chat.id, bio)
                if text:
                    if len(text) > 4000:
                        await bot.send_message(message.chat.id, escape(text[:4000]), parse_mode="MarkdownV2")
                        await bot.send_message(message.chat.id, escape(text[4000:]), parse_mode="MarkdownV2")
                    else:
                        await bot.send_message(message.chat.id, escape(text), parse_mode="MarkdownV2")
                
                try:
                    await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)
                except Exception: pass
                break
                
            except Exception as e:
                error_str = str(e)
                if (hasattr(e, 'status_code') and e.status_code == 429) or ("429 RESOURCE_EXHAUSTED" in error_str and "You exceeded your current quota" in error_str):
                    if switch_to_next_api_key():
                        try:
                            await safe_edit_message(bot, get_user_text(message.from_user.id, "api_quota_exhausted"), sent_message.chat.id, sent_message.message_id)
                        except Exception: pass
                        retry_count += 1
                        continue
                    else:
                        error_msg = get_user_text(message.from_user.id, "error_info")
                        await safe_edit_message(bot, f"{error_msg}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}", sent_message.chat.id, sent_message.message_id)
                        break
                else:
                    error_msg = get_user_text(message.from_user.id, "error_info")
                    await safe_edit_message(bot, f"{error_msg}\nError details: {str(e)}", sent_message.chat.id, sent_message.message_id)
                    break
            retry_count += 1
            
    except Exception as e:
        error_msg = get_user_text(message.from_user.id, "error_info")
        if sent_message:
            await safe_edit_message(bot, f"{error_msg}\nError details: {str(e)}", sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, f"{error_msg}\nError details: {str(e)}")
