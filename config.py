from google.genai import types

# Default system prompt
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant. You should use web search to provide factual and up-to-date information, citing your sources."

lang_settings = {
    "en": {
        "error_info": "⚠️⚠️⚠️\nSomething went wrong!\nPlease try to change your prompt or contact the admin!",
        "before_generate_info": "🤖Generating🤖",
        "download_pic_notify": "🤖Loading picture🤖",
        "welcome_message": "Welcome, you can ask me questions now.\nFor example: `Who is john lennon?`",
        "gemini_prompt_help": "Please add what you want to say after /gemini.\nFor example: `/gemini Who is john lennon?`",
        "gemini_pro_prompt_help": "Please add what you want to say after /gemini_pro.\nFor example: `/gemini_pro Who is john lennon?`",
        "history_cleared": "Your history has been cleared",
        "private_chat_only": "This command is only for private chat!",
        "now_using_model": "Now you are using",
        "send_photo_prompt": "Please send a photo",
        "drawing_message": "Drawing...",
        "draw_prompt_help": "Please add what you want to draw after /draw.\nFor example: `/draw draw me a cat.`",
        "language_switched": "Switched to English",
        "language_current": "Current language: English",
        "system_prompt_current": "Current system prompt: ",
        "system_prompt_set": "System prompt has been set to: ",
        "system_prompt_deleted": "System prompt has been deleted",
        "system_prompt_reset": "System prompt has been reset to default",
        "system_prompt_help": "Please add your system prompt after /system.\nFor example: `/system You are a professional assistant`\nUse /system_clear to delete system prompt\nUse /system_reset to reset to default system prompt\nUse /system_show to view current system prompt",
        "api_key_added": "API key has been added successfully",
        "api_key_already_exists": "API key already exists, not added",
        "api_key_add_help": "Please add your API key after /api_add\nFor example: `/api_add YOUR_API_KEY`\nYou can also add multiple keys at once, separated by commas\nFor example: `/api_add KEY1,KEY2,KEY3`",
        "api_key_removed": "API key has been removed successfully",
        "api_key_not_found": "API key not found",
        "api_key_remove_help": "Please add the API key or its index you want to remove after /api_remove\nFor example: `/api_remove YOUR_API_KEY` or `/api_remove 0`",
        "api_key_list_empty": "No API keys currently. Please use /api_add command to add a key",
        "api_key_list_title": "API key list:",
        "api_key_switched": "Switched to API key",
        "api_key_switch_invalid": "Invalid index",
        "api_key_switch_help": "Please add the index of the API key you want to switch to after /api_switch\nFor example: `/api_switch 0`",
        "api_quota_exhausted": "API key quota exhausted, switching to the next key...",
        "all_api_quota_exhausted": "All API key quotas are exhausted, please try again later or add a new API key.",
        "api_key_invalid_format": "Invalid API key format. The key should have at least 8 characters and contain only letters, numbers, and some special characters.",
        "api_key_invalid": "Invalid API key. The key could not be verified with Google API."
    }
}

conf = {
    "default_language": "en", 
    "model_1": "gemini-2.5-flash",
    "model_2": "gemini-2.5-pro",  
    "model_3": "gemini-2.0-flash-preview-image-generation",  
    "streaming_update_interval": 0.5,  
}


default_lang = conf["default_language"]
conf.update(lang_settings[default_lang])


safety_settings = [
    types.SafetySetting(
        category="HARM_CATEGORY_HARASSMENT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_HATE_SPEECH",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_CIVIC_INTEGRITY",
        threshold="BLOCK_NONE",
    )
]


generation_config = {
    "response_modalities": ['Text'],
    "safety_settings": safety_settings,
}


draw_generation_config = {
    "response_modalities": ['Text', 'IMAGE'],
    "safety_settings": safety_settings,
}
