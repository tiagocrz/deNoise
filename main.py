'''
FastAPI backend
Generates endpoints for all the functions and methods that the frontend will call.
'''

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime

from services.agents_service import AgentsService
from app_settings import PROJECT_ROOT

# FastAPI app
app = FastAPI(
    title="deNoise API",
    description="AI-powered news processing platform with RAG capabilities",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", # React default
        "http://localhost:5173", # Vite default
        "http://localhost:8080", # Vue default
        "https://denoise.lovable.app" # Production URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agents_service = AgentsService(model="gemini-2.5-flash")


# Request/Response objects for interaction with the frontend
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
    structure: str = Field(..., description="Report structure type")
    user_id: str = Field(..., description="User identifier")

class ReportResponse(BaseModel):
    report: str = Field(..., description="Generated report content")
    timestamp: str = Field(..., description="Report generation timestamp")

class PodcastRequest(BaseModel):
    topics: str = Field(..., description="Topics for podcast content")
    time_range: str = Field(..., description="Time range for news articles (e.g., 'weekly', 'monthly')")
    structure: str = Field(..., description="Podcast structure/style")
    user_id: str = Field(..., description="User identifier")

class PodcastResponse(BaseModel):
    audio_url: str = Field(..., description="URI audio file")
    timestamp: str = Field(..., description="Podcast generation timestamp")

class UserProfileRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User's email address")
    display_name: str = Field(..., description="User's chosen display name")
    system_instructions: str = Field(..., description="Custom system instructions for the generate_content calls")

class ShortUserProfileResponse(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    instructions: str = Field(..., description="Custom system instructions")
    display_name: str = Field(..., description="User's display name")

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


# API Endpoints

# Health
@app.get("/", response_model=HealthResponse)
async def root():
    '''
    Root endpoint - Health check
    '''
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    '''
    Health check endpoint
    '''
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


# Conversational agent endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    '''
    Conversational chat endpoint with RAG capabilities.
    Maintains session context per user.
    '''
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
    '''
    Clear chat history for a specific user.
    '''
    try:
        result = agents_service.clear_session_memory(request.user_id)
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        )


# Report generation endpoints
@app.post("/api/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    '''
    Generate a structured report based on retrieved context and instructions.
    '''
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


# Podcast generation endpoints
@app.post("/api/podcast/generate", response_model=PodcastResponse)
async def generate_podcast(request: PodcastRequest):
    '''
    Generate the podcast based on retrieved context and instructions.
    '''
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
    
    
# User profile endpoints    
@app.get("/api/user/{user_id}/instructions")
async def get_user_instructions(user_id: str):
    '''
    Retrieve custom instructions and display name for a specific user.
    '''
    try:
        profile_data = agents_service.cosmos_db_service.retrieve_user_instructions(user_id)
        
        if profile_data is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return ShortUserProfileResponse(
            user_id=user_id,
            instructions=profile_data["system_instructions"],
            display_name=profile_data["display_name"]
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/user/profile")
async def sync_user_profile(profile: UserProfileRequest):
    '''
    Create or Update user profile settings.
    '''
    try:
        # Convert Pydantic model to dict
        profile_data = profile.dict()

        agents_service.cosmos_db_service.sync_user_profile(profile_data)

        return {"status": "success", "message": "Profile updated"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving profile: {str(e)}"
        )
    

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    '''
    Error Handling for 404 Not Found
    '''
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    '''
    Error Handling for 500 Internal Server Error
    '''
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Startup/shutdown handlers
@app.on_event("startup")
async def startup_event():
    '''
    Initialize services and connections on startup.
    '''
    print("Starting deNoise API...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Environment loaded successfully")

@app.on_event("shutdown")
async def shutdown_event():
    '''
    Cleanup on shutdown.
    '''
    print("Shutting down deNoise API...")


# Run the app
if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
