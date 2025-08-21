from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

from .models import ChatRequest, ChatResponse
from .agent import TravelAgent

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Travel Agent AI",
    description="An AI-powered travel agent for flight booking",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the travel agent
travel_agent = TravelAgent()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with simple chat interface."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Travel Agent AI</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .chat-container { border: 1px solid #ddd; border-radius: 10px; padding: 20px; margin: 20px 0; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user { background-color: #e3f2fd; margin-left: 20px; }
            .agent { background-color: #f5f5f5; margin-right: 20px; }
            .input-container { display: flex; gap: 10px; margin-top: 20px; }
            input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            button { padding: 10px 20px; background-color: #2196f3; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background-color: #1976d2; }
            .examples { margin: 20px 0; padding: 15px; background-color: #fff3e0; border-radius: 5px; }
            .examples h3 { margin-top: 0; }
        </style>
    </head>
    <body>
        <h1>🛩️ Travel Agent AI</h1>
        <p>Your AI-powered flight booking assistant. Ask me to help you find and book flights!</p>
        
        <div class="examples">
            <h3>Try these examples:</h3>
            <ul>
                <li>"I want to fly from Los Angeles to New York on December 15th"</li>
                <li>"Find me flights from LAX to JFK next Friday"</li>
                <li>"Book a round trip from San Francisco to Miami"</li>
                <li>"Show me business class flights from Chicago to Atlanta"</li>
            </ul>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message agent">
                Hello! I'm your AI travel agent. I can help you search for flights and guide you through the booking process. Where would you like to travel?
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <script>
            let sessionId = null;
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;
                
                // Add user message to chat
                addMessage(message, 'user');
                input.value = '';
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            session_id: sessionId
                        })
                    });
                    
                    const data = await response.json();
                    sessionId = data.session_id;
                    
                    // Add agent response to chat
                    addMessage(data.response, 'agent');
                    
                } catch (error) {
                    addMessage('Sorry, I encountered an error. Please try again.', 'agent');
                    console.error('Error:', error);
                }
            }
            
            function addMessage(content, sender) {
                const container = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                messageDiv.innerHTML = content.replace(/\\n/g, '<br>');
                container.appendChild(messageDiv);
                container.scrollTop = container.scrollHeight;
            }
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "travel-agent-ai"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for conversing with the travel agent.
    
    This endpoint handles all conversation with the AI travel agent,
    including flight searches, bookings, and general travel assistance.
    """
    try:
        response = await travel_agent.chat(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get conversation session details."""
    if session_id not in travel_agent.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = travel_agent.sessions[session_id]
    return {
        "session_id": session.session_id,
        "state": session.state,
        "message_count": len(session.messages),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "has_search_results": session.last_search_results is not None,
        "has_selected_flight": session.selected_flight is not None,
        "passenger_count": len(session.passengers)
    }

@app.get("/docs-info")
async def docs_info():
    """Information about API documentation."""
    return {
        "message": "Visit /docs for interactive API documentation",
        "swagger_ui": "/docs",
        "redoc": "/redoc",
        "openapi_json": "/openapi.json"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)