import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Setup Gemini API
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./it_support.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text, nullable=False)
    retrieved_context = Column(Text, nullable=True)
    ai_response = Column(Text, nullable=True)
    status = Column(String, default="open")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    id = Column(Integer, primary_key=True, index=True)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)

Base.metadata.create_all(bind=engine)

def initialize_kb():
    db = SessionLocal()
    if db.query(KnowledgeBase).count() == 0:
        initial_data = [
            {"problem": "Forgot password", "solution": "Click on 'Forgot Password' on the login screen. You will receive an email to reset it."},
            {"problem": "Network printer not working", "solution": "Restart the printer. Check if it's connected to the same network. Reinstall printer drivers."},
            {"problem": "Blue screen of death (BSOD)", "solution": "Note the error code. Restart the computer. If it persists, boot in safe mode and update drivers."},
            {"problem": "Cannot connect to VPN", "solution": "Check your internet connection. Verify VPN credentials. Try connecting to a different VPN server."},
            {"problem": "Email not syncing", "solution": "Check internet connection. Restart the email client. Verify server settings in the email client."},
            {"problem": "Software installation failing", "solution": "Ensure you have administrator privileges. Check if you have enough disk space. Disable antivirus temporarily."},
            {"problem": "Computer is running slow", "solution": "Close unused applications. Clear browser cache and temp files. Run a malware scan."},
            {"problem": "No audio from speakers", "solution": "Check if speakers are plugged in and turned on. Verify volume is not muted. Update audio drivers."},
            {"problem": "Mouse/Keyboard not responding", "solution": "Reconnect the USB. Try a different USB port. Replace batteries if wireless."},
            {"problem": "Application crashes frequently", "solution": "Update the application to the latest version. Reinstall the application. Check for OS updates."}
        ]
        for item in initial_data:
            kb_entry = KnowledgeBase(problem=item["problem"], solution=item["solution"])
            db.add(kb_entry)
        db.commit()
    db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_kb()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TicketRequest(BaseModel):
    query: str

@app.get("/api/kb")
def get_kb():
    db = SessionLocal()
    kb_items = db.query(KnowledgeBase).all()
    db.close()
    return [{"id": item.id, "problem": item.problem, "solution": item.solution} for item in kb_items]

def retrieve_context(query: str, db) -> str:
    # Simple keyword match
    query_words = set(query.lower().split())
    kb_items = db.query(KnowledgeBase).all()
    best_match = None
    max_matches = 0
    
    for item in kb_items:
        problem_words = set(item.problem.lower().split())
        matches = len(query_words.intersection(problem_words))
        if matches > max_matches:
            max_matches = matches
            best_match = item
            
    if best_match:
        return f"Problem: {best_match.problem}\nSolution: {best_match.solution}"
    return ""

@app.post("/api/ticket")
def create_ticket(request: TicketRequest):
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key is missing. Check .env file.")
        
    db = SessionLocal()
    context = retrieve_context(request.query, db)
    
    # Call Gemini LLM
    try:
        if GOOGLE_API_KEY == "mock_key":
            ai_text = f"Mock AI Response for: {request.query}"
        else:
            model = genai.GenerativeModel('gemini-3.6-flash')
            prompt = f"User query: {request.query}\n"
            if context:
                prompt += f"Context from Knowledge Base:\n{context}\n"
            prompt += "\nPlease provide a helpful and professional IT support response based on the query and context provided."
            
            response = model.generate_content(prompt)
            ai_text = response.text
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    new_ticket = Ticket(
        user_query=request.query,
        retrieved_context=context,
        ai_response=ai_text,
        status="open"
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    db.close()
    
    return {
        "id": new_ticket.id,
        "user_query": new_ticket.user_query,
        "retrieved_context": new_ticket.retrieved_context,
        "ai_response": new_ticket.ai_response,
        "status": new_ticket.status
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
