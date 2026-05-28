from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session
import os

app = FastAPI(
    title="3rdParty Agent Organization API",
    version="0.1.0",
    description="Self-hosted agentic organization management platform"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    print("✅ Database initialized")

@app.get("/")
def root():
    return {"message": "3rdParty Agent Organization API", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)