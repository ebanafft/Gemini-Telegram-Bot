# Gemini-Telegram-Bot

A powerful Telegram bot based on Google's Gemini AI, featuring model switching, image understanding & generation, and more. It is configured to be private by default but can be made public.

This is a fork of the original project. The original repository can be found here: [https://github.com/laoguodong/Gemini-Telegram-Bot](https://github.com/laoguodong/Gemini-Telegram-Bot)

## ✨ Features

- 💬 **Smart Conversation**: Engage in natural, multi-turn conversations with the Gemini model.
- 🔄 **Model Switching**: Freely switch between different Gemini models.
- 📸 **Image Understanding**: Can recognize and analyze the content of images uploaded by the user.
- 🎨 **AI Drawing**: Generate images from text descriptions.
- ✏️ **Image Editing**: Perform AI-assisted editing on uploaded images.
- 🔑 **API Key Management**: Support for adding, removing, and switching between multiple Gemini API keys.
- 📝 **Custom System Prompts**: Set, modify, and manage custom system prompts.

## 🚀 Installation

This guide explains how to install and run the bot manually.

1.  **Clone the repository**
    ```bash
    git clone https://github.com/laoguodong/Gemini-Telegram-Bot.git
    ```

2.  **Navigate into the project directory**
    ```bash
    cd Gemini-Telegram-Bot
    ```

3.  **Install the required dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create the `.env` configuration file**
    
    Create a file named `.env` in the main directory and add your credentials to it.
    
    ```env
    # Your bot token from @BotFather
    TG_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    
    # Your API key from Google AI Studio (you can add multiple, separated by commas)
    GOOGLE_GEMINI_KEY="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    
    # Your numeric Telegram User ID to make the bot private
    OWNER_ID="123456789"
    ```
    
    **Important Note on `OWNER_ID`:**
    *   To make the bot **private** and respond only to you, set this to your numeric Telegram User ID.
    *   To make the bot **public** and respond to everyone, set `OWNER_ID="-1"`.

5.  **Run the bot**
    
    The script will automatically load the credentials from your `.env` file.
    ```bash
    python main.py
    ```

## 📖 Commands

### Basic Commands

-   `/start` - Start using the bot.
-   `/gemini` - Use the Gemini model.
-   `/gemini_pro` - Use the Gemini Pro model.
-   `/draw` - Use the AI drawing feature.
-   `/edit` - Edit an image.
-   `/clear` - Clear the current conversation history.
-   `/switch` - Switch the default model.

### System Prompt Management

-   `/system` - Set a custom system prompt.
-   `/system_clear` - Delete the custom system prompt.
-   `/system_reset` - Reset the system prompt to the default.
-   `/system_show` - Display the current system prompt.

### API Key Management

-   `/api_add` - Add a new API key.
-   `/api_remove` - Remove an existing API key.
-   `/api_list` - View the list of all API keys.
-   `/api_switch` - Switch the currently active API key.