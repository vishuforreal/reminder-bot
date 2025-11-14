import os
import time
import subprocess
import sys

def restart_bot():
    """Auto-restart script for the bot"""
    while True:
        print("Starting bot...")
        
        # Run the bot
        process = subprocess.Popen([sys.executable, "bot.py"])
        
        # Wait for the process to complete
        process.wait()
        
        # Check if restart flag exists
        if os.path.exists("restart_flag.txt"):
            print("Restart flag detected. Restarting bot...")
            os.remove("restart_flag.txt")
            time.sleep(2)  # Wait 2 seconds before restart
            continue
        else:
            print("Bot stopped normally.")
            break

if __name__ == "__main__":
    restart_bot()