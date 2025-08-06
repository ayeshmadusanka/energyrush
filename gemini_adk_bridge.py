#!/usr/bin/env python3
"""
Gemini-ADK Bridge System for EnergyRush Chatbot
Uses Gemini as a communication layer to translate user requests into ADK commands
and format ADK responses for user display.
"""

import os
import re
import json
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, date
from dotenv import load_dotenv

from gemini_integration import GeminiChatbot
from enhanced_chatbot import EnhancedChatbot

# Load environment variables
load_dotenv()

class GeminiADKBridge:
    """Bridge system that uses Gemini to communicate with ADK for database queries."""
    
    def __init__(self):
        self.gemini = GeminiChatbot()
        self.enhanced_chatbot = EnhancedChatbot()
        
        # Override Gemini system instructions for bridge mode
        self.bridge_system_instructions = self._get_bridge_system_instructions()
        
    def _get_bridge_system_instructions(self) -> str:
        """Get specialized system instructions for bridge mode."""
        return """You are an intelligent assistant for EnergyRush admin panel that bridges user requests with database operations.

CORE MISSION:
- Handle ALL user queries naturally and helpfully
- For database questions: translate to ADK tools and format results beautifully  
- For general questions: provide helpful, informative responses
- Never redirect users or say you can't help with database queries

AVAILABLE ADK TOOLS:
- get_order_details: Get specific order by ID or customer name
- get_order_summary: Get order summaries with filtering
- search_orders_by_date: Find orders by date range
- get_product_details: Get product information and stock levels
- get_revenue_analysis: Get revenue statistics and trends
- get_customer_analysis: Analyze customer behavior and patterns  
- get_daily_statistics: Get total orders/revenue for specific date
- get_date_range_statistics: Get statistics for date range
- execute_custom_query: Run custom SQL SELECT queries

DATABASE QUERY TRANSLATION PATTERNS:

**Daily Statistics:**
- "orders today" → get_daily_statistics(date="2025-08-07")
- "revenue on July 15" → get_daily_statistics(date="2025-07-15")
- "how many orders yesterday" → get_daily_statistics(date="2025-08-06")

**Date Range Analysis:**
- "orders this week" → get_date_range_statistics(start_date="2025-08-01", end_date="2025-08-07")
- "revenue last month" → get_date_range_statistics(start_date="2025-07-01", end_date="2025-07-31")

**Specific Data:**
- "show order 123" → get_order_details(order_id=123)
- "customer analysis" → get_customer_analysis()
- "revenue trends" → get_revenue_analysis()

RESPONSE GUIDELINES:
1. **For database queries**: Always process them through ADK tools and format results naturally
2. **For general questions**: Provide helpful, informative responses directly
3. **Format all responses** with clear structure, friendly tone, and helpful context
4. **Never redirect users** - handle every query type appropriately
5. **Preserve data accuracy** but make it readable and engaging

WORKFLOW:
1. Analyze user request
2. If database-related: Choose appropriate ADK tool with parameters
3. If general: Respond helpfully with available knowledge  
4. Format all responses in user-friendly manner

Always be helpful and comprehensive - never tell users to use other tools or redirect them elsewhere."""

    def _extract_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format."""
        return datetime.now().strftime('%Y-%m-%d')
    
    def _parse_relative_date(self, user_input: str) -> Optional[str]:
        """Parse relative date expressions like 'today', 'yesterday'."""
        today = datetime.now().date()
        user_lower = user_input.lower()
        
        if 'today' in user_lower:
            return today.strftime('%Y-%m-%d')
        elif 'yesterday' in user_lower:
            yesterday = today.replace(day=today.day-1) if today.day > 1 else today.replace(month=today.month-1, day=31) if today.month > 1 else today.replace(year=today.year-1, month=12, day=31)
            return yesterday.strftime('%Y-%m-%d')
        elif 'tomorrow' in user_lower:
            tomorrow = today.replace(day=today.day+1) if today.day < 28 else today.replace(month=today.month+1, day=1) if today.month < 12 else today.replace(year=today.year+1, month=1, day=1)
            return tomorrow.strftime('%Y-%m-%d')
        
        return None

    async def process_user_query(self, user_message: str) -> Dict[str, Any]:
        """
        Main bridge function that processes user queries through Gemini and ADK.
        
        Returns formatted response ready for display.
        """
        
        try:
            # Step 1: Use Gemini to understand the user request and translate to ADK commands
            translation_prompt = f"""
USER REQUEST: "{user_message}"
CURRENT DATE: {self._extract_current_date()}

Analyze this request and respond accordingly:

**If this is a DATABASE QUERY** (orders, revenue, customers, products, statistics):
Respond with a JSON object:
{{
    "adk_tool": "tool_name",
    "parameters": {{"param1": "value1"}},
    "context": "brief explanation",
    "format_instructions": "how to present results"
}}

**If this is a GENERAL QUESTION** (greetings, explanations, how-to, concepts):
Respond directly with a helpful, conversational answer. No JSON needed.

DATABASE EXAMPLES:
- "orders today" → {{"adk_tool": "get_daily_statistics", "parameters": {{"date": "{self._extract_current_date()}"}}}}
- "show order 123" → {{"adk_tool": "get_order_details", "parameters": {{"order_id": 123}}}}
- "revenue analysis" → {{"adk_tool": "get_revenue_analysis", "parameters": {{}}}}

GENERAL EXAMPLES:
- "hello" → "Hi! I'm here to help with your EnergyRush admin panel..."
- "what is e-commerce?" → "E-commerce refers to buying and selling..."
- "how do I use this?" → "You can use this admin panel to..."
"""
            
            # Get translation from Gemini
            gemini_response = self.gemini.generate_response(
                translation_prompt,
                context=self.bridge_system_instructions
            )
            
            if not gemini_response['success']:
                return {
                    'success': False,
                    'response': f"I'm having trouble understanding your request. {gemini_response['response']}"
                }
            
            # Step 2: Parse Gemini's translation
            try:
                # Extract JSON from Gemini response
                response_text = gemini_response['response']
                
                # Check if this is a general question (no JSON tool call needed)
                if not re.search(r'\{.*"adk_tool".*\}', response_text, re.DOTALL):
                    # This is a general question - return Gemini's direct response
                    return {
                        'success': True,
                        'response': response_text,
                        'bridge_info': {
                            'type': 'general_question',
                            'handled_by': 'gemini_direct',
                            'no_database_needed': True
                        }
                    }
                
                # Find JSON in response for database queries
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    translation = json.loads(json_match.group())
                else:
                    # Fallback: try to extract tool and parameters from text
                    return await self._fallback_query_processing(user_message)
                    
            except (json.JSONDecodeError, KeyError) as e:
                # If parsing fails but response exists, it might be a general answer
                if gemini_response.get('response'):
                    return {
                        'success': True,
                        'response': gemini_response['response'],
                        'bridge_info': {
                            'type': 'general_question',
                            'handled_by': 'gemini_direct',
                            'parsing_failed_fallback': True
                        }
                    }
                return await self._fallback_query_processing(user_message)
            
            # Step 3: Execute ADK tool with translated parameters
            adk_tool = translation.get('adk_tool')
            parameters = translation.get('parameters', {})
            context = translation.get('context', '')
            format_instructions = translation.get('format_instructions', '')
            
            if not adk_tool:
                return {
                    'success': False,
                    'response': "I couldn't determine which database tool to use for your request."
                }
            
            # Execute ADK tool
            adk_result = await self._execute_adk_tool(adk_tool, parameters)
            
            # Step 4: Use Gemini to format ADK results for user display
            formatting_prompt = f"""
USER ORIGINAL REQUEST: "{user_message}"
CONTEXT: {context}
ADK TOOL USED: {adk_tool}
PARAMETERS: {json.dumps(parameters)}

ADK RAW RESULT:
{adk_result}

FORMAT INSTRUCTIONS: {format_instructions}

Please format this database result into a friendly, conversational response for the user. 
Make it easy to read and understand, but preserve all the important data and numbers.
Use clear headings, bullet points, and natural language.
"""
            
            formatted_response = self.gemini.generate_response(formatting_prompt)
            
            if formatted_response['success']:
                return {
                    'success': True,
                    'response': formatted_response['response'],
                    'bridge_info': {
                        'adk_tool_used': adk_tool,
                        'parameters_used': parameters,
                        'context': context
                    }
                }
            else:
                # Fallback to raw ADK result if formatting fails
                return {
                    'success': True,
                    'response': f"Here's the information from our database:\n\n{adk_result}",
                    'bridge_info': {
                        'adk_tool_used': adk_tool,
                        'parameters_used': parameters,
                        'formatting_failed': True
                    }
                }
                
        except Exception as e:
            return {
                'success': False,
                'response': f"I encountered an error while processing your request: {str(e)}"
            }
    
    async def _execute_adk_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute an ADK tool via MCP call."""
        
        try:
            # Use the enhanced_chatbot's MCP integration
            result = await self.enhanced_chatbot.call_mcp_tool(tool_name, parameters)
            return str(result)
            
        except Exception as e:
            return f"❌ Error executing ADK tool '{tool_name}' via MCP: {str(e)}"
    
    async def _fallback_query_processing(self, user_message: str) -> Dict[str, Any]:
        """Fallback processing when Gemini translation fails."""
        
        user_lower = user_message.lower()
        
        # Simple pattern matching for common queries
        if any(word in user_lower for word in ['order', 'orders']) and any(word in user_lower for word in ['today', 'yesterday']):
            # Daily orders query
            target_date = self._parse_relative_date(user_message) or self._extract_current_date()
            adk_result = await self._execute_adk_tool('get_daily_statistics', {'date': target_date})
            
            return {
                'success': True,
                'response': f"Here are the order statistics for {target_date}:\n\n{adk_result}",
                'bridge_info': {'fallback_used': True}
            }
        
        elif 'revenue' in user_lower or 'sales' in user_lower:
            # Revenue analysis
            adk_result = await self._execute_adk_tool('get_revenue_analysis', {})
            
            return {
                'success': True,
                'response': f"Here's the revenue analysis:\n\n{adk_result}",
                'bridge_info': {'fallback_used': True}
            }
        
        else:
            # Use enhanced chatbot directly
            try:
                result = await self.enhanced_chatbot.process_query(user_message)
                return {
                    'success': True,
                    'response': result.get('response', 'No response available'),
                    'bridge_info': {'direct_adk_used': True}
                }
            except Exception as e:
                return {
                    'success': False,
                    'response': f"I'm not sure how to help with that request. Could you be more specific?"
                }

    def test_connection(self) -> Dict[str, Any]:
        """Test the bridge system connectivity."""
        
        gemini_test = self.gemini.test_connection()
        
        try:
            adk_available = bool(self.enhanced_chatbot)
            adk_tools_count = len([
                'get_order_details', 'get_order_summary', 'search_orders_by_date',
                'get_product_details', 'get_revenue_analysis', 'get_customer_analysis',
                'get_daily_statistics', 'get_date_range_statistics', 'execute_custom_query'
            ])
        except Exception as e:
            adk_available = False
            adk_tools_count = 0
        
        return {
            'gemini_connected': gemini_test['connection_successful'],
            'gemini_response': gemini_test['test_response'][:50] + "..." if gemini_test['connection_successful'] else gemini_test['test_response'],
            'adk_available': adk_available,
            'adk_tools_count': adk_tools_count,
            'bridge_ready': gemini_test['connection_successful'] and adk_available,
            'current_date': self._extract_current_date()
        }


# Factory function
def create_gemini_adk_bridge() -> Optional['GeminiADKBridge']:
    """Factory function to create Gemini-ADK bridge instance."""
    
    try:
        bridge = GeminiADKBridge()
        return bridge
    except Exception as e:
        print(f"Failed to initialize Gemini-ADK bridge: {e}")
        return None


if __name__ == "__main__":
    # Test the bridge system
    async def test_bridge():
        print("🌉 Testing Gemini-ADK Bridge System")
        print("=" * 40)
        
        try:
            bridge = GeminiADKBridge()
            
            # Test connection
            connection_test = bridge.test_connection()
            print(f"🤖 Gemini Connected: {connection_test['gemini_connected']}")
            print(f"🔧 ADK Available: {connection_test['adk_available']}")
            print(f"🛠️  ADK Tools: {connection_test['adk_tools_count']}")
            print(f"🌉 Bridge Ready: {connection_test['bridge_ready']}")
            print(f"📅 Current Date: {connection_test['current_date']}")
            
            if connection_test['bridge_ready']:
                print(f"\n🧪 Testing Sample Queries:")
                
                test_queries = [
                    "orders today",
                    "show order 1", 
                    "revenue analysis"
                ]
                
                for query in test_queries:
                    print(f"\n📝 Testing: '{query}'")
                    result = await bridge.process_user_query(query)
                    if result['success']:
                        print(f"✅ Success: {result['response'][:100]}...")
                        if 'bridge_info' in result:
                            print(f"🔧 Used tool: {result['bridge_info'].get('adk_tool_used', 'N/A')}")
                    else:
                        print(f"❌ Failed: {result['response']}")
                
                print(f"\n✅ Bridge system testing complete!")
            else:
                print(f"\n❌ Bridge system not ready - check connections")
                
        except Exception as e:
            print(f"❌ Error testing bridge: {e}")
    
    # Run test
    asyncio.run(test_bridge())