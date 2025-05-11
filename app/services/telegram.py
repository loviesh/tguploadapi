import os
import logging
import aiohttp
import tempfile
from telethon import TelegramClient

from app.config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, PRIVATE_CHANNEL_ID

# Configure logging
logger = logging.getLogger(__name__)

# Define session path within the data directory
SESSION_FILE_PATH = os.path.join("data", "tg_session")

class TelegramService:
    def __init__(self):
        self.client = None
        self.me = None
        self.channel_validated = False
    
    async def start(self):
        """Initialize and start the Telegram client"""
        if self.client:
            logger.info("Telegram client already started")
            return
        
        logger.info("Starting Telegram client")
        
        if not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE]):
            error_msg = "Telegram credentials not found. Please set TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE environment variables."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(SESSION_FILE_PATH), exist_ok=True)
        
        # Initialize client
        self.client = TelegramClient(SESSION_FILE_PATH, TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await self.client.start(phone=TELEGRAM_PHONE)
        
        self.me = await self.client.get_me()
        logger.info(f"Logged in as {self.me.first_name}")
        
        # Validate the channel at startup
        await self._validate_channel(PRIVATE_CHANNEL_ID)
        logger.info("Telegram client started successfully")
    
    async def _validate_channel(self, channel_id):
        """Validate if a channel is accessible by the client"""
        if not channel_id:
            error_msg = "No channel ID provided. Set PRIVATE_CHANNEL_ID in your environment variables."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Convert to int if it's a string
            if isinstance(channel_id, str):
                channel_id = int(channel_id)
                
            # Try to get the entity
            entity = await self.client.get_entity(channel_id)
            logger.info(f"Channel validated: {getattr(entity, 'title', str(entity))}")
            self.channel_validated = True
            return True
        except Exception as e:
            logger.error(f"Channel validation failed: {str(e)}")
            self.channel_validated = False
            raise ValueError(f"Cannot access channel {channel_id}. Please check your PRIVATE_CHANNEL_ID environment variable.")
    
    async def download_file(self, url):
        """Download file from URL"""
        # Use shorter URL in logs
        url_short = url if len(url) < 60 else f"{url[:30]}...{url[-20:]}"
        logger.debug(f"Downloading: {url_short}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Download failed: HTTP {response.status}")
                    raise Exception(f"Failed to download file: HTTP {response.status}")
                
                # Get the filename from URL or headers
                content_disposition = response.headers.get("Content-Disposition", "")
                content_type = response.headers.get("Content-Type", "")
                
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1].strip('"')
                else:
                    filename = url.split("/")[-1]
                    # Make sure filename has an extension
                    if "." not in filename:
                        ext = self._get_extension_from_content_type(content_type)
                        if ext:
                            filename = f"{filename}.{ext}"
                        else:
                            filename = "downloaded_file"
                
                # Extract file extension
                file_ext = os.path.splitext(filename)[1]
                if not file_ext:
                    file_ext = self._get_extension_from_content_type(content_type)
                    if file_ext:
                        file_ext = f".{file_ext}"
                
                # Save file to temp directory with proper extension
                with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
                    content = await response.read()
                    temp_file.write(content)
                    temp_path = temp_file.name
                    
                logger.info(f"Downloaded: {filename} ({len(content)} bytes)")
                
                return temp_path, filename
    
    def _get_extension_from_content_type(self, content_type):
        """Get file extension from content type"""
        content_type = content_type.lower()
        extension = None
        
        if content_type.startswith("image/"):
            extension = content_type.split("/")[1]
        elif content_type == "application/pdf":
            extension = "pdf"
        elif content_type.startswith("video/"):
            extension = content_type.split("/")[1]
        elif content_type.startswith("audio/"):
            extension = content_type.split("/")[1]
        
        return extension
    
    def _get_content_type(self, file_path):
        """Get content type from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        content_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".wmv": "video/x-ms-wmv",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
        }
        
        return content_type_map.get(ext, "application/octet-stream")
    
    def _get_file_type(self, filename):
        """Get file type based on extension"""
        ext = os.path.splitext(filename)[1].lower()
        
        # Image formats
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            return "photo"
        
        # Video formats
        if ext in [".mp4", ".avi", ".mov", ".mkv", ".webm", ".wmv"]:
            return "video"
        
        # Audio formats
        if ext in [".mp3", ".wav", ".ogg", ".m4a", ".flac"]:
            return "audio"
        
        return "document"
    
    async def upload_file_to_channel(self, url, task_id, channel_id=None, force_document=False):
        """Upload file to the private channel for processing by bots"""
        if not self.client:
            await self.start()
        
        try:
            # Use configured channel ID if none provided
            if not channel_id:
                channel_id = PRIVATE_CHANNEL_ID
                
            # Ensure the channel_id is an integer
            if isinstance(channel_id, str):
                channel_id = int(channel_id)
            
            # Check if channel is validated
            if not self.channel_validated:
                raise ValueError(f"Channel {channel_id} was not validated at startup")
            
            # Download the file from URL
            temp_path, filename = await self.download_file(url)
            
            # Determine file type from extension
            file_type = self._get_file_type(filename)
            logger.debug(f"Processing: {filename} (type: {file_type})")
            
            # Caption for all messages
            caption = f"Task ID: {task_id}"
            
            # Send based on file type or force_document setting
            try:
                if force_document:
                    # Always send as document if forced
                    message = await self.client.send_file(
                        channel_id,
                        temp_path,
                        caption=caption,
                        file_name=filename,
                        force_document=True
                    )
                else:
                    # Send based on file type
                    force_doc = file_type == "document"
                    supports_streaming = file_type == "video"
                    
                    message = await self.client.send_file(
                        channel_id,
                        temp_path,
                        caption=caption,
                        force_document=force_doc,
                        supports_streaming=supports_streaming,
                    )
            except Exception as e:
                logger.error(f"Failed to send file: {str(e)}")
                # Try as document as a fallback
                if not force_document:
                    logger.info("Retrying as document")
                    message = await self.client.send_file(
                        channel_id,
                        temp_path,
                        caption=caption,
                        file_name=filename,
                        force_document=True
                    )
                else:
                    # Re-raise the exception if we were already trying as document
                    raise
            
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {str(e)}")
            
            # Return message info
            return {
                "message_id": message.id,
                "channel_id": channel_id,
                "file_type": file_type
            }
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise

# Create a singleton instance
telegram_service = TelegramService() 