#!/usr/bin/env python3
"""
Enhanced Chatbot with MCP Database Integration
Provides intelligent database query capabilities using natural language
"""

import re
import json
import asyncio
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

class EnhancedChatbot:
    """Enhanced chatbot with MCP database integration."""
    
    def __init__(self, db_path: str = "instance/energyrush.db"):
        self.db_path = db_path
        self.setup_nlp_models()
        self.setup_intent_patterns()
    
    def setup_nlp_models(self):
        """Initialize NLP models for intent classification."""
        try:
            # Use a lightweight model for intent classification
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
            print("✅ NLP models loaded successfully")
        except Exception as e:
            print(f"⚠️ NLP model loading failed: {e}")
            self.tokenizer = None
    
    def setup_intent_patterns(self):
        """Setup patterns for intent recognition."""
        self.intent_patterns = {
            "order_details": [
                r"order\s+(?:id\s+)?(\d+)",
                r"order\s+number\s+(\d+)",
                r"find\s+order\s+(\d+)",
                r"show\s+order\s+(\d+)",
                r"details\s+(?:for\s+)?order\s+(\d+)"
            ],
            "customer_orders": [
                r"orders?\s+(?:for\s+|by\s+)(.+?)(?:\s|$)",
                r"customer\s+(.+?)\s+orders?",
                r"find\s+(?:orders?\s+)?(?:for\s+)?customer\s+(.+?)(?:\s|$)",
                r"show\s+(.+?)(?:'?s)?\s+orders?",
                r"(.+?)\s+order\s+history"
            ],
            "order_summary": [
                r"order\s+summary",
                r"total\s+orders?",
                r"order\s+statistics?",
                r"how\s+many\s+orders?",
                r"order\s+count",
                r"recent\s+orders?",
                r"orders?\s+in\s+last\s+(\d+)\s+days?"
            ],
            "revenue_analysis": [
                r"revenue\s+(?:analysis|report)",
                r"sales\s+(?:analysis|report)",
                r"total\s+(?:revenue|sales)",
                r"how\s+much\s+(?:revenue|money|sales)",
                r"earnings?",
                r"income\s+report",
                r"financial\s+summary"
            ],
            "product_details": [
                r"product\s+(?:id\s+)?(\d+)",
                r"inventory",
                r"stock\s+levels?",
                r"products?\s+(?:in\s+)?stock",
                r"what\s+products?",
                r"show\s+products?"
            ],
            "customer_analysis": [
                r"customer\s+analysis",
                r"top\s+customers?",
                r"best\s+customers?",
                r"customer\s+(?:behavior|patterns)",
                r"who\s+(?:are\s+)?(?:my\s+)?(?:top\s+)?customers?"
            ],
            "date_search": [
                r"orders?\s+(?:from|between|in)\s+(.+)",
                r"(?:show|find)\s+orders?\s+(?:from|between)\s+(.+)",
                r"sales\s+(?:from|between)\s+(.+)"
            ]
        }
    
    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """Classify user intent and extract entities."""
        user_input_lower = user_input.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, user_input_lower)
                if match:
                    entities = {}
                    
                    # Extract specific entities based on intent
                    if intent == "order_details":
                        entities["order_id"] = int(match.group(1))
                    elif intent == "customer_orders":
                        entities["customer_name"] = match.group(1).strip()
                    elif intent == "product_details" and match.groups():
                        entities["product_id"] = int(match.group(1))
                    elif intent == "order_summary" and match.groups():
                        entities["days"] = int(match.group(1))
                    elif intent == "date_search":
                        entities["date_text"] = match.group(1).strip()
                    
                    return {
                        "intent": intent,
                        "entities": entities,
                        "confidence": 0.9  # High confidence for pattern matches
                    }
        
        # If no pattern matches, try to extract common entities
        return self.extract_fallback_entities(user_input_lower)
    
    def extract_fallback_entities(self, user_input: str) -> Dict[str, Any]:
        """Extract entities when no clear intent pattern is found."""
        entities = {}
        
        # Look for order numbers
        order_match = re.search(r'\b(\d{1,6})\b', user_input)
        if order_match:
            entities["order_id"] = int(order_match.group(1))
        
        # Look for customer names (common names)
        customer_match = re.search(r'customer[_\s]+(\w+(?:[_\s]+\w+)*)', user_input)
        if customer_match:
            entities["customer_name"] = customer_match.group(1)
        
        # Look for date references
        date_patterns = [
            r'yesterday', r'today', r'last\s+week', r'this\s+week',
            r'last\s+month', r'this\s+month', r'\d{4}-\d{2}-\d{2}'
        ]
        for pattern in date_patterns:
            if re.search(pattern, user_input):
                entities["has_date"] = True
                break
        
        # Default to general query
        return {
            "intent": "general_query",
            "entities": entities,
            "confidence": 0.3
        }
    
    def parse_date_text(self, date_text: str) -> Optional[Dict[str, str]]:
        """Parse natural language date expressions."""
        date_text = date_text.lower().strip()
        today = datetime.now().date()
        
        if "yesterday" in date_text:
            target_date = today - timedelta(days=1)
            return {"start_date": str(target_date), "end_date": str(target_date)}
        elif "today" in date_text:
            return {"start_date": str(today), "end_date": str(today)}
        elif "last week" in date_text:
            start_date = today - timedelta(days=7)
            return {"start_date": str(start_date), "end_date": str(today)}
        elif "this week" in date_text:
            days_since_monday = today.weekday()
            start_date = today - timedelta(days=days_since_monday)
            return {"start_date": str(start_date), "end_date": str(today)}
        elif "last month" in date_text:
            start_date = today.replace(day=1) - timedelta(days=1)
            start_date = start_date.replace(day=1)
            end_date = today.replace(day=1) - timedelta(days=1)
            return {"start_date": str(start_date), "end_date": str(end_date)}
        elif "this month" in date_text:
            start_date = today.replace(day=1)
            return {"start_date": str(start_date), "end_date": str(today)}
        else:
            # Try to parse explicit date ranges
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})(?:\s+(?:to|and)\s+(\d{4}-\d{2}-\d{2}))?', date_text)
            if date_match:
                start_date = date_match.group(1)
                end_date = date_match.group(2) if date_match.group(2) else start_date
                return {"start_date": start_date, "end_date": end_date}
        
        return None
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call MCP database tools directly."""
        try:
            # Import and use MCP server directly
            from mcp_database_server import EnergyRushMCPServer
            
            server = EnergyRushMCPServer()
            
            if tool_name == "get_order_details":
                return await server.get_order_details(arguments)
            elif tool_name == "get_order_summary":
                return await server.get_order_summary(arguments)
            elif tool_name == "search_orders_by_date":
                return await server.search_orders_by_date(arguments)
            elif tool_name == "get_product_details":
                return await server.get_product_details(arguments)
            elif tool_name == "get_revenue_analysis":
                return await server.get_revenue_analysis(arguments)
            elif tool_name == "get_customer_analysis":
                return await server.get_customer_analysis(arguments)
            elif tool_name == "get_daily_statistics":
                return await server.get_daily_statistics(arguments)
            elif tool_name == "get_date_range_statistics":
                return await server.get_date_range_statistics(arguments)
            elif tool_name == "execute_custom_query":
                return await server.execute_custom_query(arguments)
            else:
                return f"Unknown tool: {tool_name}"
                
        except ImportError as e:
            return f"❌ MCP server not available: {str(e)}"
        except Exception as e:
            return f"❌ Error executing tool: {str(e)}"
    
    def get_project_root(self) -> str:
        """Get the project root directory."""
        import os
        return os.path.dirname(os.path.abspath(__file__))
    
    async def process_query(self, user_input: str) -> str:
        """Process user query and return appropriate response."""
        
        # Classify intent and extract entities
        classification = self.classify_intent(user_input)
        intent = classification["intent"]
        entities = classification["entities"]
        
        print(f"🤖 Detected intent: {intent}, entities: {entities}")
        
        try:
            # Route to appropriate MCP tool
            if intent == "order_details" and "order_id" in entities:
                return await self.call_mcp_tool("get_order_details", {"order_id": entities["order_id"]})
            
            elif intent == "customer_orders" and "customer_name" in entities:
                return await self.call_mcp_tool("get_order_details", {"customer_name": entities["customer_name"]})
            
            elif intent == "order_summary":
                days = entities.get("days", 30)
                return await self.call_mcp_tool("get_order_summary", {"days": days})
            
            elif intent == "product_details":
                if "product_id" in entities:
                    return await self.call_mcp_tool("get_product_details", {"product_id": entities["product_id"]})
                else:
                    return await self.call_mcp_tool("get_product_details", {})
            
            elif intent == "revenue_analysis":
                return await self.call_mcp_tool("get_revenue_analysis", {"days": 30})
            
            elif intent == "customer_analysis":
                if "customer_name" in entities:
                    return await self.call_mcp_tool("get_customer_analysis", {"customer_name": entities["customer_name"]})
                else:
                    return await self.call_mcp_tool("get_customer_analysis", {})
            
            elif intent == "date_search" and "date_text" in entities:
                date_range = self.parse_date_text(entities["date_text"])
                if date_range:
                    return await self.call_mcp_tool("search_orders_by_date", date_range)
                else:
                    return "❌ I couldn't understand the date range. Please use format like 'yesterday', 'last week', or '2025-01-01 to 2025-01-31'."
            
            elif "order_id" in entities:
                # Fallback: if order ID detected, show order details
                return await self.call_mcp_tool("get_order_details", {"order_id": entities["order_id"]})
            
            elif "customer_name" in entities:
                # Fallback: if customer name detected, show customer orders
                return await self.call_mcp_tool("get_order_details", {"customer_name": entities["customer_name"]})
            
            else:
                # General help response
                return self.get_help_response(user_input)
                
        except Exception as e:
            return f"❌ Sorry, I encountered an error processing your request: {str(e)}"
    
    def get_help_response(self, user_input: str) -> str:
        """Provide help and examples for the user."""
        return f"""
🤖 **EnergyRush Admin Assistant**

I can help you with various database queries. Here are some examples:

📋 **Order Queries:**
   • "Show order 123" or "Order details for 123"
   • "Find orders for Customer_01_01"
   • "Orders summary" or "Total orders"
   • "Orders from yesterday" or "Orders last week"

📦 **Product & Inventory:**
   • "Show products" or "Inventory status"
   • "Product 1 details"

💰 **Revenue & Analytics:**
   • "Revenue analysis" or "Sales report"
   • "Customer analysis" or "Top customers"

📅 **Date-based Searches:**
   • "Orders from 2025-01-01 to 2025-01-31"
   • "Sales yesterday" or "Orders this week"

❓ **Your query:** "{user_input}"
**Suggestion:** Try asking more specifically about orders, products, customers, or revenue!
"""


# Integration function for Flask app
def create_enhanced_chatbot_handler():
    """Create chatbot handler for Flask integration."""
    chatbot = EnhancedChatbot()
    
    async def handle_message(message: str) -> str:
        """Handle chatbot message asynchronously."""
        return await chatbot.process_query(message)
    
    def sync_handle_message(message: str) -> str:
        """Synchronous wrapper for Flask."""
        import asyncio
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create new loop in thread if current loop is running
                    import threading
                    import concurrent.futures
                    
                    def run_async():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(handle_message(message))
                        finally:
                            new_loop.close()
                    
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_async)
                        return future.result(timeout=30)
                else:
                    return loop.run_until_complete(handle_message(message))
            except RuntimeError:
                # No event loop exists
                return asyncio.run(handle_message(message))
                
        except Exception as e:
            return f"❌ Chatbot error: {str(e)}"
    
    return sync_handle_message


if __name__ == "__main__":
    # Test the chatbot
    async def test_chatbot():
        chatbot = EnhancedChatbot()
        
        test_queries = [
            "Show order 1",
            "Find orders for Customer_01_01", 
            "Order summary",
            "Revenue analysis",
            "Show products"
        ]
        
        print("🧪 Testing Enhanced Chatbot...")
        for query in test_queries:
            print(f"\n👤 User: {query}")
            response = await chatbot.process_query(query)
            print(f"🤖 Bot: {response[:200]}...")
    
    asyncio.run(test_chatbot())