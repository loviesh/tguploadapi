import requests
import time
import os
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API base URL (change this if your API runs on a different URL)
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Telegram bot and channel configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_CHANNEL_ID = int(os.getenv("PRIVATE_CHANNEL_ID", 0))  # Must start with -100

def upload_file(url, force_document=False):
    """Upload a file to Telegram channel from URL"""
    response = requests.post(
        f"{API_URL}/api/upload",
        json={"url": url, "force_document": force_document}
    )
    response.raise_for_status()
    return response.json()

def get_task_status(task_id):
    """Get status for a specific task (with polling)"""
    try:
        response = requests.get(f"{API_URL}/api/file/{task_id}")
        response.raise_for_status()
        return response.json(), None
    except:
        return None, response.json()

class BotHandler:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = int(channel_id)
        self.application = None
        
    async def start(self):
        """Initialize and start the bot"""
        print("Starting bot...")
        self.application = Application.builder().token(self.token).build()
        
        # Add handler for channel posts with files
        self.application.add_handler(
            MessageHandler(
                filters.Chat(chat_id=self.channel_id) & filters.ATTACHMENT,
                self.handle_channel_post
            )
        )
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        print(f"Bot started and is monitoring channel: {self.channel_id}")
        
    async def handle_channel_post(self, update: Update, context: CallbackContext):
        """Handle new messages in the channel"""
        message = update.channel_post or update.message
        
        if not message:
            return
            
        # Check for caption with task ID
        if message.caption and "Task ID:" in message.caption:
            task_id = message.caption.split("Task ID:")[1].strip().split()[0]
            file_id = None
            
            # Get the file ID based on what type of file it is
            if message.document:
                file_id = message.document.file_id
            elif message.photo:
                file_id = message.photo[-1].file_id
            elif message.video:
                file_id = message.video.file_id
            elif message.audio:
                file_id = message.audio.file_id
            elif message.voice:
                file_id = message.voice.file_id
            elif message.video_note:
                file_id = message.video_note.file_id
                
            if file_id:
                print("\n" + "="*50)
                print(f"YAAAAY! Found a file for Task ID: {task_id}")
                print(f"File ID: {file_id}")
                print("="*50 + "\n")
                
                # Here you could store the file_id in your database if needed
        
    async def stop(self):
        """Stop the bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            print("Bot stopped")

async def upload_example():
    """Example function to upload files in various formats"""
    # Example file URLs with different types
    examples = [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1869px-Python-logo-notext.svg.png",
            "description": "PNG Image (as native format)",
            "force_document": False
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1869px-Python-logo-notext.svg.png",
            "description": "PNG Image (forced as document)",
            "force_document": True
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/e/e7/Everest_North_Face_toward_Base_Camp_Tibet_Luca_Galuzzi_2006.jpg",
            "description": "JPEG image (as native format)",
            "force_document": False
        },
        {
            "url": "https://dl.espressif.com/dl/audio/ff-16b-2c-44100hz.mp3",
            "description": "MP3 Audio (as native format)",
            "force_document": False
        },
        {
            "url": "https://dl.espressif.com/dl/audio/ff-16b-2c-44100hz.mp3",
            "description": "MP3 Audio (forced as document)",
            "force_document": True
        },
        {
            "url": "https://filesamples.com/samples/document/pdf/sample3.pdf",
            "description": "PDF document (default is document)",
            "force_document": False
        }
    ]
    
    results = []
    
    for example in examples:
        # Upload file to channel
        print(f"\n{'-'*50}")
        print(f"Uploading: {example['description']} - Force as document: {example['force_document']}")
        
        try:
            task = upload_file(example['url'], force_document=example['force_document'])
            task_id = task["id"]
            print(f"Task created with ID: {task_id}")
            
            # Wait for file to be uploaded
            print(f"Waiting for file to be uploaded...")
            
            retry_count = 0
            max_retries = 20
            success = False
            
            while retry_count < max_retries:
                task_info, progress_info = get_task_status(task_id)
                
                if task_info:
                    # Task has a status
                    if task_info["status"] == "completed":
                        print(f"Upload completed - Message ID: {task_info.get('channel_message_id')}")
                        
                        # Store result for summary
                        results.append({
                            "description": example['description'],
                            "task_id": task_id,
                            "message_id": task_info.get('channel_message_id')
                        })
                        
                        success = True
                        break
                    elif task_info["status"] == "failed":
                        error_message = task_info.get("error_message", "Unknown error")
                        print(f"Upload failed: {error_message}")
                        break
                elif progress_info:
                    # Still processing
                    detail = progress_info.get("detail", {})
                    status = detail.get("status", "unknown")
                    print(f"Status: {status}")
                
                retry_count += 1
                time.sleep(2)
            
            if not success:
                print("Failed: maximum retries reached")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            continue
    
    # Print a summary of all uploads
    print("\n" + "-"*50)
    print("UPLOAD SUMMARY")
    print("-"*50)
    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result['description']} - Task: {result['task_id']} - Message: {result['message_id']}")
    
    print("\nWaiting for file_id extraction from bot...")
    print("="*50)

async def main_async():
    """Main async function that runs both the bot and the upload example"""
    if not BOT_TOKEN or not PRIVATE_CHANNEL_ID:
        print("ERROR: Please set BOT_TOKEN and PRIVATE_CHANNEL_ID environment variables.")
        print("You can add them to your .env file or export them in your shell.")
        return
        
    print("\n== Telegram Upload API Example Bot ==")
    print(f"API URL: {API_URL}")
    print(f"Bot Token: {BOT_TOKEN[:5]}...{BOT_TOKEN[-3:] if len(BOT_TOKEN) > 8 else ''}")
    print(f"Channel ID: {PRIVATE_CHANNEL_ID}")
    print("-"*39 + "\n")
    
    # Start the bot
    bot_handler = BotHandler(BOT_TOKEN, PRIVATE_CHANNEL_ID)
    await bot_handler.start()
    
    try:
        # Run the upload example
        await upload_example()
        
        # Keep the bot running to listen for updates
        print("\nBot is now listening for files in the channel. Press Ctrl+C to stop.")
        
        # Wait indefinitely
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping bot...")
    finally:
        # Stop the bot when we're done
        await bot_handler.stop()

def main():
    """Non-async wrapper for main_async"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main() 