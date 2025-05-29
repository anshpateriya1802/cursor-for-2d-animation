import os
import shutil
import subprocess
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from .prompt_engine import generate_scene_code
from .utils import extract_scene_class_name
from .error_logging import LogError

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Directories for temporary files and output
GENERATED_DIR = os.path.abspath("temp/generated")
OUTPUT_DIR = os.path.abspath("temp/output")
STATIC_DIR = os.path.abspath("static")

# Start FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create directories if they don't exist
    os.makedirs(GENERATED_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
    yield
    # Don't remove temp directory on shutdown to preserve videos

app = FastAPI(lifespan=lifespan)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],  # Added Streamlit port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input data model
class PromptInput(BaseModel):
    prompt: str  # User's prompt to generate the Manim code
    filename: str  # The filename for the rendered video
    quality: str = "l"  # Quality flag (low by default)

# Quality flag mappings
QUALITY_FLAGS = {
    "l": "-pql",  # Low quality
    "m": "-pqm",  # Medium quality
    "h": "-pqh",  # High quality
}

@app.get("/")
async def root():
    return {"message": "Welcome to the Manim Animation Generator!"}

@app.post("/generate")
async def generate(data: PromptInput):
    try:
        start_time = time.time()
        prompt = data.prompt.strip()
        filename = data.filename.strip().replace(" ", "_")
        quality_flag = QUALITY_FLAGS.get(data.quality.lower(), "-pql")

        # Path for the generated Python file
        scene_path = os.path.join(GENERATED_DIR, f"{filename}.py")

        # Generate the scene code using AI
        print("Generating scene code...")
        scene_code = generate_scene_code(prompt)
        with open(scene_path, "w") as f:
            f.write(scene_code)

        # Extract the scene class name from the generated code
        print("Extracting scene class...")
        scene_class = extract_scene_class_name(scene_path)
        if not scene_class:
            error_message = "Scene class not found"
            error_details = LogError(error_message)
            raise HTTPException(status_code=400, detail=error_details)

        # Run Manim to render the animation
        print("Starting Manim rendering...")
        result = subprocess.run(
            [
                "manim",
                scene_path,
                scene_class,
                quality_flag,
                "-o", filename,
                "--media_dir", OUTPUT_DIR
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for Manim
        )

        if result.returncode != 0:
            error_message = f"Manim failed:\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}"
            print(error_message)
            return JSONResponse(
                {"error": error_message},
                status_code=400
            )

        # Path to the rendered video
        video_path = os.path.join(OUTPUT_DIR, "videos", filename, "480p15", f"{filename}.mp4")
        
        # Wait for video file to be created (up to 30 seconds)
        wait_start = time.time()
        while not os.path.exists(video_path) and time.time() - wait_start < 30:
            time.sleep(1)
            print("Waiting for video file...")

        if not os.path.exists(video_path):
            error_message = "Rendered video not found"
            error_details = LogError(error_message)
            raise HTTPException(status_code=500, detail=error_details)

        # Copy video to static directory for web access
        print("Copying video to static directory...")
        static_video_path = os.path.join(STATIC_DIR, f"{filename}.mp4")
        shutil.copy2(video_path, static_video_path)

        # Clean up generated Python file
        if os.path.exists(scene_path):
            os.remove(scene_path)

        end_time = time.time()
        print(f"Total processing time: {end_time - start_time:.2f} seconds")

        # Return success with video path
        return JSONResponse(
            {
                "message": "✅ Animation created",
                "scene_class": scene_class,
                "video_path": static_video_path
            },
            status_code=200
        )

    except subprocess.TimeoutExpired:
        error_message = "Video generation timed out after 5 minutes"
        error_details = LogError(error_message)
        raise HTTPException(status_code=504, detail=error_details)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error_details = LogError(str(e))
        raise HTTPException(status_code=500, detail=error_details)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
