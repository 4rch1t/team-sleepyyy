import uvicorn
import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    # Ensure uploads directory exists
    os.makedirs(os.getenv("UPLOAD_FOLDER_PATH", "./uploads"), exist_ok=True)
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
