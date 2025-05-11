import asyncio
import logging
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.setup import get_db, engine, Base
from app.models.task import Task
from app.models.schemas import UploadRequest, TaskResponse, FileResponse, ProgressResponse
from app.services.telegram import telegram_service

# Create tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Filter out verbose logs
logging.getLogger('telethon').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('uvicorn').setLevel(logging.WARNING)
logging.getLogger('fastapi').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

# Custom filter to show only important logs from app.services.telegram
class TelegramLogFilter(logging.Filter):
    def filter(self, record):
        # Skip dialog/entity listing logs
        if 'Dialog:' in record.getMessage():
            return False
        # Allow important messages from telegram service
        if 'uploaded:' in record.getMessage() or 'completed' in record.getMessage():
            return True
        return False

telegram_logger = logging.getLogger('app.services.telegram')
telegram_logger.addFilter(TelegramLogFilter())

app = FastAPI(
    title="Telegram Upload API",
    description="""
    An API that uploads files from URLs to a Telegram channel.
    
    ## Features
    
    * Upload files to a private Telegram channel by providing a URL
    * Get task status by task ID (with polling)
    
    ## How it works
    
    1. Send a POST request to `/api/upload` with a URL
    2. The service will download the file and upload it to a private Telegram channel
    3. The file is uploaded with the task ID in the caption
    4. You can integrate your own bot to monitor the channel and extract file IDs
    """,
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """Start the Telegram client on application startup"""
    logger.info("=== Starting Telegram Upload API ===")
    try:
        # Start Telegram client
        await telegram_service.start()
        logger.info("API startup complete")
    except Exception as e:
        logger.error(f"Failed to start services: {str(e)}")
    
    logger.info("===============================")

async def process_upload(task_id: str, url: str, db: Session):
    """Process file upload in background"""
    try:
        # Update task status to processing
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.status = "processing"
        db.commit()
        
        # Upload file to Telegram channel
        logger.info(f"Processing: {task_id[:8]}... - {url}")
        
        result = await telegram_service.upload_file_to_channel(url, task_id, force_document=task.force_document)
        
        # Update task with channel message ID and status
        task.channel_message_id = str(result["message_id"])
        task.status = "completed"
        db.commit()
        
        logger.info(f"Completed: {task_id[:8]}... - Message ID: {result['message_id']}")
    except Exception as e:
        # Update task status to failed
        logger.error(f"Failed: {task_id[:8]}... - {str(e)}")
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(e)
            db.commit()

@app.post("/api/upload", response_model=TaskResponse, 
          summary="Upload a file from URL to Telegram channel",
          description="Provide a URL to a file, and the service will download it and upload it to a private Telegram channel. Returns a task ID that can be used to check the status.")
async def upload_file(
    request: UploadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Endpoint to upload a file from URL to Telegram channel"""
    # Create a new task
    task = Task(url=str(request.url), force_document=request.force_document)
    db.add(task)
    db.commit()
    db.refresh(task)
    
    logger.info(f"Created: {task.id[:8]}... - {request.url}")
    
    # Process upload in background
    background_tasks.add_task(process_upload, task.id, str(request.url), db)
    
    return task

@app.get("/api/file/{task_id}", response_model=FileResponse,
         summary="Get file status for a specific task",
         description="Returns the task status and channel message ID when the upload is complete. If the file is not ready, returns status code 425 with current status.")
async def get_file(task_id: str, db: Session = Depends(get_db)):
    """Endpoint to get file status for a specific task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    
    # If task is completed or failed, return result immediately
    if task.status in ["completed", "failed"]:
        return task
    
    # If task is still processing, return 425 status code
    progress_response = ProgressResponse(
        id=task.id, 
        status=task.status, 
        message="File is still being processed"
    )
    raise HTTPException(status_code=425, detail=progress_response.dict()) 