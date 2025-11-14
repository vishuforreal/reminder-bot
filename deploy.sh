#!/bin/bash
# Auto-deployment script for free servers

echo "🚀 Starting Bot Deployment..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set up admin (you'll need to update this with your chat ID)
echo "🔧 Setting up admin..."
echo "IMPORTANT: Update ADMIN_ID in bot.py with your Telegram chat ID"

# Create necessary directories
mkdir -p logs
mkdir -p backups

# Set permissions
chmod +x restart_bot.py
chmod +x bot.py

# Create systemd service file (for VPS)
cat > telegram-bot.service << EOF
[Unit]
Description=Telegram Routine Bot
After=network.target

[Service]
Type=simple
User=\$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 restart_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Deployment setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Update your bot token in bot.py or set BOT_TOKEN environment variable"
echo "2. Get your Telegram chat ID and update ADMIN_ID in bot.py"
echo "3. Run: python3 bot.py (for testing)"
echo "4. Run: python3 restart_bot.py (for production with auto-restart)"
echo ""
echo "🎯 Admin Commands (use from your Telegram):"
echo "  /admin - Full admin panel"
echo "  /emergency - Emergency controls"
echo "  /status - Bot status (available to all)"
echo "  /health - Detailed health check (admin only)"