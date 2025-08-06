#!/usr/bin/env python3
"""
Test the fixed markdown parser with the problematic response
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fixed_markdown_parsing():
    """Test the fixed markdown parser with the exact problematic text."""
    
    from app import parse_markdown_response
    
    # The exact problematic text from the user
    problematic_text = """📋 **Order Details - ID: 6714**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **Customer Information:**
• Name: Customer_218_12
• Phone: 94753131685
• Address: 203 Colombo Rd, Kandy 76300

💰 **Order Information:**
• Total Amount: $42.23
• Status: Completed
• Order Date: 2025-08-07 20:38:57.000000

📦 **Items:** [{"product_id": 1, "name": "Energy Drink", "price": 42.23, "quantity": 1, "total": 42.23}]"""

    print("🔧 TESTING FIXED MARKDOWN PARSER")
    print("="*50)
    
    print("📝 Original problematic text:")
    print(repr(problematic_text[:100]))
    print()
    
    # Parse the text
    parsed_html = parse_markdown_response(problematic_text)
    
    print("🎨 Parsed HTML result:")
    print(parsed_html)
    print()
    
    # Check for specific improvements
    improvements = []
    
    if '<div class="border-t-2 border-gray-300 my-3"></div>' in parsed_html:
        improvements.append("✅ Unicode line separators (━━━━━━━━) converted to divider")
    else:
        improvements.append("❌ Line separators not properly converted")
    
    if '<li class="flex items-start"><span class="text-blue-500 mr-2">•</span><span>' in parsed_html:
        improvements.append("✅ Bullet points (•) converted to styled list items")
    else:
        improvements.append("❌ Bullet points not properly converted")
    
    if '<strong class="font-semibold text-gray-800">' in parsed_html:
        improvements.append("✅ Bold text (**text**) properly styled")
    else:
        improvements.append("❌ Bold text not properly styled")
    
    if '<p class="mb-2 leading-relaxed">' in parsed_html:
        improvements.append("✅ Paragraphs properly spaced")
    else:
        improvements.append("❌ Paragraph spacing not applied")
    
    print("🎯 IMPROVEMENT CHECKLIST:")
    for improvement in improvements:
        print(f"   {improvement}")
    
    print()
    
    # Count successful conversions
    success_count = len([i for i in improvements if i.startswith("✅")])
    total_count = len(improvements)
    
    print(f"📊 SUCCESS RATE: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 ALL IMPROVEMENTS SUCCESSFULLY APPLIED!")
        return True
    else:
        print("⚠️  Some improvements still needed")
        return False

def test_with_live_app():
    """Test with the live Flask application."""
    
    print("\n🌐 TESTING WITH LIVE FLASK APP")
    print("="*35)
    
    try:
        import requests
        
        # Test the exact query that was problematic
        response = requests.post(
            'http://127.0.0.1:8000/admin/chatbot',
            json={'message': 'Show order 6714'},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            formatted_response = data.get('response', '')
            
            print("✅ Flask app responded successfully")
            print()
            print("🎨 Formatted response preview:")
            print(formatted_response[:300])
            print("...")
            
            # Check for the improvements
            has_divider = 'border-t-2 border-gray-300' in formatted_response
            has_bullet_styling = 'text-blue-500 mr-2' in formatted_response
            has_proper_bold = 'font-semibold text-gray-800' in formatted_response
            
            print("\n🔍 Improvement verification:")
            print(f"   Divider lines: {'✅' if has_divider else '❌'}")
            print(f"   Styled bullets: {'✅' if has_bullet_styling else '❌'}")  
            print(f"   Proper bold text: {'✅' if has_proper_bold else '❌'}")
            
            return has_divider and has_bullet_styling and has_proper_bold
        else:
            print(f"❌ Flask app error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing with Flask app: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixed Markdown Parser Test")
    print("🎯 Testing improvements for bullet points and Unicode characters")
    print()
    
    # Test the parser directly
    parser_success = test_fixed_markdown_parsing()
    
    # Test with Flask app
    app_success = test_with_live_app()
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Parser improvements: {'✅' if parser_success else '❌'}")
    print(f"   Flask integration: {'✅' if app_success else '❌'}")
    
    if parser_success and app_success:
        print("\n🎉 MARKDOWN PARSING FULLY FIXED!")
        print("✅ Bullet points, line separators, and formatting all working correctly")
    else:
        print("\n⚠️  Additional fixes may be needed")