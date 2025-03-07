import os
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import shutil
from pathlib import Path
from typing import Literal
import logging

from .media_processor import MediaProcessor
from .virtual_camera_service import virtual_camera_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get the current directory path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize paths relative to the StreamShield directory
MODEL_PATH = os.path.join(CURRENT_DIR, "best.pt")
BADWORDS_PATH = os.path.join(CURRENT_DIR, "static", "badwords.txt")

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path(CURRENT_DIR) / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize the media processor
processor = MediaProcessor(MODEL_PATH, BADWORDS_PATH)

def cleanup_files(*files):
    """Clean up temporary files."""
    for file in files:
        try:
            if file and os.path.exists(file):
                os.remove(file)
                logger.info(f"Cleaned up file: {file}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file}: {e}")

@app.post("/process-media")
async def process_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    processOption: Literal['blur', 'beep_video', 'beep_audio'] = Form(...)
):
    try:
        logger.info(f"Received file: {file.filename} with option: {processOption}")
        
        # Generate unique filenames
        input_path = UPLOAD_DIR / f"input_{file.filename}"
        output_path = UPLOAD_DIR / f"output_{file.filename}"
        
        # Save uploaded file
        try:
            with open(input_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info(f"File saved to {input_path}")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
        
        try:
            # Process the media file
            processor.process_media(str(input_path), str(output_path), processOption)
            logger.info(f"File processed successfully: {output_path}")
            
            # Check if output file exists
            if not output_path.exists():
                raise HTTPException(status_code=500, detail="Processing completed but output file not found")
            
            # Schedule cleanup after response is sent
            background_tasks.add_task(cleanup_files, str(input_path), str(output_path))
            
            # Return the processed file
            return FileResponse(
                path=output_path,
                media_type=file.content_type,
                filename=f"processed_{file.filename}",
                headers={"Content-Disposition": f"attachment; filename=processed_{file.filename}"}
            )
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            # Clean up input file if processing fails
            cleanup_files(str(input_path))
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/virtual-camera/start")
async def start_virtual_camera():
    """Start the virtual camera with privacy protection"""
    result = virtual_camera_service.start()
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/virtual-camera/stop")
async def stop_virtual_camera():
    """Stop the virtual camera"""
    result = virtual_camera_service.stop()
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )
