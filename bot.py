import os
import json
import asyncio
from datetime import datetime, timedelta, date
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Config
TOKEN = os.getenv("BOT_TOKEN", "7286786180:AAGKuJTdsh-aE1qIBW-r6L3ayWZcXpi3Z8k")
ADMIN_ID = int(os.getenv("ADMIN_ID", "YOUR_CHAT_ID"))  # Replace with your chat ID
TIMEZONE = "Asia/Kolkata"
tz = pytz.timezone(TIMEZONE)
DATA_FILE = "data.json"
CONFIG_FILE = "config.json"
MAINTENANCE_MODE = False

# Routines with exact times
SUNDAY_ROUTINE = [
    ("WAKEUP", "🌅 Wake up + Fresh", "06:00"),
    ("CUET", "📘 CUET Study", "07:00"),
    ("BREAKFAST", "🍽 Breakfast", "09:00"),
    ("STUDY", "📚 Study (Skills)", "10:00"),
    ("ENTERTAINMENT", "🎮 Entertainment", "12:00"),
    ("CUET_REV", "📘 CUET Revision", "14:30"),
    ("PROJECT", "💻 Project Work", "16:00"),
    ("ENJOY", "😌 Enjoy", "18:00"),
    ("SOCIAL_7PM", "👪 Social Time", "19:00"),
    ("DINNER_8PM", "🍽 Dinner", "20:00"),
    ("WEEK_PREP", "📝 Week Preparation", "21:00"),
    ("ENJOY2", "😊 Relax Time", "22:50"),
    ("SLEEP", "🛏 Sleep", "23:30")
]

WEEKDAY_ROUTINE = [
    ("WAKEUP", "🌅 Wake up", "06:00"),
    ("CUET", "🍵 CUET Reasoning", "06:30"),
    ("TRAVEL_CUET", "📘 CUET Travel Revision", "07:00"),
    ("OFFICE", "🏢 Office", "08:00"),
    ("FRESH", "🏠 Fresh", "20:30"),
    ("SOCIAL", "💬 Social Time", "21:00"),
    ("STUDY_BLOCK", "", "21:30"),  # Will be filled based on day
    ("RELAX", "😌 Relax", "22:30"),
    ("PERSONAL", "🔒 Personal/Others", "22:50"),
    ("SLEEP", "🛏 Sleep", "23:30")
]

# Global bot instance
bot_app = None

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "maintenance_mode": False,
            "emergency_message": "",
            "custom_routines": {},
            "global_settings": {
                "morning_time": "06:05",
                "night_time": "22:55",
                "reminders_enabled": True
            }
        }
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def is_admin(user_id):
    return user_id == ADMIN_ID

def backup_data():
    """Create backup of current data"""
    timestamp = datetime.now(tz).strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.json"
    
    data = load_data()
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return backup_file

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def ensure_chat(data, chat_id):
    cid = str(chat_id)
    if cid not in data:
        data[cid] = {
            "registered": True, 
            "records": {}, 
            "pending_extra": None,
            "streak": 0,
            "best_streak": 0,
            "total_score": 0,
            "reminders_enabled": True,
            "snooze_count": {}
        }
    return data[cid]

def get_day_routine(date_obj):
    if date_obj.weekday() == 6:  # Sunday
        return SUNDAY_ROUTINE
    else:
        routine = []
        for key, desc, time in WEEKDAY_ROUTINE:
            if key == "STUDY_BLOCK":
                if date_obj.weekday() in [0, 2, 4]:  # Mon, Wed, Fri
                    routine.append(("CUET_STUDY", "📘 CUET Study", "21:30"))
                else:  # Tue, Thu, Sat
                    routine.append(("SKILL_IMPROVEMENT", "🛠 Skill Improvement", "21:30"))
            else:
                routine.append((key, desc, time))
        return routine

def init_day_record(chat_id, date_str):
    data = load_data()
    chat = ensure_chat(data, chat_id)
    if date_str not in chat["records"]:
        routine = get_day_routine(datetime.strptime(date_str, "%Y-%m-%d").date())
        chat["records"][date_str] = {
            "activities": [k for k, _, _ in routine],
            "descriptions": [f"{desc} ({time})" for _, desc, time in routine],
            "completed": [False] * len(routine),
            "checked_at": [None] * len(routine),
            "extra": None,
            "daily_score": 0,
            "mood": None
        }
        save_data(data)

def calculate_streak(chat_id):
    data = load_data()
    chat = ensure_chat(data, chat_id)
    
    today = datetime.now(tz).date()
    streak = 0
    
    for i in range(30):  # Check last 30 days
        check_date = today - timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        
        if date_str in chat["records"]:
            rec = chat["records"][date_str]
            completed = sum(rec["completed"])
            total = len(rec["activities"])
            
            if completed / total >= 0.7:  # 70% completion
                streak += 1
            else:
                break
        else:
            break
    
    chat["streak"] = streak
    if streak > chat.get("best_streak", 0):
        chat["best_streak"] = streak
    
    save_data(data)
    return streak

def get_progress_bar(completed, total):
    if total == 0:
        return "⬜⬜⬜⬜⬜ 0%"
    
    percentage = (completed / total) * 100
    filled = int(percentage / 20)  # 5 blocks
    empty = 5 - filled
    
    bar = "🟩" * filled + "⬜" * empty
    return f"{bar} {percentage:.0f}%"

def get_motivational_message(percentage):
    if percentage >= 90:
        return "🔥 Outstanding! You're on fire! 🔥"
    elif percentage >= 80:
        return "⭐ Excellent work! Keep it up! ⭐"
    elif percentage >= 70:
        return "👍 Good job! You're doing great! 👍"
    elif percentage >= 50:
        return "💪 Keep pushing! You can do better! 💪"
    else:
        return "🌱 Every step counts! Let's improve! 🌱"

def build_checklist_markup(chat_id, date_str):
    data = load_data()
    chat = ensure_chat(data, chat_id)
    if date_str not in chat["records"]:
        init_day_record(chat_id, date_str)
        data = load_data()
        chat = ensure_chat(data, chat_id)
    
    rec = chat["records"][date_str]
    completed = sum(rec["completed"])
    total = len(rec["activities"])
    
    kb = []
    # Progress bar at top
    progress_bar = get_progress_bar(completed, total)
    kb.append([InlineKeyboardButton(f"📊 Progress: {progress_bar}", callback_data="progress_info")])
    
    for i, desc in enumerate(rec["descriptions"]):
        done = rec["completed"][i]
        label = f"{'✅' if done else '⬜️'} {desc}"
        kb.append([InlineKeyboardButton(label, callback_data=f"toggle|{date_str}|{i}")])
    
    # Bottom buttons
    kb.append([
        InlineKeyboardButton("📊 Summary", callback_data=f"summary|{date_str}"),
        InlineKeyboardButton("🔥 Streak", callback_data="show_streak")
    ])
    kb.append([
        InlineKeyboardButton("😊 Mood", callback_data=f"mood|{date_str}"),
        InlineKeyboardButton("⚙️ Settings", callback_data="settings")
    ])
    
    return InlineKeyboardMarkup(kb)

# Emergency and Admin handlers
async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick status check - available to all users"""
    config = load_config()
    data = load_data()
    
    maintenance_status = "🔧 MAINTENANCE" if config.get("maintenance_mode", False) else "✅ ONLINE"
    reminders_status = "🔔 ON" if config["global_settings"]["reminders_enabled"] else "🔕 OFF"
    
    total_users = len(data)
    server_time = datetime.now(tz).strftime('%H:%M:%S')
    
    status_message = f"""🤖 Bot Status:

🟢 Status: {maintenance_status}
🔔 Reminders: {reminders_status}
👥 Total Users: {total_users}
⏰ Server Time: {server_time}
📅 Date: {datetime.now(tz).strftime('%d %b %Y')}"""
    
    await update.message.reply_text(status_message)

async def health_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed health check - admin only"""
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("❌ Admin only command.")
        return
    
    try:
        data = load_data()
        config = load_config()
        
        # System health metrics
        total_users = len(data)
        active_today = 0
        total_records = 0
        today_str = datetime.now(tz).strftime("%Y-%m-%d")
        
        for chat_id, chat_data in data.items():
            total_records += len(chat_data.get("records", {}))
            if today_str in chat_data.get("records", {}):
                active_today += 1
        
        # File system check
        data_file_exists = os.path.exists(DATA_FILE)
        config_file_exists = os.path.exists(CONFIG_FILE)
        
        health_message = f"""🌡️ System Health Report:

🟢 Core Status: HEALTHY
👥 Total Users: {total_users}
🟢 Active Today: {active_today}
📝 Total Records: {total_records}

💾 Files Status:
  • Data File: {'✅' if data_file_exists else '❌'}
  • Config File: {'✅' if config_file_exists else '❌'}

🔧 Maintenance: {config.get('maintenance_mode', False)}
🔔 Global Reminders: {config['global_settings']['reminders_enabled']}

⏰ Server Time: {datetime.now(tz).strftime('%H:%M:%S')}
📅 Date: {datetime.now(tz).strftime('%d %b %Y')}

🟢 All systems operational!"""
        
        await update.message.reply_text(health_message)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Health check failed: {str(e)}")

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    kb = [
        [InlineKeyboardButton("🔧 Maintenance Mode", callback_data="admin_maintenance")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("💾 Backup Data", callback_data="admin_backup")],
        [InlineKeyboardButton("📊 System Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("⚙️ Update Config", callback_data="admin_config")],
        [InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart")],
        [InlineKeyboardButton("🎆 Emergency Panel", callback_data="emergency_panel")]
    ]
    
    await update.message.reply_text("🔐 Admin Panel:", reply_markup=InlineKeyboardMarkup(kb))

async def emergency_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Emergency command for quick fixes"""
    if not is_admin(update.effective_chat.id):
        return
    
    args = context.args
    if not args:
        kb = [
            [InlineKeyboardButton("🔕 Stop All Reminders", callback_data="emergency_stop_reminders")],
            [InlineKeyboardButton("🔔 Enable All Reminders", callback_data="emergency_enable_reminders")],
            [InlineKeyboardButton("🔧 Maintenance ON", callback_data="emergency_maintenance_on")],
            [InlineKeyboardButton("✅ Maintenance OFF", callback_data="emergency_maintenance_off")],
            [InlineKeyboardButton("💾 Force Backup", callback_data="emergency_backup")],
            [InlineKeyboardButton("🔄 Force Restart", callback_data="emergency_restart")]
        ]
        await update.message.reply_text("🎆 Emergency Control Panel:", reply_markup=InlineKeyboardMarkup(kb))
        return
    
    command = args[0].lower()
    config = load_config()
    
    if command == "stop_reminders":
        config["global_settings"]["reminders_enabled"] = False
        save_config(config)
        await update.message.reply_text("🔕 All reminders stopped globally!")
    
    elif command == "enable_reminders":
        config["global_settings"]["reminders_enabled"] = True
        save_config(config)
        await update.message.reply_text("🔔 All reminders enabled globally!")
    
    elif command == "maintenance_on":
        config["maintenance_mode"] = True
        config["emergency_message"] = "Bot is under maintenance. Please try again later."
        save_config(config)
        await update.message.reply_text("🔧 Maintenance mode activated!")
    
    elif command == "maintenance_off":
        config["maintenance_mode"] = False
        config["emergency_message"] = ""
        save_config(config)
        await update.message.reply_text("✅ Maintenance mode deactivated!")
    
    else:
        await update.message.reply_text("❌ Unknown emergency command.")

# Bot handlers
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    if config.get("maintenance_mode", False):
        await update.message.reply_text(f"🔧 {config.get('emergency_message', 'Bot is under maintenance.')}")
        return
    
    cid = update.effective_chat.id
    data = load_data()
    ensure_chat(data, cid)
    save_data(data)
    await update.message.reply_text("✅ Bot activated! Use /menu for options. You'll receive daily routine and reminders.")

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    if config.get("maintenance_mode", False):
        await update.message.reply_text(f"🔧 {config.get('emergency_message', 'Bot is under maintenance.')}")
        return
    
    cid = update.effective_chat.id
    streak = calculate_streak(cid)
    
    kb = [
        [InlineKeyboardButton("📅 Today's Routine", callback_data="menu_show")],
        [InlineKeyboardButton("📋 Checklist", callback_data="menu_checklist")],
        [InlineKeyboardButton("➕ Add Extra", callback_data="menu_add_extra")],
        [InlineKeyboardButton(f"🔥 Streak: {streak} days", callback_data="show_streak")],
        [InlineKeyboardButton("📈 Analytics", callback_data="analytics")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ]
    
    if is_admin(cid):
        kb.append([InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")])
    
    await update.message.reply_text("🎯 Main Menu:", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cid = q.message.chat_id
    data = load_data()

    if q.data == "menu_show":
        today = datetime.now(tz).date()
        routine = get_day_routine(today)
        lines = [f"📅 Routine for {today.strftime('%A, %d %b')}", ""]
        for i, (_, desc, time) in enumerate(routine, 1):
            lines.append(f"{i}. {desc} ({time})")
        await q.message.reply_text("\n".join(lines))

    elif q.data == "menu_checklist":
        today_str = datetime.now(tz).strftime("%Y-%m-%d")
        init_day_record(cid, today_str)
        markup = build_checklist_markup(cid, today_str)
        await q.message.reply_text("📋 Today's Checklist:", reply_markup=markup)

    elif q.data == "menu_add_extra":
        data = load_data()
        chat = ensure_chat(data, cid)
        chat["pending_extra"] = datetime.now(tz).strftime("%Y-%m-%d")
        save_data(data)
        await q.message.reply_text("Send your extra activity for today:")

    elif q.data.startswith("toggle|"):
        _, date_str, idx = q.data.split("|")
        idx = int(idx)
        chat = ensure_chat(data, cid)
        if date_str not in chat["records"]:
            init_day_record(cid, date_str)
            data = load_data()
            chat = ensure_chat(data, cid)
        
        rec = chat["records"][date_str]
        rec["completed"][idx] = not rec["completed"][idx]
        rec["checked_at"][idx] = datetime.now(tz).isoformat() if rec["completed"][idx] else None
        save_data(data)
        
        try:
            await q.message.edit_reply_markup(build_checklist_markup(cid, date_str))
        except:
            pass

    elif q.data.startswith("summary|"):
        _, date_str = q.data.split("|")
        chat = ensure_chat(data, cid)
        if date_str not in chat["records"]:
            await q.message.reply_text("No data for that date.")
            return
        
        rec = chat["records"][date_str]
        total = len(rec["activities"])
        done = sum(rec["completed"])
        percentage = (done / total) * 100 if total > 0 else 0
        
        lines = [
            f"📅 Summary for {datetime.strptime(date_str, '%Y-%m-%d').strftime('%d %b %Y')}",
            f"📊 Progress: {get_progress_bar(done, total)}",
            get_motivational_message(percentage),
            ""
        ]
        
        for i, (activity, desc, completed, checked_at) in enumerate(zip(rec["activities"], rec["descriptions"], rec["completed"], rec["checked_at"])):
            status = "✅" if completed else "⬜️"
            time_info = f" — {checked_at.split('T')[1][:5]}" if checked_at else ""
            lines.append(f"{status} {desc}{time_info}")
        
        if rec.get("extra"):
            lines.append(f"📝 Extra: {rec['extra']}")
        
        if rec.get("mood"):
            lines.append(f"😊 Mood: {rec['mood']}")
        
        await q.message.reply_text("\n".join(lines))
    
    elif q.data == "show_streak":
        chat = ensure_chat(data, cid)
        streak = calculate_streak(cid)
        best_streak = chat.get("best_streak", 0)
        
        message = f"🔥 Current Streak: {streak} days\n⭐ Best Streak: {best_streak} days\n\n"
        
        if streak >= 7:
            message += "🏆 Amazing! You're building great habits!"
        elif streak >= 3:
            message += "💪 Good momentum! Keep it up!"
        elif streak >= 1:
            message += "🌱 Great start! Every day counts!"
        else:
            message += "🎯 Ready for a fresh start? You got this!"
        
        await q.message.reply_text(message)
    
    elif q.data == "analytics":
        chat = ensure_chat(data, cid)
        today = datetime.now(tz).date()
        
        # Last 7 days analysis
        week_data = []
        for i in range(7):
            date_obj = today - timedelta(days=i)
            date_str = date_obj.strftime("%Y-%m-%d")
            
            if date_str in chat["records"]:
                rec = chat["records"][date_str]
                completed = sum(rec["completed"])
                total = len(rec["activities"])
                percentage = (completed / total) * 100 if total > 0 else 0
                week_data.append((date_obj.strftime("%a"), percentage))
            else:
                week_data.append((date_obj.strftime("%a"), 0))
        
        week_data.reverse()
        avg_performance = sum(p for _, p in week_data) / 7
        
        lines = ["📈 Weekly Analytics:", ""]
        for day, perf in week_data:
            bar = "🟩" * int(perf / 20) + "⬜" * (5 - int(perf / 20))
            lines.append(f"{day}: {bar} {perf:.0f}%")
        
        lines.extend([
            "",
            f"📊 Average Performance: {avg_performance:.1f}%",
            f"🔥 Current Streak: {calculate_streak(cid)} days"
        ])
        
        await q.message.reply_text("\n".join(lines))
    
    elif q.data == "settings":
        chat = ensure_chat(data, cid)
        reminders_status = "🔔 ON" if chat.get("reminders_enabled", True) else "🔕 OFF"
        
        kb = [
            [InlineKeyboardButton(f"Reminders: {reminders_status}", callback_data="toggle_reminders")],
            [InlineKeyboardButton("📊 Export Data", callback_data="export_data")],
            [InlineKeyboardButton("🔄 Reset Streak", callback_data="reset_streak")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_menu")]
        ]
        
        await q.message.reply_text("⚙️ Settings:", reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == "toggle_reminders":
        chat = ensure_chat(data, cid)
        chat["reminders_enabled"] = not chat.get("reminders_enabled", True)
        save_data(data)
        
        status = "enabled" if chat["reminders_enabled"] else "disabled"
        await q.message.reply_text(f"🔔 Reminders {status}!")
    
    elif q.data.startswith("mood|"):
        _, date_str = q.data.split("|")
        kb = [
            [InlineKeyboardButton("😊 Great", callback_data=f"set_mood|{date_str}|Great")],
            [InlineKeyboardButton("😐 Okay", callback_data=f"set_mood|{date_str}|Okay")],
            [InlineKeyboardButton("😔 Not Good", callback_data=f"set_mood|{date_str}|Not Good")]
        ]
        await q.message.reply_text("How was your day?", reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith("set_mood|"):
        _, date_str, mood = q.data.split("|")
        chat = ensure_chat(data, cid)
        
        if date_str not in chat["records"]:
            init_day_record(cid, date_str)
            data = load_data()
            chat = ensure_chat(data, cid)
        
        chat["records"][date_str]["mood"] = mood
        save_data(data)
        
        await q.message.reply_text(f"😊 Mood set to: {mood}")
    
    elif q.data == "back_menu":
        await menu_handler(update, context)
    
    elif q.data == "progress_info":
        today_str = datetime.now(tz).strftime("%Y-%m-%d")
        chat = ensure_chat(data, cid)
        
        if today_str in chat["records"]:
            rec = chat["records"][today_str]
            completed = sum(rec["completed"])
            total = len(rec["activities"])
            percentage = (completed / total) * 100 if total > 0 else 0
            
            message = f"📊 Today's Progress:\n\n{get_progress_bar(completed, total)}\n\n{get_motivational_message(percentage)}"
        else:
            message = "📊 No progress data for today yet. Start checking off tasks!"
        
        await q.message.reply_text(message)
    
    # Admin Panel Handlers
    elif q.data == "admin_panel":
        if not is_admin(cid):
            await q.message.reply_text("❌ Access denied.")
            return
        
        config = load_config()
        maintenance_status = "🔧 ON" if config.get("maintenance_mode", False) else "✅ OFF"
        
        kb = [
            [InlineKeyboardButton(f"Maintenance: {maintenance_status}", callback_data="admin_maintenance")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("💾 Backup", callback_data="admin_backup")],
            [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("⚙️ Config", callback_data="admin_config")],
            [InlineKeyboardButton("🔄 Restart", callback_data="admin_restart")]
        ]
        
        await q.message.reply_text("🔐 Admin Panel:", reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == "admin_maintenance":
        if not is_admin(cid):
            return
        
        config = load_config()
        current_status = config.get("maintenance_mode", False)
        
        kb = [
            [InlineKeyboardButton("🔧 Enable Maintenance", callback_data="maintenance_on")],
            [InlineKeyboardButton("✅ Disable Maintenance", callback_data="maintenance_off")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]
        ]
        
        status_text = "🔧 ENABLED" if current_status else "✅ DISABLED"
        await q.message.reply_text(f"Maintenance Mode: {status_text}", reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == "maintenance_on":
        if not is_admin(cid):
            return
        
        config = load_config()
        config["maintenance_mode"] = True
        config["emergency_message"] = "🔧 Bot is under maintenance. Updates in progress. Please try again later."
        save_config(config)
        
        await q.message.reply_text("🔧 Maintenance mode ENABLED! All users will see maintenance message.")
    
    elif q.data == "maintenance_off":
        if not is_admin(cid):
            return
        
        config = load_config()
        config["maintenance_mode"] = False
        config["emergency_message"] = ""
        save_config(config)
        
        await q.message.reply_text("✅ Maintenance mode DISABLED! Bot is now accessible to all users.")
    
    elif q.data == "admin_broadcast":
        if not is_admin(cid):
            return
        
        data = load_data()
        chat = ensure_chat(data, cid)
        chat["pending_broadcast"] = True
        save_data(data)
        
        await q.message.reply_text("📢 Send your broadcast message:")
    
    elif q.data == "admin_backup":
        if not is_admin(cid):
            return
        
        try:
            backup_file = backup_data()
            
            with open(backup_file, 'rb') as f:
                await bot_app.bot.send_document(chat_id=cid, document=f, filename=backup_file)
            
            os.remove(backup_file)
            await q.message.reply_text("💾 Backup created and sent successfully!")
        except Exception as e:
            await q.message.reply_text(f"❌ Backup failed: {str(e)}")
    
    elif q.data == "admin_stats":
        if not is_admin(cid):
            return
        
        data = load_data()
        total_users = len(data)
        active_today = 0
        total_records = 0
        
        today_str = datetime.now(tz).strftime("%Y-%m-%d")
        
        for chat_id, chat_data in data.items():
            total_records += len(chat_data.get("records", {}))
            if today_str in chat_data.get("records", {}):
                active_today += 1
        
        config = load_config()
        maintenance_status = "🔧 ON" if config.get("maintenance_mode", False) else "✅ OFF"
        
        stats_message = f"""📊 System Statistics:

👥 Total Users: {total_users}
🟢 Active Today: {active_today}
📝 Total Records: {total_records}
🔧 Maintenance: {maintenance_status}
⏰ Server Time: {datetime.now(tz).strftime('%H:%M:%S')}
📅 Date: {datetime.now(tz).strftime('%d %b %Y')}"""
        
        await q.message.reply_text(stats_message)
    
    elif q.data == "admin_config":
        if not is_admin(cid):
            return
        
        config = load_config()
        
        config_text = f"""⚙️ Current Configuration:

🔧 Maintenance: {config.get('maintenance_mode', False)}
🌅 Morning Time: {config['global_settings']['morning_time']}
🌙 Night Time: {config['global_settings']['night_time']}
🔔 Reminders: {config['global_settings']['reminders_enabled']}

To update config, use /emergency command"""
        
        await q.message.reply_text(config_text)
    
    elif q.data == "emergency_panel":
        if not is_admin(cid):
            return
        
        kb = [
            [InlineKeyboardButton("🔕 Stop All Reminders", callback_data="emergency_stop_reminders")],
            [InlineKeyboardButton("🔔 Enable All Reminders", callback_data="emergency_enable_reminders")],
            [InlineKeyboardButton("🔧 Emergency Maintenance", callback_data="emergency_maintenance_on")],
            [InlineKeyboardButton("✅ Exit Maintenance", callback_data="emergency_maintenance_off")],
            [InlineKeyboardButton("💾 Force Backup", callback_data="emergency_backup")],
            [InlineKeyboardButton("🔄 Force Restart", callback_data="emergency_restart")],
            [InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_panel")]
        ]
        
        await q.message.reply_text("🎆 EMERGENCY CONTROL PANEL\n\n⚠️ Use these controls only when needed!", reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == "admin_restart":
        if not is_admin(cid):
            return
        
        kb = [
            [InlineKeyboardButton("🔄 Confirm Restart", callback_data="confirm_restart")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")]
        ]
        
        await q.message.reply_text("⚠️ This will restart the bot. Are you sure?", reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == "confirm_restart":
        if not is_admin(cid):
            return
        
        await q.message.reply_text("🔄 Restarting bot... Please wait.")
        
        # Create restart flag file
        with open("restart_flag.txt", "w") as f:
            f.write("restart")
        
        # Exit the application
        os._exit(0)
    
    # Emergency callback handlers
    elif q.data == "emergency_stop_reminders":
        if not is_admin(cid):
            return
        
        config = load_config()
        config["global_settings"]["reminders_enabled"] = False
        save_config(config)
        await q.message.reply_text("🔕 EMERGENCY: All reminders stopped globally!")
    
    elif q.data == "emergency_enable_reminders":
        if not is_admin(cid):
            return
        
        config = load_config()
        config["global_settings"]["reminders_enabled"] = True
        save_config(config)
        await q.message.reply_text("🔔 All reminders enabled globally!")
    
    elif q.data == "emergency_maintenance_on":
        if not is_admin(cid):
            return
        
        config = load_config()
        config["maintenance_mode"] = True
        config["emergency_message"] = "🔧 Bot is under emergency maintenance. Updates in progress."
        save_config(config)
        await q.message.reply_text("🔧 EMERGENCY: Maintenance mode activated!")
    
    elif q.data == "emergency_maintenance_off":
        if not is_admin(cid):
            return
        
        config = load_config()
        config["maintenance_mode"] = False
        config["emergency_message"] = ""
        save_config(config)
        await q.message.reply_text("✅ Maintenance mode deactivated! Bot is live.")
    
    elif q.data == "emergency_backup":
        if not is_admin(cid):
            return
        
        try:
            backup_file = backup_data()
            
            with open(backup_file, 'rb') as f:
                await bot_app.bot.send_document(chat_id=cid, document=f, filename=backup_file, caption="🎆 Emergency Backup")
            
            os.remove(backup_file)
            await q.message.reply_text("💾 Emergency backup completed!")
        except Exception as e:
            await q.message.reply_text(f"❌ Emergency backup failed: {str(e)}")
    
    elif q.data == "emergency_restart":
        if not is_admin(cid):
            return
        
        kb = [
            [InlineKeyboardButton("🎆 FORCE RESTART", callback_data="force_restart_confirm")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")]
        ]
        
        await q.message.reply_text("⚠️ EMERGENCY RESTART\n\nThis will immediately restart the bot. All current operations will stop.\n\nAre you sure?", reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == "force_restart_confirm":
        if not is_admin(cid):
            return
        
        await q.message.reply_text("🎆 EMERGENCY RESTART INITIATED\n\nBot will restart in 3 seconds...")
        
        # Create restart flag file
        with open("restart_flag.txt", "w") as f:
            f.write("emergency_restart")
        
        # Exit the application
        os._exit(0)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    data = load_data()
    chat = ensure_chat(data, cid)
    
    # Handle broadcast message from admin
    if is_admin(cid) and chat.get("pending_broadcast"):
        broadcast_text = update.message.text
        chat["pending_broadcast"] = False
        save_data(data)
        
        # Send to all users
        success_count = 0
        total_users = len(data)
        
        for chat_id in data.keys():
            try:
                await bot_app.bot.send_message(chat_id=int(chat_id), text=f"📢 Admin Message:\n\n{broadcast_text}")
                success_count += 1
            except:
                pass
        
        await update.message.reply_text(f"📢 Broadcast sent to {success_count}/{total_users} users!")
        return
    
    if chat.get("pending_extra"):
        date_str = chat["pending_extra"]
        extra_text = update.message.text
        
        # Initialize day record if not exists
        init_day_record(cid, date_str)
        data = load_data()
        chat = ensure_chat(data, cid)
        
        # Add extra activity
        rec = chat["records"][date_str]
        rec["extra"] = extra_text
        
        if "EXTRA" not in rec["activities"]:
            rec["activities"].append("EXTRA")
            rec["descriptions"].append(f"📝 Extra: {extra_text}")
            rec["completed"].append(False)
            rec["checked_at"].append(None)
        else:
            idx = rec["activities"].index("EXTRA")
            rec["descriptions"][idx] = f"📝 Extra: {extra_text}"
        
        chat["pending_extra"] = None
        save_data(data)
        await update.message.reply_text(f"✅ Extra activity added: {extra_text}")
    
    elif q.data.startswith("quick_done|"):
        _, activity_key = q.data.split("|")
        today_str = datetime.now(tz).strftime("%Y-%m-%d")
        
        init_day_record(cid, today_str)
        data = load_data()
        chat = ensure_chat(data, cid)
        rec = chat["records"][today_str]
        
        if activity_key in rec["activities"]:
            idx = rec["activities"].index(activity_key)
            rec["completed"][idx] = True
            rec["checked_at"][idx] = datetime.now(tz).isoformat()
            save_data(data)
            
            # Update streak
            calculate_streak(cid)
            
            await q.message.reply_text(f"✅ {rec['descriptions'][idx]} marked as done!")
        else:
            await q.message.reply_text("❌ Activity not found.")
    
    elif q.data.startswith("snooze|"):
        _, activity_key, mins = q.data.split("|")
        chat = ensure_chat(data, cid)
        
        # Track snooze count
        snooze_key = f"{activity_key}_{datetime.now(tz).strftime('%Y-%m-%d')}"
        chat["snooze_count"][snooze_key] = chat["snooze_count"].get(snooze_key, 0) + 1
        
        if chat["snooze_count"][snooze_key] > 3:
            await q.message.reply_text("⚠️ You've snoozed this too many times today. Time to take action!")
        else:
            save_data(data)
            await q.message.reply_text(f"⏰ Snoozed for {mins} minutes. I'll remind you again!")
            
            # Schedule snooze reminder
            snooze_time = datetime.now(tz) + timedelta(minutes=int(mins))
            # Note: In production, you'd want to add this to scheduler
    
    elif q.data.startswith("skip|"):
        _, activity_key = q.data.split("|")
        await q.message.reply_text(f"⏭️ Skipped reminder for today. Focus on other tasks!")
    
    elif q.data == "export_data":
        chat = ensure_chat(data, cid)
        
        # Create simple text export
        lines = ["📊 Your Activity Data Export", "="*30, ""]
        
        for date_str, rec in sorted(chat["records"].items()):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            completed = sum(rec["completed"])
            total = len(rec["activities"])
            
            lines.append(f"{date_obj.strftime('%d %b %Y')}: {completed}/{total} tasks")
            
            if rec.get("extra"):
                lines.append(f"  Extra: {rec['extra']}")
            if rec.get("mood"):
                lines.append(f"  Mood: {rec['mood']}")
            lines.append("")
        
        lines.extend([
            f"Current Streak: {chat.get('streak', 0)} days",
            f"Best Streak: {chat.get('best_streak', 0)} days"
        ])
        
        export_text = "\n".join(lines)
        
        # Send as document
        filename = f"activity_data_{cid}_{datetime.now(tz).strftime('%Y%m%d')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(export_text)
        
        with open(filename, 'rb') as f:
            await bot_app.bot.send_document(chat_id=cid, document=f, filename=filename)
        
        os.remove(filename)
        await q.message.reply_text("📤 Data exported successfully!")
    
    elif q.data == "reset_streak":
        kb = [
            [InlineKeyboardButton("✅ Yes, Reset", callback_data="confirm_reset")],
            [InlineKeyboardButton("❌ Cancel", callback_data="back_menu")]
        ]
        await q.message.reply_text("⚠️ Are you sure you want to reset your streak?", reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == "confirm_reset":
        chat = ensure_chat(data, cid)
        chat["streak"] = 0
        save_data(data)
        await q.message.reply_text("🔄 Streak reset! Fresh start begins now!")

# Scheduled functions
async def send_morning_routine():
    data = load_data()
    today = datetime.now(tz).date()
    routine = get_day_routine(today)
    
    for chat_id in data.keys():
        try:
            cid = int(chat_id)
            chat = data[chat_id]
            streak = calculate_streak(cid)
            
            lines = [
                f"🌅 Good Morning! Day {streak + 1} of your journey",
                f"📅 Routine for {today.strftime('%A, %d %b')}",
                ""
            ]
            
            for i, (_, desc, time) in enumerate(routine, 1):
                lines.append(f"{i}. {desc} ({time})")
            
            if streak > 0:
                lines.extend(["", f"🔥 Current streak: {streak} days - Keep it going!"])
            
            message = "\n".join(lines)
            
            kb = [
                [InlineKeyboardButton("📋 Open Checklist", callback_data="menu_checklist")],
                [InlineKeyboardButton("🎯 Quick Menu", callback_data="back_menu")]
            ]
            
            await bot_app.bot.send_message(
                chat_id=cid, 
                text=message, 
                reply_markup=InlineKeyboardMarkup(kb)
            )
        except:
            pass

async def send_night_checklist():
    data = load_data()
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    
    for chat_id in data.keys():
        try:
            cid = int(chat_id)
            init_day_record(cid, today_str)
            
            # Calculate today's progress
            chat = data[chat_id]
            rec = chat["records"][today_str]
            completed = sum(rec["completed"])
            total = len(rec["activities"])
            percentage = (completed / total) * 100 if total > 0 else 0
            
            message = f"🌙 Day Review Time!\n\n📊 Today's Progress: {get_progress_bar(completed, total)}\n\n{get_motivational_message(percentage)}"
            
            markup = build_checklist_markup(cid, today_str)
            await bot_app.bot.send_message(chat_id=cid, text=message, reply_markup=markup)
        except:
            pass

async def send_weekly_report():
    data = load_data()
    today = datetime.now(tz).date()
    week_start = today - timedelta(days=6)
    
    for chat_id in data.keys():
        try:
            chat = data[chat_id]
            lines = [f"📈 Weekly Report ({week_start.strftime('%d %b')} – {today.strftime('%d %b')})", ""]
            total_tasks = 0
            total_completed = 0
            
            for i in range(7):
                date_obj = week_start + timedelta(days=i)
                date_str = date_obj.strftime("%Y-%m-%d")
                
                if date_str in chat["records"]:
                    rec = chat["records"][date_str]
                    completed = sum(rec["completed"])
                    total = len(rec["activities"])
                    total_tasks += total
                    total_completed += completed
                    
                    extra_info = f"  📝 Extra: {rec['extra']}" if rec.get("extra") else ""
                    lines.append(f"{date_obj.strftime('%d %b')} — {completed}/{total}{extra_info}")
                else:
                    lines.append(f"{date_obj.strftime('%d %b')} — No data")
            
            if total_tasks > 0:
                percentage = (total_completed / total_tasks) * 100
                lines.append(f"\nTotal: {total_completed}/{total_tasks} ({percentage:.1f}%)")
            
            await bot_app.bot.send_message(chat_id=int(chat_id), text="\n".join(lines))
        except:
            pass

async def send_monthly_report():
    data = load_data()
    today = datetime.now(tz).date()
    month_start = today.replace(day=1)
    
    for chat_id in data.keys():
        try:
            chat = data[chat_id]
            
            # Create PDF
            filename = f"monthly_report_{chat_id}_{today.strftime('%Y_%m')}.pdf"
            c = canvas.Canvas(filename, pagesize=A4)
            
            y = 750
            c.drawString(50, y, f"Monthly Report - {today.strftime('%B %Y')}")
            y -= 30
            
            current_date = month_start
            while current_date <= today:
                date_str = current_date.strftime("%Y-%m-%d")
                if date_str in chat["records"]:
                    rec = chat["records"][date_str]
                    completed = sum(rec["completed"])
                    total = len(rec["activities"])
                    extra_info = f"  Extra: {rec['extra']}" if rec.get("extra") else ""
                    
                    line = f"{current_date.strftime('%d %b')} — {completed}/{total}{extra_info}"
                    c.drawString(50, y, line)
                    y -= 20
                    
                    if y < 50:  # New page
                        c.showPage()
                        y = 750
                
                current_date += timedelta(days=1)
            
            c.save()
            
            # Send PDF
            with open(filename, 'rb') as f:
                await bot_app.bot.send_document(chat_id=int(chat_id), document=f, filename=filename)
            
            # Delete file
            os.remove(filename)
        except:
            pass

# Smart Reminder system
async def send_reminder(activity_name, time_left, activity_key):
    # Check global reminders setting
    config = load_config()
    if not config["global_settings"]["reminders_enabled"]:
        return  # Skip all reminders if globally disabled
    
    data = load_data()
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    
    for chat_id in data.keys():
        try:
            chat = data[chat_id]
            
            # Skip if user reminders disabled
            if not chat.get("reminders_enabled", True):
                continue
            
            # Check if activity already completed
            if today_str in chat["records"]:
                rec = chat["records"][today_str]
                if activity_key in rec["activities"]:
                    idx = rec["activities"].index(activity_key)
                    if rec["completed"][idx]:
                        continue  # Skip reminder if already done
            
            # Smart reminder with quick actions
            kb = [
                [InlineKeyboardButton("✅ Mark Done", callback_data=f"quick_done|{activity_key}")],
                [InlineKeyboardButton("⏰ Snooze 5min", callback_data=f"snooze|{activity_key}|5")],
                [InlineKeyboardButton("🔕 Skip Today", callback_data=f"skip|{activity_key}")]
            ]
            
            message = f"⏰ {time_left} left for {activity_name}"
            await bot_app.bot.send_message(
                chat_id=int(chat_id), 
                text=message, 
                reply_markup=InlineKeyboardMarkup(kb)
            )
        except:
            pass

async def send_time_notification(activity_name, activity_key):
    # Check global reminders setting
    config = load_config()
    if not config["global_settings"]["reminders_enabled"]:
        return  # Skip all notifications if globally disabled
    
    data = load_data()
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    
    for chat_id in data.keys():
        try:
            chat = data[chat_id]
            
            if not chat.get("reminders_enabled", True):
                continue
            
            # Check if already completed
            if today_str in chat["records"]:
                rec = chat["records"][today_str]
                if activity_key in rec["activities"]:
                    idx = rec["activities"].index(activity_key)
                    if rec["completed"][idx]:
                        continue
            
            kb = [
                [InlineKeyboardButton("✅ Start Now", callback_data=f"quick_done|{activity_key}")],
                [InlineKeyboardButton("📋 Open Checklist", callback_data="menu_checklist")]
            ]
            
            message = f"🔔 Time for {activity_name}!"
            await bot_app.bot.send_message(
                chat_id=int(chat_id), 
                text=message, 
                reply_markup=InlineKeyboardMarkup(kb)
            )
        except:
            pass

def setup_reminders(scheduler):
    # Get all unique activities and their times
    all_activities = set()
    
    # Sunday activities
    for activity, desc, time in SUNDAY_ROUTINE:
        all_activities.add((activity, desc, time, 6))  # Sunday = 6
    
    # Weekday activities
    for day in range(6):  # Monday to Saturday
        routine = get_day_routine(date(2024, 1, 1 + day))  # Sample dates for each weekday
        for activity, desc, time in routine:
            all_activities.add((activity, desc, time, day))
    
    # Schedule reminders for each activity
    for activity, desc, time_str, weekday in all_activities:
        hour, minute = map(int, time_str.split(':'))
        
        # Schedule reminders: 15min, 10min, 5min, 2min, 1min before
        for mins_before in [15, 10, 5, 2, 1]:
            reminder_time = datetime.combine(date.today(), datetime.min.time().replace(hour=hour, minute=minute)) - timedelta(minutes=mins_before)
            reminder_hour = reminder_time.hour
            reminder_minute = reminder_time.minute
            
            scheduler.add_job(
                send_reminder,
                CronTrigger(day_of_week=weekday, hour=reminder_hour, minute=reminder_minute, timezone=tz),
                args=[desc, f"{mins_before} min", activity],
                id=f"reminder_{activity}_{weekday}_{mins_before}min"
            )
        
        # Schedule "Time for" notification
        scheduler.add_job(
            send_time_notification,
            CronTrigger(day_of_week=weekday, hour=hour, minute=minute, timezone=tz),
            args=[desc, activity],
            id=f"time_{activity}_{weekday}"
        )

def main():
    global bot_app
    
    # Create bot application
    bot_app = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    bot_app.add_handler(CommandHandler("start", start_handler))
    bot_app.add_handler(CommandHandler("menu", menu_handler))
    bot_app.add_handler(CommandHandler("admin", admin_handler))
    bot_app.add_handler(CommandHandler("emergency", emergency_handler))
    bot_app.add_handler(CommandHandler("status", status_handler))
    bot_app.add_handler(CommandHandler("health", health_handler))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Setup scheduler
    scheduler = AsyncIOScheduler(timezone=tz)
    
    # Daily schedules
    scheduler.add_job(send_morning_routine, CronTrigger(hour=6, minute=5, timezone=tz))
    scheduler.add_job(send_night_checklist, CronTrigger(hour=22, minute=55, timezone=tz))
    scheduler.add_job(send_weekly_report, CronTrigger(day_of_week=6, hour=23, minute=50, timezone=tz))
    scheduler.add_job(send_monthly_report, CronTrigger(day=1, hour=9, minute=0, timezone=tz))
    
    # Setup activity reminders
    setup_reminders(scheduler)
    
    scheduler.start()
    
    # Initialize config
    load_config()
    
    # Run bot
    print("Bot starting...")
    print(f"Admin ID: {ADMIN_ID}")
    bot_app.run_polling()

if __name__ == "__main__":
    main()