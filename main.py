from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import pandas as pd
from datetime import datetime
import os
from database import DatabaseManager
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database manager
# Replace with your SQL Server connection string
#DB_CONNECTION = "mssql+pyodbc://MyUser:Mypassword@MyServer/POWERBI_DB?driver=SQL+Server"
DB_CONNECTION = "mssql+pyodbc://DESKTOP-LKDRID9/ABCD?driver=SQL+Server&trusted_connection=yes"
db_manager = DatabaseManager(DB_CONNECTION)

try:
    
    db_manager = DatabaseManager(DB_CONNECTION)
except Exception as e:
    print(f"Database connection error: {str(e)}")
    db_manager = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        tables = db_manager.get_tables() if db_manager else []
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "tables": tables}
        )
    except Exception as e:
        print(f"Error in home route: {str(e)}")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "tables": [], "error": str(e)}
        )
        
@app.get("/")
async def home(request: Request):
    tables = db_manager.get_tables()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "tables": tables}
    )

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), table_name: str = Form(...)):
    try:
        # Save uploaded file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Upload to database
        db_manager.upload_file_to_table(file_path, table_name)
        
        # Clean up
        os.remove(file_path)
        
        return JSONResponse(content={"message": "File uploaded successfully"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/download/")
async def download_data(table_name: str, start_date: str = None, end_date: str = None, format: str = "csv"):
    try:
        df = db_manager.export_table_data(table_name, start_date, end_date)
        
        # Create temporary file
        temp_file = f"temp_export.{format}"
        if format == "csv":
            df.to_csv(temp_file, index=False)
        else:
            df.to_excel(temp_file, index=False)
        
        response = FileResponse(
            temp_file,
            filename=f"{table_name}_{datetime.now().strftime('%Y%m%d')}.{format}"
        )
        
        return response
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)