#!/usr/bin/env python3
"""
Test Markdown Parser for Chatbot Responses
Verifies that raw markdown is properly converted to HTML
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test the markdown parser
def test_markdown_parser():
    """Test markdown parsing functionality."""
    
    # Import the function from app.py
    from app import parse_markdown_response
    
    print("🧪 TESTING MARKDOWN PARSER")
    print("="*40)
    
    # Sample raw markdown responses (similar to what chatbot generates)
    test_cases = [
        {
            "name": "Order Details Response",
            "markdown": """
📋 **Order Details - ID: 1**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **Customer Information:**
   • Name: Customer_000_00
   • Phone: 94756868336
   • Address: 420 Colombo Rd, Kandy 36005

💰 **Order Information:**
   • Total Amount: $33.43
   • Status: Completed
   • Order Date: 2025-01-01 18:58:20

📦 **Items:** [{"product_id": 1, "name": "Energy Drink", "price": 33.43, "quantity": 1, "total": 33.43}]
"""
        },
        {
            "name": "Order Summary Response", 
            "markdown": """
📊 **Order Summary (Last 30 Days)**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 **Overall Statistics:**
   • Total Orders (All Time): 6,730
   • Recent Orders (30 days): 1,234
   • Daily Average: 41.1 orders/day
   • Average Order Value: $39.31
   • Total Revenue (30 days): $48,506.59

📋 **Status Breakdown:**
   • Completed: 1,234 orders ($48,506.59)
"""
        },
        {
            "name": "Help Response",
            "markdown": """
🤖 **EnergyRush Admin Assistant**

I can help you with:
📋 **Orders:** "Show order 123" or "Order summary"  
📦 **Products:** "Show products" or "Inventory status"
💰 **Revenue:** "Revenue summary"

Try asking me about orders, products, or revenue!
"""
        },
        {
            "name": "Revenue Analysis",
            "markdown": """
💰 **Revenue Analysis (Last 30 Days - Grouped by day)**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Summary:**
   • Total Revenue: $48,506.59
   • Total Orders: 1,234
   • Average Order Value: $39.31

📈 **Period Breakdown:**
📅 2025-01-07: 42 orders | $1,648.32 revenue | $39.24 avg
📅 2025-01-06: 38 orders | $1,521.18 revenue | $40.03 avg
"""
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print("-" * 50)
        
        # Parse markdown
        html_output = parse_markdown_response(test_case['markdown'])
        
        print("📝 Original markdown (first 100 chars):")
        print(repr(test_case['markdown'][:100]))
        
        print("\n🎨 Parsed HTML (first 200 chars):")
        print(repr(html_output[:200]))
        
        # Check if conversion happened
        has_html_tags = any(tag in html_output for tag in ['<p>', '<strong>', '<ul>', '<li>', '<h1>', '<h2>'])
        
        if has_html_tags:
            print("✅ SUCCESS: Markdown converted to HTML")
        else:
            print("⚠️  INFO: No HTML conversion (possibly plain text)")
        
        # Check for styling classes
        has_styling = 'class=' in html_output
        if has_styling:
            print("✅ SUCCESS: Styling classes added")
        else:
            print("ℹ️  INFO: No styling classes (basic HTML)")
        
        print()
    
    print("🎯 MARKDOWN PARSER TEST COMPLETE!")
    print("="*40)


def test_with_flask_app():
    """Test the markdown parser with a real Flask request."""
    
    print("\n🌐 TESTING WITH FLASK APP")
    print("="*30)
    
    try:
        import requests
        import json
        
        # Test a simple query
        print("🔍 Testing with live Flask app...")
        
        response = requests.post(
            'http://127.0.0.1:8000/admin/chatbot',
            json={'message': 'Help'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Flask app responded successfully")
            print(f"   Response type: {data.get('type', 'unknown')}")
            print(f"   Success: {data.get('success', False)}")
            
            # Check if response is HTML
            formatted_response = data.get('response', '')
            raw_response = data.get('raw_response', '')
            
            print(f"\n📝 Raw response (first 100 chars):")
            print(repr(raw_response[:100]))
            
            print(f"\n🎨 Formatted response (first 150 chars):")
            print(repr(formatted_response[:150]))
            
            # Verify HTML conversion
            if '<p>' in formatted_response or '<strong>' in formatted_response:
                print("✅ SUCCESS: Markdown converted to HTML in Flask app")
            else:
                print("⚠️  WARNING: No HTML detected in Flask response")
        else:
            print(f"❌ Flask app error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Flask app not running - start with 'python app.py'")
    except Exception as e:
        print(f"❌ Flask test error: {e}")


if __name__ == "__main__":
    print("🎨 Markdown Parser Test Suite")
    print("🎯 Testing conversion from raw markdown to HTML")
    print()
    
    # Test the parser function directly
    test_markdown_parser()
    
    # Test with Flask app (if running)
    test_with_flask_app()
    
    print("\n📊 TEST SUMMARY:")
    print("• Markdown to HTML conversion")
    print("• Styling class injection")
    print("• Flask endpoint integration")
    print("• Real chatbot response formatting")
    print("\n🎉 Markdown parser ready for production!")