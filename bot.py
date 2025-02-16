import pymongo
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Bot Config
API_ID = "22012880"
API_HASH = "5b0e07f5a96d48b704eb9850d274fe1d"
BOT_TOKEN = "8090987232:AAErYh4-Ji5Q1sYn3qV1JKRPrKIxSkrKGVw"
DEVELOPER_LINK = "https://t.me/Axa_bachha"  # Replace with your Telegram profile link
START_IMAGE = "https://envs.sh/Q_x.jpg"  # Replace with an image URL

# MongoDB Setup
MONGO_URI = "mongodb+srv://uramit0001:EZ1u5bfKYZ52XeGT@cluster0.qnbzn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(MONGO_URI)
db = client["AuraDB"]
users_collection = db["Users"]

# Pyrogram Client
app = Client("AuraBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Aura Ranks
RANKS = [
    (9, "Novice"), (29, "Apprentice"), (49, "Skilled"),
    (99, "Expert"), (199, "Master"), (float("inf"), "Grandmaster")
]

def get_rank(aura):
    for limit, rank in RANKS:
        if aura <= limit:
            return rank
    return "Unknown"

# Start Command
@app.on_message(filters.command("start"))
async def start_message(_, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠 Developer", url=DEVELOPER_LINK)],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ])
    
    await message.reply_photo(
        START_IMAGE,
        caption="👋 Welcome to the **Aura Tracker Bot**!\n\nReply with `+1` to increase someone's Aura.\nUse `/level` to check your Aura rank!",
        reply_markup=buttons
    )

# Help Button Callback
@app.on_callback_query(filters.regex("help"))
async def help_callback(_, query: CallbackQuery):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="start")]
    ])
    
    await query.message.edit_text(
        "**❓ Help Menu**\n\n"
        "✅ Reply with `+1` to give someone Aura.\n"
        "✅ Use `/level` to check your rank.\n"
        "✅ Use `/top` to see the leaderboard.\n",
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
        "👋 Welcome to the **Aura Tracker Bot**!\n\nReply with `+1` to increase someone's Aura.\nUse `/level` to check your Aura rank!",
        reply_markup=buttons
    )

# Increase Aura when replying with "+1"
@app.on_message(filters.reply & filters.text)
async def increase_aura(_, message: Message):
    if message.text.strip() == "+1":
        replied_user_id = message.reply_to_message.from_user.id
        replied_user_name = message.reply_to_message.from_user.first_name
        
        user_data = users_collection.find_one({"user_id": replied_user_id})
        new_aura = user_data["aura"] + 1 if user_data else 1
        
        users_collection.update_one(
            {"user_id": replied_user_id},
            {"$set": {"user_id": replied_user_id, "name": replied_user_name, "aura": new_aura}},
            upsert=True
        )
        
        await message.reply_text(f"🔥 {replied_user_name} gained +1 Aura! (Total: {new_aura})")

# Check karma Level
@app.on_message(filters.command("leaderboard"))
async def check_aura(_, message: Message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply_text("You have no Aura yet! Start earning by getting +1s.")
        return
    
    aura = user_data["aura"]
    rank = get_rank(aura)
    await message.reply_text(f"✨ Your Aura: {aura}\n🏆 Rank: {rank}")

# Show Top Aura Holders
@app.on_message(filters.command("top"))
async def show_leaderboard(_, message: Message):
    top_users = list(users_collection.find().sort("karma_points", -1).limit(5))
    
    if not top_users:
        await message.reply_text("No one has earned Karma Points yet!")
        return

    medals = ["🥇", "🥈", "🥉"]  # Emojis for 1st, 2nd, and 3rd place
    leaderboard = ""

    for i, user in enumerate(top_users):
        medal = medals[i] if i < 3 else "🎖️"  # Use a default medal for others
        leaderboard += f"{medal} {user['name']} - {user['karma_points']} Karma Points\n"

    await message.reply_text(f"🏆 **Karma Leaderboard** 🏆\n\n{leaderboard}")

# Run the Bot
app.run()
