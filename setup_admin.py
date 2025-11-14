"""
Setup script to configure admin ID
Run this once to set your chat ID as admin
"""

def setup_admin():
    print("🔧 Bot Admin Setup")
    print("=" * 30)
    
    print("\n1. Start your bot first")
    print("2. Send /start to your bot")
    print("3. Send any message to get your chat ID")
    print("4. Copy your chat ID and paste here")
    
    chat_id = input("\nEnter your Chat ID: ").strip()
    
    try:
        chat_id = int(chat_id)
        
        # Update bot.py file
        with open("bot.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace the admin ID line
        old_line = 'ADMIN_ID = int(os.getenv("ADMIN_ID", "YOUR_CHAT_ID"))'
        new_line = f'ADMIN_ID = int(os.getenv("ADMIN_ID", "{chat_id}"))'
        
        content = content.replace(old_line, new_line)
        
        with open("bot.py", "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"\n✅ Admin ID set to: {chat_id}")
        print("🔄 Please restart your bot to apply changes")
        print("\n📋 Admin Commands:")
        print("  /admin - Open admin panel")
        print("  /emergency stop_reminders - Stop all reminders")
        print("  /emergency enable_reminders - Enable all reminders")
        print("  /emergency maintenance_on - Enable maintenance mode")
        print("  /emergency maintenance_off - Disable maintenance mode")
        
    except ValueError:
        print("❌ Invalid chat ID. Please enter numbers only.")

if __name__ == "__main__":
    setup_admin()