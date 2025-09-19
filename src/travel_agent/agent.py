import uuid
from datetime import date, datetime
from typing import Dict, Any, Optional, List
import json

from .models import (
    ConversationSession, ConversationState, ChatRequest, ChatResponse,
    FlightSearchRequest, FlightSearchResponse, Flight, PassengerInfo,
    BookingRequest, BookingResponse, CabinClass, FlightType
)
from .flight_service import MockFlightService
from .github_models import GitHubModelsClient


class TravelAgent:
    """
    Core travel agent with conversation management and flight booking logic.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        self.flight_service = MockFlightService()
        self.ai_client = GitHubModelsClient(github_token)
        self.sessions: Dict[str, ConversationSession] = {}
    
    def _create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new conversation session."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = ConversationSession(session_id=session_id)
        return session_id
    
    def _get_session(self, session_id: str) -> ConversationSession:
        """Get or create a conversation session."""
        if session_id not in self.sessions:
            self._create_session(session_id)
        return self.sessions[session_id]
    
    async def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse a date string into a date object."""
        try:
            # Try common formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%B %d, %Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except:
            return None
    
    async def _extract_search_params(self, intent_data: Dict[str, Any]) -> Optional[FlightSearchRequest]:
        """Convert extracted intent data into a FlightSearchRequest."""
        try:
            origin = intent_data.get("origin")
            destination = intent_data.get("destination")
            departure_date_str = intent_data.get("departure_date")
            
            if not all([origin, destination, departure_date_str]):
                return None
            
            departure_date = await self._parse_date(departure_date_str)
            if not departure_date:
                return None
            
            # Handle return date
            return_date = None
            if intent_data.get("return_date"):
                return_date = await self._parse_date(intent_data["return_date"])
            
            # Map cabin class
            cabin_class_map = {
                "economy": CabinClass.ECONOMY,
                "premium_economy": CabinClass.PREMIUM_ECONOMY,
                "business": CabinClass.BUSINESS,
                "first": CabinClass.FIRST
            }
            cabin_class = cabin_class_map.get(intent_data.get("cabin_class", "economy"), CabinClass.ECONOMY)
            
            # Determine flight type
            flight_type = FlightType.ROUND_TRIP if return_date else FlightType.ONE_WAY
            
            return FlightSearchRequest(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                adults=intent_data.get("adults", 1),
                cabin_class=cabin_class,
                flight_type=flight_type,
                direct_only=intent_data.get("direct_only", False),
                max_price=intent_data.get("max_budget")
            )
            
        except Exception:
            return None
    
    def _format_flight_for_display(self, flight: Flight, index: int) -> str:
        """Format a flight for user display with enhanced visual hierarchy."""
        segments_info = []
        for segment in flight.segments:
            dep_time = segment.departure_time.strftime("%I:%M %p")
            arr_time = segment.arrival_time.strftime("%I:%M %p")
            segments_info.append(
                f"🛫 **{segment.departure_airport.code}** → **{segment.arrival_airport.code}** "
                f"({dep_time} - {arr_time})"
            )
            segments_info.append(f"   ✈️ {segment.airline} {segment.flight_number}")
        
        stops_text = "🎯 Direct Flight" if flight.is_direct else f"🔄 {flight.stops} Stop(s)"
        baggage_text = self._format_baggage(flight.baggage_info)
        refund_status = "✅ **Refundable**" if flight.is_refundable else "❌ Non-refundable"
        
        # Enhanced formatting with icons and better structure
        return f"""
---
**💺 Option {index + 1}** - **${flight.price:.2f}** | {stops_text}

{chr(10).join(segments_info)}

⏱️ **Duration:** {flight.total_duration}  
🎫 **Cabin:** {flight.cabin_class.value.replace('_', ' ').title()}  
🧳 **Baggage:** {baggage_text}  
🔄 **Refund:** {refund_status}
---"""
    
    def _format_baggage(self, baggage_info: List) -> str:
        """Format baggage information for display with icons."""
        carry_on = next((b for b in baggage_info if b.type.value == "carry_on"), None)
        checked = next((b for b in baggage_info if b.type.value == "checked"), None)
        
        parts = []
        if carry_on:
            if carry_on.included:
                parts.append("👜 Carry-on **included**")
            else:
                parts.append(f"👜 Carry-on: **${carry_on.fee}**")
        if checked:
            if checked.included:
                parts.append("🧳 1st bag **included**")
            else:
                parts.append(f"🧳 1st bag: **${checked.fee}**")
        
        return " | ".join(parts)
    
    def _create_comparison_table(self, flights: List[Flight]) -> str:
        """Create a quick comparison table for flights."""
        if len(flights) < 2:
            return ""
        
        table_parts = [
            "📊 **Quick Comparison**",
            "",
            "| Option | Price | Duration | Type | Refundable |",
            "|--------|-------|----------|------|------------|"
        ]
        
        for i, flight in enumerate(flights):
            price = f"${flight.price:.2f}"
            duration = flight.total_duration
            flight_type = "Direct" if flight.is_direct else f"{flight.stops} stop(s)"
            refundable = "✅" if flight.is_refundable else "❌"
            
            table_parts.append(f"| Option {i+1} | **{price}** | {duration} | {flight_type} | {refundable} |")
        
        return "\n".join(table_parts)
    
    async def _handle_flight_search(self, session: ConversationSession, intent_data: Dict[str, Any]) -> str:
        """Handle flight search request."""
        search_request = await self._extract_search_params(intent_data)
        
        if not search_request:
            missing_info = []
            if not intent_data.get("origin"):
                missing_info.append("departure city/airport")
            if not intent_data.get("destination"):
                missing_info.append("destination city/airport")
            if not intent_data.get("departure_date"):
                missing_info.append("departure date")
            
            return f"I need a bit more information to search for flights. Please provide: {', '.join(missing_info)}"
        
        try:
            # Perform the search
            search_response = await self.flight_service.search_flights(search_request)
            
            # Update session
            session.current_search = search_request
            session.last_search_results = search_response
            session.state = ConversationState.SHOWING_RESULTS
            session.updated_at = datetime.now()
            
            if not search_response.flights:
                return "I couldn't find any flights matching your criteria. Would you like to try different dates or destinations?"
            
            # Format response
            response_parts = [
                f"Great! I found {len(search_response.flights)} flights from {search_request.origin} to {search_request.destination} on {search_request.departure_date.strftime('%B %d, %Y')}:\\n"
            ]
            
            # Show top 5 flights
            for i, flight in enumerate(search_response.flights[:5]):
                response_parts.append(self._format_flight_for_display(flight, i))
                response_parts.append("")  # Empty line
            
            # Add comparison table if 3 or more flights
            if len(search_response.flights) >= 3:
                response_parts.append(self._create_comparison_table(search_response.flights[:5]))
                response_parts.append("")
            
            if len(search_response.flights) > 5:
                response_parts.append(f"... and {len(search_response.flights) - 5} more options.")
            
            response_parts.append("\\nWhich option interests you? Just say the number (e.g., 'Option 1') or ask for more details!")
            
            return "\\n".join(response_parts)
            
        except ValueError as e:
            return f"Sorry, I couldn't search for flights: {str(e)}"
        except Exception:
            return "I encountered an error while searching for flights. Please try again."
    
    async def _handle_flight_selection(self, session: ConversationSession, user_message: str) -> str:
        """Handle flight selection from search results."""
        if not session.last_search_results or not session.last_search_results.flights:
            return "I don't have any flight search results. Let's search for flights first!"
        
        # Extract number from user message
        import re
        numbers = re.findall(r'\\b(\\d+)\\b', user_message.lower())
        option_words = re.findall(r'option\\s+(\\d+)', user_message.lower())
        
        selected_index = None
        if option_words:
            selected_index = int(option_words[0]) - 1
        elif numbers:
            selected_index = int(numbers[0]) - 1
        
        if selected_index is None or selected_index < 0 or selected_index >= len(session.last_search_results.flights):
            return f"Please select a valid option (1-{len(session.last_search_results.flights)}). Which flight would you like to book?"
        
        # Select the flight
        selected_flight = session.last_search_results.flights[selected_index]
        session.selected_flight = selected_flight
        session.state = ConversationState.COLLECTING_PASSENGER_INFO
        session.updated_at = datetime.now()
        
        flight_summary = self._format_flight_for_display(selected_flight, selected_index)
        
        return f"""Perfect! You've selected:

{flight_summary}

Now I need some passenger information to proceed with the booking. Let's start with the first passenger:

1. **Full Name** (as it appears on your ID)
2. **Date of Birth** (MM/DD/YYYY)  
3. **Email Address**
4. **Phone Number**

You can provide all the information at once or one piece at a time. What's the passenger's full name?"""
    
    async def _collect_passenger_info(self, session: ConversationSession, user_message: str) -> str:
        """Collect passenger information step by step."""
        # This is a simplified version - in a real system you'd have more sophisticated
        # information extraction and validation
        
        # For now, let's assume we're collecting all info at once
        # In practice, you'd use the AI model to extract structured information
        
        context = {
            "collecting_passenger_info": True,
            "passengers_collected": len(session.passengers),
            "total_passengers_needed": session.current_search.adults if session.current_search else 1
        }
        
        # Use AI to extract passenger information
        response = await self.ai_client.generate_response(
            user_message, context, session.state.value
        )
        
        # For demo purposes, let's simulate successful collection after a few exchanges
        if len(session.passengers) == 0 and any(word in user_message.lower() for word in ['john', 'jane', 'smith', 'doe']):
            # Simulate adding a passenger
            passenger = PassengerInfo(
                first_name="John",
                last_name="Doe", 
                date_of_birth=date(1990, 1, 1),
                email="john.doe@example.com",
                phone="+1-555-0123"
            )
            session.passengers.append(passenger)
            session.state = ConversationState.CONFIRMING_BOOKING
            session.updated_at = datetime.now()
            
            return """Great! I have the passenger information:

**Passenger 1:**
- Name: John Doe
- Date of Birth: January 1, 1990
- Email: john.doe@example.com
- Phone: +1-555-0123

Now let me prepare your booking summary..."""
        
        return response
    
    async def _handle_booking_confirmation(self, session: ConversationSession, user_message: str) -> str:
        """Handle final booking confirmation."""
        if not session.selected_flight or not session.passengers:
            return "I'm missing some information. Let's start over with finding flights."
        
        # Generate booking reference
        booking_ref = f"TB{uuid.uuid4().hex[:6].upper()}"
        
        flight_summary = self._format_flight_for_display(session.selected_flight, 0)
        passenger_summary = "\\n".join([
            f"**Passenger {i+1}:** {p.first_name} {p.last_name}"
            for i, p in enumerate(session.passengers)
        ])
        
        # Create booking response (simulation - no actual booking)
        booking = BookingResponse(
            booking_reference=booking_ref,
            total_price=session.selected_flight.price * len(session.passengers),
            flight=session.selected_flight,
            passengers=session.passengers
        )
        
        # Update session
        session.state = ConversationState.COMPLETED
        session.updated_at = datetime.now()
        
        return f"""
🎉 **BOOKING CONFIRMED** 🎉

📋 **Booking Reference:** `{booking_ref}`  
💰 **Total Price:** **${booking.total_price:.2f}**

**Flight Details:**
{flight_summary}

**Passengers:**
{passenger_summary}

**Important:** This is a DEMO booking simulation. No actual charges have been made or tickets purchased. In a real system, this is where payment processing would occur.

Is there anything else I can help you with for your travel planning?"""
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Main chat interface for the travel agent."""
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        session = self._get_session(session_id)
        
        # Add user message to conversation
        from .models import UserMessage
        session.messages.append(UserMessage(content=request.message))
        
        try:
            # Extract intent from user message
            intent_data = await self.ai_client.extract_travel_intent(request.message)
            
            # Handle based on current state and intent
            if session.state == ConversationState.INITIAL:
                if intent_data["intent"] == "search_flights":
                    response_text = await self._handle_flight_search(session, intent_data)
                else:
                    context = {"first_interaction": True}
                    response_text = await self.ai_client.generate_response(
                        request.message, context, session.state.value
                    )
            
            elif session.state == ConversationState.SHOWING_RESULTS:
                # User is selecting from flight results
                response_text = await self._handle_flight_selection(session, request.message)
            
            elif session.state == ConversationState.COLLECTING_PASSENGER_INFO:
                response_text = await self._collect_passenger_info(session, request.message)
            
            elif session.state == ConversationState.CONFIRMING_BOOKING:
                response_text = await self._handle_booking_confirmation(session, request.message)
            
            elif session.state == ConversationState.COMPLETED:
                # Handle post-booking queries
                context = {"booking_completed": True}
                response_text = await self.ai_client.generate_response(
                    request.message, context, session.state.value
                )
            
            else:
                # Fallback
                context = session.context
                response_text = await self.ai_client.generate_response(
                    request.message, context, session.state.value
                )
            
            # Add agent message to conversation
            from .models import AgentMessage
            session.messages.append(AgentMessage(content=response_text))
            session.updated_at = datetime.now()
            
            # Prepare response
            flight_results = None
            if session.state == ConversationState.SHOWING_RESULTS and session.last_search_results:
                flight_results = session.last_search_results.flights[:5]  # Top 5 for display
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                state=session.state,
                flight_results=flight_results
            )
            
        except Exception as e:
            # Error handling
            error_response = "I apologize, but I encountered an error. Let's try again - how can I help you with your travel plans?"
            
            from .models import AgentMessage
            session.messages.append(AgentMessage(content=error_response))
            
            return ChatResponse(
                response=error_response,
                session_id=session_id,
                state=session.state
            )