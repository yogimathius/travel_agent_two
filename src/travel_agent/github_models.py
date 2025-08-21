import httpx
import json
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()


class GitHubModelsClient:
    """Client for interacting with GitHub Models API (GPT-4o-mini)."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        self.base_url = "https://models.inference.ai.azure.com"
        self.model = "gpt-4o-mini"
        
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Send a chat completion request to GitHub Models.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Response randomness (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt to prepend
        
        Returns:
            The model's response content
        """
        # Prepend system prompt if provided
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        payload = {
            "messages": messages,
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("Invalid GitHub token. Please check your GITHUB_TOKEN environment variable.")
                elif e.response.status_code == 429:
                    raise ValueError("Rate limit exceeded. Please try again later.")
                else:
                    raise ValueError(f"GitHub Models API error: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                raise ValueError(f"Request error: {str(e)}")
            except KeyError as e:
                raise ValueError(f"Unexpected response format: {str(e)}")
    
    async def extract_travel_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Extract travel booking intent from user message.
        
        Returns a structured dict with extracted information like:
        - origin, destination
        - dates
        - passenger count
        - preferences
        """
        system_prompt = """You are a travel booking assistant. Extract structured information from user travel requests.

Return a JSON object with the following fields (use null for missing info):
- "origin": departure city/airport
- "destination": arrival city/airport  
- "departure_date": date in YYYY-MM-DD format
- "return_date": return date in YYYY-MM-DD format (null for one-way)
- "adults": number of adult passengers (default 1)
- "cabin_class": "economy", "premium_economy", "business", or "first"
- "direct_only": boolean for direct flights preference
- "max_budget": maximum price if mentioned
- "intent": "search_flights", "book_flight", "get_info", "modify_search", or "other"
- "user_message": the original message for context

Examples:
User: "I want to fly from Los Angeles to New York on December 15th"
Response: {"origin": "Los Angeles", "destination": "New York", "departure_date": "2025-12-15", "return_date": null, "adults": 1, "cabin_class": "economy", "direct_only": false, "max_budget": null, "intent": "search_flights", "user_message": "I want to fly from Los Angeles to New York on December 15th"}

Only return valid JSON, no additional text."""

        messages = [{"role": "user", "content": user_message}]
        
        try:
            response = await self.chat_completion(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for structured extraction
                max_tokens=500
            )
            
            # Parse JSON response
            return json.loads(response.strip())
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "origin": None,
                "destination": None,
                "departure_date": None,
                "return_date": None,
                "adults": 1,
                "cabin_class": "economy",
                "direct_only": False,
                "max_budget": None,
                "intent": "other",
                "user_message": user_message
            }
    
    async def generate_response(
        self,
        user_message: str,
        context: Dict[str, Any],
        conversation_state: str
    ) -> str:
        """
        Generate a conversational response based on context and state.
        
        Args:
            user_message: Latest user message
            context: Conversation context (search results, booking info, etc.)
            conversation_state: Current conversation state
        
        Returns:
            Generated response string
        """
        system_prompt = f"""You are a helpful travel booking assistant. Current conversation state: {conversation_state}

Guidelines:
- Be friendly, helpful, and concise
- Ask clarifying questions when needed
- Provide clear flight options and details
- Guide users through the booking process step by step
- For passenger information, collect: full name, date of birth, email, phone
- Always confirm important details before proceeding
- Use natural, conversational language

Context information: {json.dumps(context, default=str, indent=2)}

Respond naturally to the user's message."""

        messages = [{"role": "user", "content": user_message}]
        
        return await self.chat_completion(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=800
        )