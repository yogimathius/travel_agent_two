import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from travel_agent.github_models import GitHubModelsClient


class TestGitHubModelsClient:
    def setup_method(self):
        # Use a test token for unit tests
        self.client = GitHubModelsClient(github_token="test_token")
    
    def test_client_initialization(self):
        assert self.client.github_token == "test_token"
        assert self.client.model == "gpt-4o-mini"
        assert "Authorization" in self.client.headers
    
    def test_missing_token_raises_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GitHub token is required"):
                GitHubModelsClient()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_chat_completion_success(self, mock_post):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello! How can I help you?"}}]
        }
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello"}]
        result = await self.client.chat_completion(messages)
        
        assert result == "Hello! How can I help you?"
        mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_chat_completion_with_system_prompt(self, mock_post):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "System response"}}]
        }
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test"}]
        system_prompt = "You are a helpful assistant"
        
        await self.client.chat_completion(messages, system_prompt=system_prompt)
        
        # Verify the system prompt was added to the messages
        call_args = mock_post.call_args
        sent_messages = call_args.kwargs['json']['messages']
        assert sent_messages[0]['role'] == 'system'
        assert sent_messages[0]['content'] == system_prompt
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_extract_travel_intent_success(self, mock_post):
        # Mock successful response with valid JSON
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"origin": "Los Angeles", "destination": "New York", "departure_date": "2025-12-15", "intent": "search_flights"}'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        user_message = "I want to fly from Los Angeles to New York on December 15th"
        result = await self.client.extract_travel_intent(user_message)
        
        assert result['origin'] == "Los Angeles"
        assert result['destination'] == "New York"
        assert result['departure_date'] == "2025-12-15"
        assert result['intent'] == "search_flights"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_extract_travel_intent_invalid_json_fallback(self, mock_post):
        # Mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Invalid JSON response"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        user_message = "I want to travel"
        result = await self.client.extract_travel_intent(user_message)
        
        # Should return fallback structure
        assert result['intent'] == "other"
        assert result['user_message'] == user_message
        assert result['adults'] == 1
        assert result['cabin_class'] == "economy"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_generate_response(self, mock_post):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "I'd be happy to help you find flights! Where would you like to travel?"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        user_message = "I need help booking a flight"
        context = {"previous_searches": []}
        state = "initial"
        
        result = await self.client.generate_response(user_message, context, state)
        
        assert "help you find flights" in result
        mock_post.assert_called_once()
    
    @pytest.mark.asyncio 
    @patch('httpx.AsyncClient.post')
    async def test_http_error_handling(self, mock_post):
        # Mock HTTP error
        import httpx
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=None, response=mock_response
        )
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(ValueError, match="Invalid GitHub token"):
            await self.client.chat_completion(messages)