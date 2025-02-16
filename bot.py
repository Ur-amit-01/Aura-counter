import time
import asyncio
import pymongo
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand

# Bot Config
API_ID = "22012880"
API_HASH = "5b0e07f5a96d48b704eb9850d274fe1d"
BOT_TOKEN = "8090987232:AAErYh4-Ji5Q1sYn3qV1JKRPrKIxSkrKGVw"
DEVELOPER_LINK = "https://t.me/Axa_bachha"  
START_IMAGE = "https://envs.sh/Q_x.jpg"  

# MongoDB Setup
MONGO_URI = "mongodb+srv://uramit0001:EZ1u5bfKYZ52XeGT@cluster0.qnbzn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
from pymongo import MongoClient
client = pymongo.MongoClient(MONGO_URI)
db = client["KarmaDB"]
users_collection = db["Users"]
countdown_collection = db["countdowns"]

# Pyrogram Client
app = Client("KarmaBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Karma Ranks
RANKS = [
    (9, "Novice"), (29, "Apprentice"), (49, "Skilled"),
    (99, "Expert"), (199, "Master"), (float("inf"), "Grandmaster")
]

def get_rank(karma):
    for limit, rank in RANKS:
        if karma <= limit:
            return rank
    return "Unknown"

# Set Commands Function
async def set_bot_commands():
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("level", "Check your Karma rank"),
        BotCommand("top", "Show group Karma leaderboard"),
        BotCommand("setcountdown", "Set a countdown (Event Name + Time in Seconds)"),
        BotCommand("stopcountdown", "Stop the current countdown"),
    ]
    await app.set_bot_commands(commands)
    print("✅ Bot commands set successfully!")

# Start Command
@app.on_message(filters.command("start"))
async def start_message(_, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠 Developer", url=DEVELOPER_LINK)],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ])
    
    await message.reply_photo(
        START_IMAGE,
        caption="👋 Welcome to **Karma Counter Bot**!\n\nReply with `+1` to increase someone's Karma.\nReply with `-1` to decrease someone's Karma.\nUse `/level` to check your Karma rank!",
        reply_markup=buttons
    )

# Help Button
@app.on_callback_query(filters.regex("help"))
async def help_callback(_, query: CallbackQuery):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="start")]])
    
    await query.message.edit_text(
        "**❓ Help Menu**\n\n"
        "✅ Reply with `+1` to give someone Karma.\n"
        "✅ Reply with `-1` to reduce someone's Karma.\n"
        "✅ Use `/level` to check your rank.\n",
        reply_markup=buttons
    )

# Back to Start Message
@app.on_callback_query(filters.regex("start"))
async def back_to_start(_, query: CallbackQuery):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠 Developer", url=DEVELOPER_LINK)],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ])
    
    await query.message.edit_caption(
        "👋 Welcome to **Karma Counter Bot**!\n\nReply with `+1` to increase someone's Karma.\nReply with `-1` to decrease someone's Karma.\nUse `/level` to check your Karma rank!",
        reply_markup=buttons
    )

# Modify Karma (+1 or -1)
@app.on_message(filters.reply & filters.text)
async def modify_karma(_, message: Message):
    if message.text.strip() not in ["+1", "-1"]:
        return  

    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id
    receiver_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text("❌ You can't modify your own Karma Points!")
        return

    user_data = users_collection.find_one({"user_id": receiver_id})
    current_karma = user_data["karma_points"] if user_data else 0

    karma_change = 1 if message.text.strip() == "+1" else -1
    new_karma = max(0, current_karma + karma_change)  

    action_text = (
        f"🔥 {receiver_name} gained +1 Karma! (Total: {new_karma})" 
        if karma_change > 0 
        else f"💀 {receiver_name} lost 1 Karma! (Total: {new_karma})"
    )

    users_collection.update_one(
        {"user_id": receiver_id},
        {"$set": {"user_id": receiver_id, "name": receiver_name, "karma_points": new_karma}},
        upsert=True
    )

    await message.reply_text(action_text)

# Check Karma Level
@app.on_message(filters.command("level"))
async def check_karma(_, message: Message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply_text("You have no Karma Points yet! Start earning by getting +1s.")
        return
    
    karma = user_data["karma_points"]
    rank = get_rank(karma)
    await message.reply_text(f"✨ Your Karma: {karma}\n🏆 Rank: {rank}")

# Show Top Karma Holders
@app.on_message(filters.command("top") & filters.group)
async def show_leaderboard(_, message: Message):
    chat_id = message.chat.id
    top_users = list(users_collection.find({"chat_id": chat_id}).sort("karma_points", -1).limit(5))
    
    if not top_users:
        await message.reply_text("No one in this group has earned Karma Points yet!")
        return

    medals = ["🥇", "🥈", "🥉"]
    leaderboard = ""

    for i, user in enumerate(top_users):
        medal = medals[i] if i < 3 else "🎖️"
        leaderboard += f"{medal} {user['name']} - {user['karma_points']} Karma Points\n"

    await message.reply_text(f"🏆 **Group Karma Leaderboard** 🏆\n\n{leaderboard}")


###dhhhhhbdjfhbdfjvdfjhvbeuhfvbhjsrvbhierbhusrbchusruhsrvhjsrvhbshjeb


# Format time into days, hours, minutes, seconds
def format_time(seconds):
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

# Countdown Task
async def update_countdown(app, countdown_collection, chat_id, message_id, event_name, end_time):
    while True:
        remaining_time = end_time - int(time.time())
        if remaining_time <= 0:
            await app.edit_message_text(chat_id, message_id, f"⏳ **{event_name}** countdown is over!")
            countdown_collection.delete_one({"chat_id": chat_id})
            break

        formatted_time = format_time(remaining_time)
        try:
            await app.edit_message_text(chat_id, message_id, f"⏳ **{event_name}**\nCountdown: {formatted_time}")
        except:
            break  # Stop updating if message is deleted

        await asyncio.sleep(5)  # Update every 10 seconds

# Start Countdown Command
@app.on_message(filters.command("setcountdown") & filters.group)
async def set_countdown(client: Client, message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply_text("Usage: `/setcountdown Event_Name Time_in_seconds`")
        return

    event_name = args[1]
    try:
        time_in_seconds = int(args[2])
    except ValueError:
        await message.reply_text("❌ Invalid time! Enter time in seconds.")
        return

    chat_id = message.chat.id

    # Check if a countdown already exists in this chat
    existing_countdown = countdown_collection.find_one({"chat_id": chat_id})
    if existing_countdown:
        await message.reply_text("❌ A countdown is already running in this chat! Use `/stopcountdown` to cancel it first.")
        return

    end_time = int(time.time()) + time_in_seconds
    msg = await message.reply_text(f"⏳ **{event_name}** Countdown: `{format_time(time_in_seconds)}`")

    # Store in database
    countdown_collection.insert_one({
        "chat_id": chat_id, "event_name": event_name, "end_time": end_time, "message_id": msg.message_id
    })

    asyncio.create_task(update_countdown(client, countdown_collection, chat_id, msg.message_id, event_name, end_time))

# Stop Countdown Command
@app.on_message(filters.command("stopcountdown") & filters.group)
async def stop_countdown(_, message: Message):
    chat_id = message.chat.id
    countdown = countdown_collection.find_one({"chat_id": chat_id})

    if not countdown:
        await message.reply_text("❌ No active countdown in this chat.")
        return

    countdown_collection.delete_one({"chat_id": chat_id})
    await message.reply_text("✅ Countdown stopped successfully.")

# Resume Countdowns on Bot Restart
async def resume_countdowns(app, countdown_collection):
    countdowns = countdown_collection.find()
    for countdown in countdowns:
        chat_id = countdown["chat_id"]
        message_id = countdown["message_id"]
        event_name = countdown["event_name"]
        end_time = countdown["end_time"]

        remaining_time = end_time - int(time.time())
        if remaining_time > 0:
            asyncio.create_task(update_countdown(app, countdown_collection, chat_id, message_id, event_name, end_time))
        else:
            countdown_collection.delete_one({"chat_id": chat_id})

async def main():
    await app.start()  # Start the bot
    await set_bot_commands()  # Set bot commands
    await resume_countdowns(app, countdown_collection)  # Resume countdowns from database
    await app.idle()  # Keep the bot running

asyncio.run(main())  # Run the bot
