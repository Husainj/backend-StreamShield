import os
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import shutil
from pathlib import Path
from typing import Literal, Optional
import logging

from .media_processor import MediaProcessor
from .virtual_camera_service import virtual_camera_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get the current directory path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Default paths
MODEL_PATH = os.path.join(CURRENT_DIR, "best.pt")
DEFAULT_BADWORDS_PATH = os.path.join(CURRENT_DIR, "static", "badwords.txt")

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path(CURRENT_DIR) / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

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
    file: UploadFile = File(...),  # Kept as 'file' to match frontend
    textFile: Optional[UploadFile] = File(default=None),  # Optional text file
    processOption: Literal['blur', 'beep_video', 'beep_audio'] = Form(...)
):
    try:
        logger.info(f"Received file: {file.filename} with option: {processOption}")
        if textFile:
            logger.info(f"Received text file: {textFile.filename}")
        
        # Generate unique filenames
        input_path = UPLOAD_DIR / f"input_{file.filename}"
        output_path = UPLOAD_DIR / f"output_{file.filename}"
        custom_badwords_path = None
        
        # Save uploaded media file
        try:
            with open(input_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info(f"File saved to {input_path}")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
        
        # Save uploaded text file if provided
        if textFile:
            custom_badwords_path = UPLOAD_DIR / f"badwords_{textFile.filename}"
            try:
                with open(custom_badwords_path, "wb") as buffer:
                    shutil.copyfileobj(textFile.file, buffer)
                logger.info(f"Text file saved to {custom_badwords_path}")
            except Exception as e:
                logger.error(f"Error saving text file: {e}")
                cleanup_files(str(input_path))
                raise HTTPException(status_code=500, detail=f"Error saving text file: {str(e)}")
        
        try:
            # Determine which badwords file to use
            badwords_path = str(custom_badwords_path) if custom_badwords_path else DEFAULT_BADWORDS_PATH
            logger.info(f"Using badwords file: {badwords_path}")
            
            # Initialize MediaProcessor with the selected badwords_path
            processor = MediaProcessor(MODEL_PATH, badwords_path)
            
            # Process the media file
            processor.process_media(str(input_path), str(output_path), processOption)
            logger.info(f"File processed successfully: {output_path}")
            
            # Check if output file exists
            if not output_path.exists():
                raise HTTPException(status_code=500, detail="Processing completed but output file not found")
            
            # Schedule cleanup after response is sent
            files_to_cleanup = [str(input_path), str(output_path)]
            if custom_badwords_path:
                files_to_cleanup.append(str(custom_badwords_path))
            background_tasks.add_task(cleanup_files, *files_to_cleanup)
            
            # Return the processed file
            return FileResponse(
                path=output_path,
                media_type=file.content_type,
                filename=f"processed_{file.filename}",
                headers={"Content-Disposition": f"attachment; filename=processed_{file.filename}"}
            )
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            # Clean up files if processing fails
            files_to_cleanup = [str(input_path)]
            if custom_badwords_path:
                files_to_cleanup.append(str(custom_badwords_path))
            cleanup_files(*files_to_cleanup)
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