# 🤖 Telegram Routine Bot

Advanced routine management bot with smart reminders, progress tracking, and remote control features.

## 🚀 Quick Setup

### 1. Get Your Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create new bot: `/newbot`
3. Copy your bot token

### 2. Get Your Chat ID
1. Start your bot
2. Send any message to your bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your chat ID in the response

### 3. Deploy on Free Server

#### Option A: Railway.app (Recommended)
1. Fork this repository
2. Connect to Railway.app
3. Set environment variables:
   - `BOT_TOKEN=your_bot_token`
   - `ADMIN_ID=your_chat_id`
4. Deploy!

#### Option B: Heroku
1. Create Heroku app
2. Set config vars:
   - `BOT_TOKEN=your_bot_token`
   - `ADMIN_ID=your_chat_id`
3. Deploy from GitHub

#### Option C: VPS/Server
```bash
git clone <your-repo>
cd Telegrambot
chmod +x deploy.sh
./deploy.sh
# Update bot.py with your credentials
python3 restart_bot.py
```

## 📱 Remote Control (From Your Phone)

### 🎯 User Commands
- `/start` - Activate bot
- `/menu` - Main menu
- `/status` - Check bot status

### 🔐 Admin Commands (Your Phone Only)
- `/admin` - Full admin panel
- `/emergency` - Emergency controls
- `/health` - System health check

### 🚨 Emergency Features
**All controllable from your Telegram chat:**

#### Instant Controls
- 🔕 **Stop All Reminders** - If bot is spamming
- 🔔 **Enable All Reminders** - Restore normal operation
- 🔧 **Maintenance Mode** - Disable bot for all users
- ✅ **Exit Maintenance** - Restore bot access
- 💾 **Force Backup** - Download all data immediately
- 🔄 **Force Restart** - Restart bot remotely

#### Broadcast System
- Send important messages to all users
- Emergency announcements
- System updates notifications

#### Data Management
- **Auto Backup**: Download complete data anytime
- **Export Data**: Get user data in text format
- **System Stats**: Monitor users, activity, performance

## 🎯 Features

### 📅 Smart Routine Management
- **Sunday Routine**: Complete day schedule
- **Weekday Routine**: Office + study schedule
- **Auto-detection**: Different routines for different days

### ⏰ Smart Reminders
- **Multi-stage alerts**: 15min, 10min, 5min, 2min, 1min before
- **Skip completed**: No reminders for finished tasks
- **Quick actions**: Mark done, snooze, skip from reminder
- **Global control**: Admin can stop/start all reminders

### 📊 Progress Tracking
- **Visual progress bars**: 🟩🟩🟩⬜⬜ 60%
- **Streak counter**: Track consecutive successful days
- **Analytics**: Weekly performance charts
- **Motivational messages**: Based on performance

### 🎮 Gamification
- **Streak system**: Build habits with daily streaks
- **Achievement messages**: Celebrate milestones
- **Progress visualization**: See improvement over time
- **Mood tracking**: Record daily mood

### 🛡️ Reliability Features
- **Auto-restart**: Bot restarts if it crashes
- **Maintenance mode**: Graceful updates
- **Error handling**: Robust error management
- **Data backup**: Automatic data protection

## 📊 System Monitoring

### Health Checks
- **System Status**: Online/maintenance status
- **User Activity**: Active users today
- **File System**: Data file integrity
- **Performance**: Response times, error rates

### Real-time Stats
- Total registered users
- Daily active users
- Total task records
- System uptime

## 🔧 Configuration

### Environment Variables
```bash
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_chat_id
```

### Config File (config.json)
```json
{
  "maintenance_mode": false,
  "emergency_message": "",
  "global_settings": {
    "morning_time": "06:05",
    "night_time": "22:55",
    "reminders_enabled": true
  }
}
```

## 🚨 Emergency Scenarios

### Bot is Spamming
**Solution**: `/emergency` → "Stop All Reminders"

### Need to Update Bot
**Solution**: 
1. `/admin` → "Maintenance Mode ON"
2. Update code on server
3. `/admin` → "Force Restart"
4. `/admin` → "Maintenance Mode OFF"

### Data Backup Needed
**Solution**: `/admin` → "Backup Data"

### Bot Not Responding
**Solution**: `/emergency` → "Force Restart"

### Broadcast Important Message
**Solution**: `/admin` → "Broadcast Message"

## 📱 Mobile-First Design

All admin features work from your phone:
- ✅ **No server access needed**
- ✅ **Telegram-based control**
- ✅ **Instant emergency response**
- ✅ **Real-time monitoring**
- ✅ **One-tap actions**

## 🔒 Security

- **Admin-only controls**: Only your chat ID can access admin features
- **Maintenance mode**: Safe updates without user disruption
- **Data protection**: Automatic backups and error handling
- **Access control**: Different permission levels

## 📈 Scalability

- **Multi-user support**: Unlimited users
- **Data efficiency**: Optimized JSON storage
- **Memory management**: Efficient resource usage
- **Performance monitoring**: Track system health

## 🆘 Support

If you need help:
1. Check `/status` for bot health
2. Use `/health` for detailed diagnostics
3. Try `/emergency` for quick fixes
4. Use maintenance mode for safe updates

**Remember**: All controls work from your Telegram chat - no server access needed! 🎯