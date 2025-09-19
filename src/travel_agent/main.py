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
    """Root endpoint with modern chat interface."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Travel Agent AI</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --primary-color: #6366f1;
                --primary-dark: #4f46e5;
                --secondary-color: #f8fafc;
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --border-color: #e2e8f0;
                --success-color: #10b981;
                --warning-color: #f59e0b;
                --danger-color: #ef4444;
                --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --message-user-bg: #6366f1;
                --message-agent-bg: #ffffff;
                --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
                --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
                --radius-sm: 0.375rem;
                --radius-md: 0.5rem;
                --radius-lg: 0.75rem;
                --radius-xl: 1rem;
            }

            [data-theme="dark"] {
                --secondary-color: #1e293b;
                --text-primary: #f1f5f9;
                --text-secondary: #94a3b8;
                --border-color: #334155;
                --message-agent-bg: #2d3748;
                --bg-gradient: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: var(--bg-gradient);
                color: var(--text-primary);
                min-height: 100vh;
                line-height: 1.6;
            }

            .app-container {
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                max-width: 1200px;
                margin: 0 auto;
                padding: 1rem;
            }

            .header {
                text-align: center;
                padding: 2rem 0;
                color: white;
            }

            .header h1 {
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                text-shadow: var(--shadow-lg);
            }

            .header p {
                font-size: 1.1rem;
                opacity: 0.9;
                font-weight: 300;
            }

            .theme-toggle {
                position: fixed;
                top: 1rem;
                right: 1rem;
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 0.75rem;
                border-radius: var(--radius-lg);
                cursor: pointer;
                backdrop-filter: blur(10px);
                z-index: 1000;
                transition: all 0.3s ease;
            }

            .theme-toggle:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: scale(1.05);
            }

            .main-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                background: var(--secondary-color);
                border-radius: var(--radius-xl);
                box-shadow: var(--shadow-lg);
                overflow: hidden;
                max-height: 70vh;
            }

            .examples-section {
                padding: 1.5rem;
                background: linear-gradient(45deg, #f8fafc, #e2e8f0);
                border-bottom: 1px solid var(--border-color);
            }

            [data-theme="dark"] .examples-section {
                background: linear-gradient(45deg, #2d3748, #1a202c);
            }

            .examples-title {
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 1rem;
                color: var(--text-primary);
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .example-chips {
                display: flex;
                flex-wrap: wrap;
                gap: 0.75rem;
            }

            .example-chip {
                background: white;
                border: 1px solid var(--border-color);
                padding: 0.5rem 1rem;
                border-radius: var(--radius-lg);
                font-size: 0.9rem;
                cursor: pointer;
                transition: all 0.2s ease;
                color: var(--text-secondary);
            }

            .example-chip:hover {
                background: var(--primary-color);
                color: white;
                transform: translateY(-1px);
                box-shadow: var(--shadow-md);
            }

            [data-theme="dark"] .example-chip {
                background: #374151;
                border-color: #4b5563;
                color: #d1d5db;
            }

            .chat-container {
                flex: 1;
                padding: 1.5rem;
                overflow-y: auto;
                scroll-behavior: smooth;
            }

            .message {
                margin-bottom: 1.5rem;
                display: flex;
                align-items: flex-start;
                gap: 0.75rem;
                animation: messageSlide 0.3s ease-out;
            }

            @keyframes messageSlide {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .message.user {
                flex-direction: row-reverse;
            }

            .message-avatar {
                width: 2.5rem;
                height: 2.5rem;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 0.9rem;
            }

            .user .message-avatar {
                background: var(--primary-color);
                color: white;
            }

            .agent .message-avatar {
                background: var(--success-color);
                color: white;
            }

            .message-content {
                flex: 1;
                max-width: 70%;
            }

            .message-bubble {
                padding: 1rem 1.25rem;
                border-radius: var(--radius-lg);
                position: relative;
                word-wrap: break-word;
                line-height: 1.5;
            }

            .user .message-bubble {
                background: var(--message-user-bg);
                color: white;
                border-bottom-right-radius: var(--radius-sm);
            }

            .agent .message-bubble {
                background: var(--message-agent-bg);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                border-bottom-left-radius: var(--radius-sm);
                box-shadow: var(--shadow-sm);
            }

            .message-time {
                font-size: 0.75rem;
                color: var(--text-secondary);
                margin-top: 0.25rem;
                opacity: 0.7;
            }

            .input-section {
                padding: 1.5rem;
                background: var(--secondary-color);
                border-top: 1px solid var(--border-color);
            }

            .input-container {
                display: flex;
                gap: 0.75rem;
                align-items: center;
                max-width: 100%;
            }

            .message-input {
                flex: 1;
                padding: 0.875rem 1.25rem;
                border: 2px solid var(--border-color);
                border-radius: var(--radius-lg);
                font-size: 1rem;
                background: white;
                color: var(--text-primary);
                transition: all 0.2s ease;
                outline: none;
            }

            [data-theme="dark"] .message-input {
                background: #374151;
                border-color: #4b5563;
                color: white;
            }

            .message-input:focus {
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }

            .send-button {
                padding: 0.875rem 1.5rem;
                background: var(--primary-color);
                color: white;
                border: none;
                border-radius: var(--radius-lg);
                cursor: pointer;
                font-weight: 600;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .send-button:hover:not(:disabled) {
                background: var(--primary-dark);
                transform: translateY(-1px);
                box-shadow: var(--shadow-md);
            }

            .send-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            .typing-indicator {
                display: none;
                align-items: center;
                gap: 0.5rem;
                padding: 1rem;
                color: var(--text-secondary);
                font-style: italic;
            }

            .typing-dots {
                display: flex;
                gap: 0.25rem;
            }

            .typing-dot {
                width: 0.5rem;
                height: 0.5rem;
                background: var(--text-secondary);
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;
            }

            .typing-dot:nth-child(2) { animation-delay: 0.2s; }
            .typing-dot:nth-child(3) { animation-delay: 0.4s; }

            @keyframes typing {
                0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
                40% { transform: scale(1); opacity: 1; }
            }

            .flight-card {
                background: linear-gradient(135deg, #fff, #f8fafc);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: var(--shadow-sm);
                transition: all 0.3s ease;
            }

            .flight-card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
            }

            @media (max-width: 768px) {
                .app-container {
                    padding: 0.5rem;
                }

                .header h1 {
                    font-size: 2rem;
                }

                .main-content {
                    max-height: 75vh;
                }

                .message-content {
                    max-width: 85%;
                }

                .example-chips {
                    flex-direction: column;
                }

                .input-container {
                    flex-direction: column;
                    gap: 0.5rem;
                }

                .message-input,
                .send-button {
                    width: 100%;
                }
            }

            .status-indicator {
                position: fixed;
                bottom: 1rem;
                left: 1rem;
                padding: 0.5rem 1rem;
                background: var(--success-color);
                color: white;
                border-radius: var(--radius-lg);
                font-size: 0.875rem;
                display: none;
            }
        </style>
    </head>
    <body data-theme="light">
        <div class="app-container">
            <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">
                <i class="fas fa-moon" id="themeIcon"></i>
            </button>

            <div class="header">
                <h1><i class="fas fa-plane-departure"></i> Travel Agent AI</h1>
                <p>Your intelligent flight booking companion - powered by AI</p>
            </div>

            <div class="main-content">
                <div class="examples-section">
                    <div class="examples-title">
                        <i class="fas fa-lightbulb"></i>
                        Quick Start Examples
                    </div>
                    <div class="example-chips">
                        <div class="example-chip" onclick="useExample('I want to fly from Los Angeles to New York on December 15th')">
                            <i class="fas fa-route"></i> LAX to NYC
                        </div>
                        <div class="example-chip" onclick="useExample('Find me flights from LAX to JFK next Friday')">
                            <i class="fas fa-calendar"></i> Next Friday
                        </div>
                        <div class="example-chip" onclick="useExample('Book a round trip from San Francisco to Miami')">
                            <i class="fas fa-exchange-alt"></i> Round Trip
                        </div>
                        <div class="example-chip" onclick="useExample('Show me business class flights from Chicago to Atlanta')">
                            <i class="fas fa-star"></i> Business Class
                        </div>
                    </div>
                </div>

                <div class="chat-container" id="chatContainer">
                    <div class="message agent">
                        <div class="message-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-content">
                            <div class="message-bubble">
                                👋 Hello! I'm your AI travel agent. I can help you search for flights and guide you through the entire booking process. Where would you like to travel today?
                            </div>
                            <div class="message-time" id="welcomeTime"></div>
                        </div>
                    </div>
                </div>

                <div class="typing-indicator" id="typingIndicator">
                    <i class="fas fa-robot"></i>
                    <span>Agent is typing</span>
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>

            <div class="input-section">
                <div class="input-container">
                    <input 
                        type="text" 
                        class="message-input" 
                        id="messageInput" 
                        placeholder="Type your message here..." 
                        onkeypress="handleKeyPress(event)"
                        autocomplete="off"
                    >
                    <button class="send-button" onclick="sendMessage()" id="sendButton">
                        <i class="fas fa-paper-plane"></i>
                        Send
                    </button>
                </div>
            </div>
        </div>

        <div class="status-indicator" id="statusIndicator">
            Connected
        </div>

        <script>
            let sessionId = null;
            let isTyping = false;

            // Initialize welcome time
            document.getElementById('welcomeTime').textContent = new Date().toLocaleTimeString();

            function toggleTheme() {
                const body = document.body;
                const themeIcon = document.getElementById('themeIcon');
                const currentTheme = body.getAttribute('data-theme');
                
                if (currentTheme === 'light') {
                    body.setAttribute('data-theme', 'dark');
                    themeIcon.className = 'fas fa-sun';
                    localStorage.setItem('theme', 'dark');
                } else {
                    body.setAttribute('data-theme', 'light');
                    themeIcon.className = 'fas fa-moon';
                    localStorage.setItem('theme', 'light');
                }
            }

            // Load saved theme
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.body.setAttribute('data-theme', savedTheme);
            document.getElementById('themeIcon').className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';

            function useExample(text) {
                document.getElementById('messageInput').value = text;
                document.getElementById('messageInput').focus();
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage();
                }
            }

            function showTypingIndicator() {
                document.getElementById('typingIndicator').style.display = 'flex';
                const container = document.getElementById('chatContainer');
                container.scrollTop = container.scrollHeight;
            }

            function hideTypingIndicator() {
                document.getElementById('typingIndicator').style.display = 'none';
            }

            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const sendButton = document.getElementById('sendButton');
                const message = input.value.trim();
                
                if (!message || isTyping) return;

                // Disable input while processing
                isTyping = true;
                input.disabled = true;
                sendButton.disabled = true;
                
                // Add user message to chat
                addMessage(message, 'user');
                input.value = '';
                
                // Show typing indicator
                showTypingIndicator();

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

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    sessionId = data.session_id;
                    
                    // Hide typing indicator and add agent response
                    hideTypingIndicator();
                    addMessage(data.response, 'agent');
                    
                } catch (error) {
                    hideTypingIndicator();
                    addMessage('Sorry, I encountered an error. Please try again.', 'agent', true);
                    console.error('Error:', error);
                } finally {
                    // Re-enable input
                    isTyping = false;
                    input.disabled = false;
                    sendButton.disabled = false;
                    input.focus();
                }
            }

            function addMessage(content, sender, isError = false) {
                const container = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                
                const avatar = document.createElement('div');
                avatar.className = 'message-avatar';
                avatar.innerHTML = sender === 'user' 
                    ? '<i class="fas fa-user"></i>' 
                    : isError 
                        ? '<i class="fas fa-exclamation-triangle"></i>'
                        : '<i class="fas fa-robot"></i>';

                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                
                const bubble = document.createElement('div');
                bubble.className = 'message-bubble';
                if (isError) {
                    bubble.style.background = 'var(--danger-color)';
                    bubble.style.color = 'white';
                }
                
                // Enhanced message formatting
                const formattedContent = content
                    .replace(/\\n/g, '<br>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/(\\$[0-9,]+\\.?[0-9]*)/g, '<span style="font-weight: bold; color: var(--success-color);">$1</span>');
                
                bubble.innerHTML = formattedContent;
                
                const timeDiv = document.createElement('div');
                timeDiv.className = 'message-time';
                timeDiv.textContent = new Date().toLocaleTimeString();
                
                contentDiv.appendChild(bubble);
                contentDiv.appendChild(timeDiv);
                
                messageDiv.appendChild(avatar);
                messageDiv.appendChild(contentDiv);
                
                container.appendChild(messageDiv);
                container.scrollTop = container.scrollHeight;
            }

            // Auto-focus input on load
            window.addEventListener('load', () => {
                document.getElementById('messageInput').focus();
                
                // Show connection status briefly
                const statusIndicator = document.getElementById('statusIndicator');
                statusIndicator.style.display = 'block';
                setTimeout(() => {
                    statusIndicator.style.display = 'none';
                }, 2000);
            });
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