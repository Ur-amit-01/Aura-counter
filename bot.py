
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pyrogram import Client, filters

options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
options.add_argument("--no-sandbox")  
options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# 🔹 Set your bot credentials
API_ID = "22012880"
API_HASH = "5b0e07f5a96d48b704eb9850d274fe1d"
BOT_TOKEN = "8090987232:AAErYh4-Ji5Q1sYn3qV1JKRPrKIxSkrKGVw"

# Initialize the bot
app = Client("TeraboxDownloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to extract direct download link using Selenium
def get_direct_download_link(terabox_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(terabox_url)
        time.sleep(5)  # Wait for the page to load

        # Find the direct download link (Update this if Terabox changes its UI)
        download_button = driver.find_element(By.XPATH, "//a[contains(@class, 'download-button-class')]")  # Update this if necessary
        direct_link = download_button.get_attribute("href")

        driver.quit()
        return direct_link

    except Exception as e:
        driver.quit()
        return f"Error: {str(e)}"

# Function to download file from direct link
def download_file(url, filename="terabox_file"):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return filename
    return None

# Command Handler: Start
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Welcome to **Terabox Downloader Bot**! \n\nSend me a **Terabox link**, and I'll download it for you.")

# Command Handler: Download Terabox Links
@app.on_message(filters.text)
async def terabox_handler(client, message):
    url = message.text.strip()
    
    if "terabox.com" not in url:
        await message.reply_text("❌ Invalid Terabox link! Please send a valid Terabox URL.")
        return

    await message.reply_text("🔍 Extracting download link, please wait...")

    direct_link = get_direct_download_link(url)

    if "Error" in direct_link:
        await message.reply_text(f"⚠️ Failed to extract download link.\n\n**Error:** {direct_link}")
        return

    await message.reply_text(f"✅ **Download Link Extracted!**\n\n🔗 [Click Here]({direct_link}) to download manually.")

    # Download the file
    await message.reply_text("📥 Downloading the file...")

    filename = download_file(direct_link)

    if filename:
        await message.reply_document(filename)
        os.remove(filename)  # Delete file after sending
    else:
        await message.reply_text("❌ Failed to download the file.")

# Run the bot
app.run()
