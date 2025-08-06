#!/usr/bin/env python3
"""
Gemini API Integration for EnergyRush Chatbot
Handles general conversational queries while ADK handles database tasks
"""

import os
import requests
import json
from typing import Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiChatbot:
    """Gemini API integration for general conversational AI."""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.system_instructions = self._get_system_instructions()
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    def _get_system_instructions(self) -> str:
        """Get system instructions for Gemini to handle all queries."""
        return """You are an AI assistant for EnergyRush, an energy drink e-commerce platform admin panel. 

YOUR ROLE:
- Handle ALL user queries with helpful, accurate responses
- Process both general questions AND database-related requests
- Provide friendly, professional assistance for any admin panel needs

IMPORTANT RESTRICTIONS:
- You MUST NOT use any outside data, web search, or external information
- You can ONLY provide information that is explicitly given to you in the conversation
- For current events or external information, politely decline and redirect to relevant topics

CAPABILITIES:
- Answer general questions about e-commerce, business, and technology
- Explain admin panel features and functionality
- Provide helpful guidance and support
- Handle conversational interactions naturally
- Process any business-related questions with available data

RESPONSE STYLE:
- Be conversational and helpful
- Use clear, professional language
- Provide specific information when available
- Be friendly and supportive
- Keep responses focused and relevant

You should handle ALL queries naturally without redirecting users elsewhere. Be a comprehensive assistant for the EnergyRush admin panel."""
    
    def generate_response(self, message: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using Gemini API."""
        
        try:
            # Prepare the prompt with system instructions
            full_prompt = f"{self.system_instructions}\n\nUser message: {message}"
            
            if context:
                full_prompt += f"\n\nContext provided: {context}"
            
            # Prepare API request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": full_prompt
                            }
                        ]
                    }
                ]
            }
            
            # Make API request
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': self.api_key
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract the generated text
                if 'candidates' in response_data and len(response_data['candidates']) > 0:
                    candidate = response_data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        generated_text = candidate['content']['parts'][0]['text']
                        
                        return {
                            'success': True,
                            'response': generated_text.strip(),
                            'type': 'gemini_chat',
                            'usage': response_data.get('usageMetadata', {})
                        }
                
                return {
                    'success': False,
                    'response': 'I apologize, but I received an unexpected response format. Please try again.',
                    'type': 'gemini_error',
                    'error': 'Invalid response format'
                }
                
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                print(f"Gemini API Error: {error_msg}")
                
                return {
                    'success': False,
                    'response': 'I apologize, but I\'m having trouble connecting to my language model. Please try again later.',
                    'type': 'gemini_error',
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'response': 'I apologize, but my response is taking too long. Please try a shorter question.',
                'type': 'gemini_error',
                'error': 'Request timeout'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            print(f"Gemini API Network Error: {error_msg}")
            
            return {
                'success': False,
                'response': 'I apologize, but I\'m having network connectivity issues. Please try again later.',
                'type': 'gemini_error',
                'error': error_msg
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"Gemini API Unexpected Error: {error_msg}")
            
            return {
                'success': False,
                'response': 'I apologize, but I encountered an unexpected error. Please try again.',
                'type': 'gemini_error',
                'error': error_msg
            }
    
    def is_database_query(self, message: str) -> bool:
        """Determine if the message requires database access (should use ADK)."""
        
        database_keywords = [
            # Order-related
            'order', 'orders', 'show order', 'find order', 'order details',
            'order summary', 'order status', 'order history',
            
            # Product-related  
            'product', 'products', 'inventory', 'stock', 'show products',
            'product details', 'stock level', 'out of stock',
            
            # Customer-related
            'customer', 'customers', 'customer analysis', 'top customers',
            'customer behavior', 'customer history', 'find customer',
            
            # Revenue-related
            'revenue', 'sales', 'earnings', 'income', 'revenue analysis',
            'sales report', 'financial', 'total revenue', 'daily revenue',
            
            # General data queries
            'summary', 'statistics', 'stats', 'analytics', 'report',
            'total', 'count', 'how many', 'list', 'show all'
        ]
        
        message_lower = message.lower()
        
        # Check for database keywords
        for keyword in database_keywords:
            if keyword in message_lower:
                return True
        
        # Check for specific patterns
        import re
        
        # Order ID patterns (numbers that might be order IDs)
        if re.search(r'show.*\d+|order.*\d+|find.*\d+', message_lower):
            return True
        
        # Customer name patterns
        if re.search(r'customer[_\s]+\w+', message_lower):
            return True
        
        return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the Gemini API connection."""
        
        test_message = "Hello, can you confirm you're working?"
        result = self.generate_response(test_message)
        
        return {
            'api_key_configured': bool(self.api_key),
            'connection_successful': result['success'],
            'test_response': result['response'] if result['success'] else result.get('error', 'Unknown error')
        }


def create_gemini_chatbot() -> Optional[GeminiChatbot]:
    """Factory function to create Gemini chatbot instance."""
    
    try:
        chatbot = GeminiChatbot()
        return chatbot
    except Exception as e:
        print(f"Failed to initialize Gemini chatbot: {e}")
        return None


if __name__ == "__main__":
    # Test the Gemini integration
    print("🤖 Testing Gemini API Integration")
    print("="*40)
    
    try:
        gemini = GeminiChatbot()
        
        # Test connection
        connection_test = gemini.test_connection()
        print(f"API Key Configured: {connection_test['api_key_configured']}")
        print(f"Connection Successful: {connection_test['connection_successful']}")
        print(f"Test Response: {connection_test['test_response'][:100]}...")
        
        # Test query classification
        test_queries = [
            "Hello, how are you?",  # Should use Gemini
            "Show order 123",       # Should use ADK
            "What is e-commerce?",  # Should use Gemini
            "Revenue analysis",     # Should use ADK
        ]
        
        print(f"\n🔍 Query Classification Tests:")
        for query in test_queries:
            is_db_query = gemini.is_database_query(query)
            handler = "ADK (Database)" if is_db_query else "Gemini (Chat)"
            print(f"   '{query}' → {handler}")
            
        print(f"\n✅ Gemini integration ready!")
        
    except Exception as e:
        print(f"❌ Error testing Gemini: {e}")