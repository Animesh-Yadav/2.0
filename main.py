import asyncio
import logging
import json
import os
import threading
import time
import requests
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from flask import Flask

# Flask app for keeping the service alive
app = Flask(__name__)

@app.route('/')
def home():
    return "📚 Question Paper Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "question_paper_bot"}

def run_flask():
    """Run Flask server in background"""
    app.run(host='0.0.0.0', port=8080)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - Using environment variables for security
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7526389597:AAFkqDJ_joxs9rQw7h3khgeWMaxiQt')
ADMIN_USER_ID = int(os.environ.get('ADMIN_USER_ID', '6645404238'))
BASE_URL = os.environ.get('BASE_URL', 'https://doubtsolved.netlify.app/papers')

# Data structure for storing question papers
QUESTION_PAPERS = {
    "6": {
        "Mathematics": {"2023": "class6/math/2023.pdf", "2022": "class6/math/2022.pdf"},
        "Science": {"2023": "class6/science/2023.pdf", "2022": "class6/science/2022.pdf"},
        "English": {"2023": "class6/english/2023.pdf", "2022": "class6/english/2022.pdf"},
        "Hindi": {"2023": "class6/hindi/2023.pdf", "2022": "class6/hindi/2022.pdf"}
    },
    "7": {
        "Mathematics": {"2023": "class7/math/2023.pdf", "2022": "class7/math/2022.pdf"},
        "Science": {"2023": "class7/science/2023.pdf", "2022": "class7/science/2022.pdf"},
        "English": {"2023": "class7/english/2023.pdf", "2022": "class7/english/2022.pdf"},
        "Hindi": {"2023": "class7/hindi/2023.pdf", "2022": "class7/hindi/2022.pdf"}
    },
    "8": {
        "Mathematics": {"2023": "class8/math/2023.pdf", "2022": "class8/math/2022.pdf"},
        "Science": {"2023": "class8/science/2023.pdf", "2022": "class8/science/2022.pdf"},
        "English": {"2023": "class8/english/2023.pdf", "2022": "class8/english/2022.pdf"},
        "Hindi": {"2023": "class8/hindi/2023.pdf", "2022": "class8/hindi/2022.pdf"}
    },
    "9": {
        "Mathematics": {"2023": "class9/math/2023.pdf", "2022": "class9/math/2022.pdf"},
        "Science": {"2023": "class9/science/2023.pdf", "2022": "class9/science/2022.pdf"},
        "English": {"2023": "class9/english/2023.pdf", "2022": "class9/english/2022.pdf"},
        "Hindi": {"2023": "class9/hindi/2023.pdf", "2022": "class9/hindi/2022.pdf"},
        "Social Science": {"2023": "class9/social/2023.pdf", "2022": "class9/social/2022.pdf"}
    },
    "10": {
        "Mathematics": {"2023": "class10/math/2023.pdf", "2022": "class10/math/2022.pdf"},
        "Science": {"2023": "class10/science/2023.pdf", "2022": "class10/science/2022.pdf"},
        "English": {"2023": "class10/english/2023.pdf", "2022": "class10/english/2022.pdf"},
        "Hindi": {"2023": "class10/hindi/2023.pdf", "2022": "class10/hindi/2022.pdf"},
        "Social Science": {"2023": "class10/social/2023.pdf", "2022": "class10/social/2022.pdf"}
    },
    "11": {
        "Mathematics": {"2023": "class11/math/2023.pdf", "2022": "class11/math/2022.pdf"},
        "Physics": {"2023": "class11/physics/2023.pdf", "2022": "class11/physics/2022.pdf"},
        "Chemistry": {"2023": "class11/chemistry/2023.pdf", "2022": "class11/chemistry/2022.pdf"},
        "Biology": {"2023": "class11/biology/2023.pdf", "2022": "class11/biology/2022.pdf"},
        "English": {"2023": "class11/english/2023.pdf", "2022": "class11/english/2022.pdf"},
        "Economics": {"2023": "class11/economics/2023.pdf", "2022": "class11/economics/2022.pdf"}
    },
    "12": {
        "Mathematics": {"2023": "class12/math/2023.pdf", "2022": "class12/math/2022.pdf"},
        "Physics": {"2023": "class12/physics/2023.pdf", "2022": "class12/physics/2022.pdf"},
        "Chemistry": {"2023": "class12/chemistry/2023.pdf", "2022": "class12/chemistry/2022.pdf"},
        "Biology": {"2023": "class12/biology/2023.pdf", "2022": "class12/biology/2022.pdf"},
        "English": {"2023": "class12/english/2023.pdf", "2022": "class12/english/2022.pdf"},
        "Economics": {"2023": "class12/economics/2023.pdf", "2022": "class12/economics/2022.pdf"}
    }
}

# Multi-language support
MESSAGES = {
    "en": {
        "welcome": "🎓 Welcome to Question Paper Bot!\n\nI can help you download previous year question papers for Classes 6-12.\n\nChoose your preferred language:",
        "language_set": "✅ Language set to English\n\nLet's get started! Choose your class:",
        "choose_class": "📚 Choose your class:",
        "choose_subject": "📖 Choose your subject for Class {class_num}:",
        "choose_year": "📅 Choose the year for {subject} - Class {class_num}:",
        "download_link": "📥 Here's your download link:\n\n**{subject} - Class {class_num} ({year})**\n\n🔗 [Download PDF]({url})",
        "paper_not_found": "❌ Sorry, this paper is not available yet.",
        "main_menu": "🏠 Main Menu",
        "back": "⬅️ Back",
        "search": "🔍 Search",
        "search_prompt": "🔍 Enter your search query (e.g., 'Math 2022 Class 10'):",
        "search_results": "🔍 Search Results for '{query}':",
        "no_results": "❌ No results found for '{query}'",
        "admin_panel": "🛠️ Admin Panel",
        "admin_welcome": "🛠️ Admin Panel\n\nChoose an action:",
        "add_paper": "➕ Add Paper",
        "view_papers": "📋 View Papers",
        "unauthorized": "❌ Unauthorized access!",
        "add_paper_format": "To add a new paper, send the details in this format:\n\n`/add_paper Class|Subject|Year|FileURL`\n\nExample:\n`/add_paper 10|Mathematics|2024|class10/math/2024.pdf`",
        "paper_added": "✅ Paper added successfully!\n\nClass: {class_num}\nSubject: {subject}\nYear: {year}",
        "paper_add_error": "❌ Error adding paper. Please check the format."
    },
    "hi": {
        "welcome": "🎓 प्रश्न पत्र बॉट में आपका स्वागत है!\n\nमैं आपको कक्षा 6-12 के पिछले वर्ष के प्रश्न पत्र डाउनलोड करने में मदद कर सकता हूं।\n\nअपनी पसंदीदा भाषा चुनें:",
        "language_set": "✅ भाषा हिंदी में सेट की गई\n\nचलिए शुरू करते हैं! अपनी कक्षा चुनें:",
        "choose_class": "📚 अपनी कक्षा चुनें:",
        "choose_subject": "📖 कक्षा {class_num} के लिए विषय चुनें:",
        "choose_year": "📅 {subject} - कक्षा {class_num} के लिए वर्ष चुनें:",
        "download_link": "📥 यहाँ आपका डाउनलोड लिंक है:\n\n**{subject} - कक्षा {class_num} ({year})**\n\n🔗 [PDF डाउनलोड करें]({url})",
        "paper_not_found": "❌ क्षमा करें, यह प्रश्न पत्र अभी तक उपलब्ध नहीं है।",
        "main_menu": "🏠 मुख्य मेनू",
        "back": "⬅️ वापस",
        "search": "🔍 खोजें",
        "search_prompt": "🔍 अपनी खोज क्वेरी दर्ज करें (जैसे 'गणित 2022 कक्षा 10'):",
        "search_results": "🔍 '{query}' के लिए खोज परिणाम:",
        "no_results": "❌ '{query}' के लिए कोई परिणाम नहीं मिला",
        "admin_panel": "🛠️ एडमिन पैनल",
        "admin_welcome": "🛠️ एडमिन पैनल\n\nकोई कार्य चुनें:",
        "add_paper": "➕ प्रश्न पत्र जोड़ें",
        "view_papers": "📋 प्रश्न पत्र देखें",
        "unauthorized": "❌ अनधिकृत पहुंच!",
        "add_paper_format": "नया प्रश्न पत्र जोड़ने के लिए, इस प्रारूप में विवरण भेजें:\n\n`/add_paper Class|Subject|Year|FileURL`\n\nउदाहरण:\n`/add_paper 10|Mathematics|2024|class10/math/2024.pdf`",
        "paper_added": "✅ प्रश्न पत्र सफलतापूर्वक जोड़ा गया!\n\nकक्षा: {class_num}\nविषय: {subject}\nवर्ष: {year}",
        "paper_add_error": "❌ प्रश्न पत्र जोड़ने में त्रुटि। कृपया प्रारूप जांचें।"
    }
}

# User data storage (in production, use a proper database)
user_data = {}

def get_user_language(user_id: int) -> str:
    return user_data.get(user_id, {}).get('language', 'en')

def set_user_language(user_id: int, language: str):
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['language'] = language

def get_message(user_id: int, key: str, **kwargs) -> str:
    lang = get_user_language(user_id)
    message = MESSAGES[lang].get(key, MESSAGES['en'][key])
    return message.format(**kwargs) if kwargs else message

def keep_alive():
    """Keep the service alive by pinging itself"""
    service_url = os.environ.get('RENDER_EXTERNAL_URL')
    if service_url:
        while True:
            try:
                requests.get(f"{service_url}/health", timeout=10)
                print("🏓 Keep-alive ping sent")
                time.sleep(300)  # Ping every 5 minutes
            except Exception as e:
                print(f"❌ Keep-alive ping failed: {e}")
                time.sleep(60)  # Retry after 1 minute on error

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    print(f"👤 User {username} (ID: {user_id}) started the bot")
    
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇮🇳 हिंदी", callback_data="lang_hi")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        MESSAGES['en']['welcome'],
        reply_markup=reply_markup
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel command"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text(get_message(user_id, "unauthorized"))
        return
    
    print(f"🛠️ Admin {user_id} accessed admin panel")
    
    keyboard = [
        [InlineKeyboardButton(get_message(user_id, "add_paper"), callback_data="admin_add")],
        [InlineKeyboardButton(get_message(user_id, "view_papers"), callback_data="admin_view")],
        [InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        get_message(user_id, "admin_welcome"),
        reply_markup=reply_markup
    )

async def add_paper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new paper command (admin only)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text(get_message(user_id, "unauthorized"))
        return
    
    if len(context.args) == 0:
        await update.message.reply_text(
            get_message(user_id, "add_paper_format"),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        paper_info = " ".join(context.args)
        class_num, subject, year, file_url = paper_info.split("|")
        
        if class_num not in QUESTION_PAPERS:
            QUESTION_PAPERS[class_num] = {}
        if subject not in QUESTION_PAPERS[class_num]:
            QUESTION_PAPERS[class_num][subject] = {}
        
        QUESTION_PAPERS[class_num][subject][year] = file_url
        
        print(f"📄 Paper added: Class {class_num} - {subject} - {year}")
        
        await update.message.reply_text(
            get_message(user_id, "paper_added", class_num=class_num, subject=subject, year=year)
        )
        
    except ValueError:
        await update.message.reply_text(get_message(user_id, "paper_add_error"))

def create_class_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for class selection"""
    keyboard = []
    row = []
    
    for i, class_num in enumerate(sorted(QUESTION_PAPERS.keys())):
        row.append(InlineKeyboardButton(f"Class {class_num}", callback_data=f"class_{class_num}"))
        if (i + 1) % 3 == 0:  # 3 buttons per row
            keyboard.append(row)
            row = []
    
    if row:  # Add remaining buttons
        keyboard.append(row)
    
    # Add search and admin panel buttons
    keyboard.append([InlineKeyboardButton(get_message(user_id, "search"), callback_data="search")])
    
    # Add admin panel button only for admin
    if user_id == ADMIN_USER_ID:
        keyboard.append([InlineKeyboardButton(get_message(user_id, "admin_panel"), callback_data="admin_panel")])
    
    keyboard.append([InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def create_subject_keyboard(user_id: int, class_num: str) -> InlineKeyboardMarkup:
    """Create keyboard for subject selection"""
    keyboard = []
    
    for subject in QUESTION_PAPERS[class_num].keys():
        keyboard.append([InlineKeyboardButton(subject, callback_data=f"subject_{class_num}_{subject}")])
    
    keyboard.append([InlineKeyboardButton(get_message(user_id, "back"), callback_data="back_to_class")])
    keyboard.append([InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def create_year_keyboard(user_id: int, class_num: str, subject: str) -> InlineKeyboardMarkup:
    """Create keyboard for year selection"""
    keyboard = []
    
    years = sorted(QUESTION_PAPERS[class_num][subject].keys(), reverse=True)
    row = []
    
    for i, year in enumerate(years):
        row.append(InlineKeyboardButton(year, callback_data=f"year_{class_num}_{subject}_{year}"))
        if (i + 1) % 3 == 0:  # 3 buttons per row
            keyboard.append(row)
            row = []
    
    if row:  # Add remaining buttons
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(get_message(user_id, "back"), callback_data=f"back_to_subject_{class_num}")])
    keyboard.append([InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    # Language selection
    if data.startswith("lang_"):
        language = data.split("_")[1]
        set_user_language(user_id, language)
        
        keyboard = create_class_keyboard(user_id)
        await query.edit_message_text(
            get_message(user_id, "language_set"),
            reply_markup=keyboard
        )
    
    # Main menu
    elif data == "main_menu":
        keyboard = create_class_keyboard(user_id)
        await query.edit_message_text(
            get_message(user_id, "choose_class"),
            reply_markup=keyboard
        )
    
    # Class selection
    elif data.startswith("class_"):
        class_num = data.split("_")[1]
        keyboard = create_subject_keyboard(user_id, class_num)
        await query.edit_message_text(
            get_message(user_id, "choose_subject", class_num=class_num),
            reply_markup=keyboard
        )
    
    # Subject selection
    elif data.startswith("subject_"):
        parts = data.split("_")
        class_num = parts[1]
        subject = "_".join(parts[2:])  # Handle subjects with underscores
        
        keyboard = create_year_keyboard(user_id, class_num, subject)
        await query.edit_message_text(
            get_message(user_id, "choose_year", subject=subject, class_num=class_num),
            reply_markup=keyboard
        )
    
    # Year selection
    elif data.startswith("year_"):
        parts = data.split("_")
        class_num = parts[1]
        subject = "_".join(parts[2:-1])  # Handle subjects with underscores
        year = parts[-1]
        
        if class_num in QUESTION_PAPERS and subject in QUESTION_PAPERS[class_num] and year in QUESTION_PAPERS[class_num][subject]:
            file_path = QUESTION_PAPERS[class_num][subject][year]
            download_url = f"{BASE_URL}/{file_path}"
            
            await query.edit_message_text(
                get_message(user_id, "download_link", subject=subject, class_num=class_num, year=year, url=download_url),
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")
                ]])
            )
        else:
            await query.edit_message_text(
                get_message(user_id, "paper_not_found"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")
                ]])
            )
    
    # Back navigation
    elif data == "back_to_class":
        keyboard = create_class_keyboard(user_id)
        await query.edit_message_text(
            get_message(user_id, "choose_class"),
            reply_markup=keyboard
        )
    
    elif data.startswith("back_to_subject_"):
        class_num = data.split("_")[-1]
        keyboard = create_subject_keyboard(user_id, class_num)
        await query.edit_message_text(
            get_message(user_id, "choose_subject", class_num=class_num),
            reply_markup=keyboard
        )
    
    # Admin panel callbacks
    elif data == "admin_add":
        if user_id != ADMIN_USER_ID:
            await query.answer("❌ Unauthorized!", show_alert=True)
            return
        
        await query.edit_message_text(
            get_message(user_id, "add_paper_format"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")
            ]])
        )
    
    elif data == "admin_view":
        if user_id != ADMIN_USER_ID:
            await query.answer("❌ Unauthorized!", show_alert=True)
            return
        
        # Generate papers summary
        total_papers = 0
        papers_summary = "📋 **Current Papers Database:**\n\n"
        
        for class_num in sorted(QUESTION_PAPERS.keys()):
            papers_summary += f"**Class {class_num}:**\n"
            for subject, years in QUESTION_PAPERS[class_num].items():
                papers_summary += f"  • {subject}: {len(years)} papers ({', '.join(sorted(years.keys()))})\n"
                total_papers += len(years)
            papers_summary += "\n"
        
        papers_summary += f"**Total Papers: {total_papers}**"
        
        await query.edit_message_text(
            papers_summary,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_message(user_id, "admin_panel"), callback_data="admin_panel")],
                [InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")]
            ])
        )
    
    elif data == "admin_panel":
        if user_id != ADMIN_USER_ID:
            await query.answer("❌ Unauthorized!", show_alert=True)
            return
        
        keyboard = [
            [InlineKeyboardButton(get_message(user_id, "add_paper"), callback_data="admin_add")],
            [InlineKeyboardButton(get_message(user_id, "view_papers"), callback_data="admin_view")],
            [InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            get_message(user_id, "admin_welcome"),
            reply_markup=reply_markup
        )
    
    # Search functionality
    elif data == "search":
        context.user_data['waiting_for_search'] = True
        await query.edit_message_text(
            get_message(user_id, "search_prompt"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")
            ]])
        )

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search queries"""
    user_id = update.effective_user.id
    
    if not context.user_data.get('waiting_for_search'):
        return
    
    context.user_data['waiting_for_search'] = False
    query = update.message.text.lower()
    results = []
    
    # Search through all papers
    for class_num, subjects in QUESTION_PAPERS.items():
        for subject, years in subjects.items():
            for year, file_path in years.items():
                search_text = f"{subject} {year} class {class_num}".lower()
                if any(term in search_text for term in query.split()):
                    results.append({
                        'class': class_num,
                        'subject': subject,
                        'year': year,
                        'file_path': file_path
                    })
    
    if results:
        keyboard = []
        for result in results[:10]:  # Limit to 10 results
            button_text = f"{result['subject']} - Class {result['class']} ({result['year']})"
            callback_data = f"year_{result['class']}_{result['subject']}_{result['year']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")])
        
        await update.message.reply_text(
            get_message(user_id, "search_results", query=query),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            get_message(user_id, "no_results", query=query),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(get_message(user_id, "main_menu"), callback_data="main_menu")
            ]])
        )

def main():
    """Main function to run the bot"""
    try:
        print("🌐 Starting Flask server...")
        # Start Flask in background thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        print("🏓 Starting keep-alive service...")
        # Start keep-alive in background thread
        keep_alive_thread = threading.Thread(target=keep_alive)
        keep_alive_thread.daemon = True
        keep_alive_thread.start()
        
        # Create application
        print("🔧 Creating bot application...")
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        print("📝 Adding command handlers...")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("admin", admin))
        application.add_handler(CommandHandler("add_paper", add_paper))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search))
        
        # Run the bot
        print("🤖 Bot is starting...")
        print("✅ Bot is now running! Send /start to your bot on Telegram to test.")
        print(f"🌐 Flask server running on port 8080")
        print(f"👤 Admin User ID: {ADMIN_USER_ID}")
        print(f"📚 Base URL: {BASE_URL}")
        print("🛑 Press Ctrl+C to stop the bot")
        print("-" * 50)
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("🔍 Please check your BOT_TOKEN and internet connection")

if __name__ == "__main__":
    main()
