import os
import shutil
import mimetypes
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    size = file_path.stat().st_size
    return {
        "filename": file.filename,
        "size": size,
        "download_url": f"/download/{file.filename}"
    }


@app.get("/files")
async def list_files():
    files = []
    for f in UPLOAD_DIR.iterdir():
        if f.is_file() and f.name != ".gitkeep":
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "download_url": f"/download/{f.name}"
            })
    files.sort(key=lambda x: x["name"].lower())
    return files


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if not file_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    mime, _ = mimetypes.guess_type(filename)
    media_type = mime or "application/octet-stream"
    return FileResponse(path=file_path, filename=filename, media_type=media_type)


@app.delete("/delete/{filename}")
async def delete_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not file_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    file_path.unlink()
    return {"message": f"{filename} deleted"}
