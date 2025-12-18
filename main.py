"""
FastAPI Backend for deNoise - AI News Processing Platform
This API provides endpoints for conversational chat, report generation, and podcast creation.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import os
from datetime import datetime
import io

# Import services
from services.agents_service import AgentsService
from app_settings import PROJECT_ROOT

# Initialize FastAPI app
app = FastAPI(
    title="deNoise API",
    description="AI-powered news processing platform with RAG capabilities",
    version="1.0.0"
)

# CORS Configuration - Adjust origins based on your frontend deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",  # Vue default
        "https://denoise.lovable.app"  # Production URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Agents Service
agents_service = AgentsService(model="gemini-2.5-flash")


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    prompt: str = Field(..., description="User's chat message")
    user_id: str = Field(..., description="Unique user identifier")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI-generated response")
    timestamp: str = Field(..., description="Response timestamp")

class ClearSessionRequest(BaseModel):
    user_id: str = Field(..., description="User ID to clear session for")

class ReportRequest(BaseModel):
    topics: str = Field(..., description="Topics to generate report on")
    time_range: str = Field(..., description="Time range for news articles (e.g., 'weekly', 'monthly')")
    structure: str = Field(default="Introduction, Extensive Summary, Wrap up", description="Report structure type")
    user_id: str = Field(..., description="User identifier")

class ReportResponse(BaseModel):
    report: str = Field(..., description="Generated report content")
    timestamp: str = Field(..., description="Report generation timestamp")

class PodcastRequest(BaseModel):
    topics: str = Field(..., description="Topics for podcast content")
    time_range: str = Field(..., description="Time range for news articles")
    structure: str = Field(default="interview_style", description="Podcast structure/style")
    user_id: str = Field(..., description="User identifier")

class PodcastResponse(BaseModel):
    audio_url: str = Field(..., description="URL to download audio file")
    timestamp: str = Field(..., description="Podcast generation timestamp")

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - Health check"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


# ============================================================================
# 1. CONVERSATIONAL CHAT ENDPOINTS
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Conversational chat endpoint with RAG capabilities.
    Maintains session context per user.
    """
    try:
        response = agents_service.generate_chat_answer(
            prompt=request.prompt,
            user_id=request.user_id
        )
        
        return ChatResponse(
            response=response,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating chat response: {str(e)}"
        )

@app.post("/api/chat/clear")
async def clear_chat_session(request: ClearSessionRequest):
    """
    Clear chat history for a specific user.
    """
    try:
        result = agents_service.clear_session_memory(request.user_id)
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        )


# ============================================================================
# 2. REPORT GENERATION ENDPOINTS
# ============================================================================

@app.post("/api/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Generate a structured report based on topics and time range.
    Uses deterministic RAG for grounded results.
    """
    try:
        report_content = agents_service.generate_report(
            topics=request.topics,
            time_range=request.time_range,
            structure=request.structure,
            user_id=request.user_id
        )
        
        return ReportResponse(
            report=report_content,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )


# ============================================================================
# 3. PODCAST GENERATION ENDPOINTS
# ============================================================================

@app.post("/api/podcast/generate", response_model=PodcastResponse)
async def generate_podcast(request: PodcastRequest):
    """
    Generate podcast script and audio file.
    Returns both the script text and a reference to the audio file.
    """
    try:
        # UPDATED: Service now returns only the Data URI string
        audio_data_uri = agents_service.generate_podcast(
            topics=request.topics,
            time_range=request.time_range,
            structure=request.structure,
            user_id=request.user_id
        )
        
        return PodcastResponse(
            audio_url=audio_data_uri,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating podcast: {str(e)}"
        )
    
    

# ============================================================================
# 4. USER PROFILE ENDPOINTS (Future Enhancement)
# ============================================================================

@app.get("/api/user/{user_id}/instructions")
async def get_user_instructions(user_id: str):
    """
    Retrieve custom instructions for a specific user.
    """
    try:
        instructions = agents_service.cosmos_db_service.retrieve_user_instructions(user_id)
        return {"user_id": user_id, "instructions": instructions}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user instructions: {str(e)}"
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Initialize services and connections on startup.
    """
    print("Starting deNoise API...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Environment loaded successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on shutdown.
    """
    print("Shutting down deNoise API...")


# ============================================================================
# Run the application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
