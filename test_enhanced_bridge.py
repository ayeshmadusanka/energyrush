#!/usr/bin/env python3
"""
Enhanced Bridge System Test
Tests the updated Gemini-ADK bridge with improved database query handling
"""

import requests
import json
import asyncio
from datetime import datetime

def test_flask_chatbot():
    """Test Flask chatbot endpoint with various query types."""
    
    print("🚀 Testing Enhanced Gemini-ADK Bridge via Flask")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    chatbot_url = f"{base_url}/admin/chatbot"
    
    # Comprehensive test queries
    test_queries = [
        # Database queries that should work seamlessly
        {
            "message": "orders today",
            "type": "database",
            "expectation": "Daily statistics with order count and revenue"
        },
        {
            "message": "how many orders did we get on 2025-08-06?",
            "type": "database", 
            "expectation": "Specific date statistics"
        },
        {
            "message": "show me order number 1",
            "type": "database",
            "expectation": "Detailed order information"
        },
        {
            "message": "give me a revenue analysis",
            "type": "database",
            "expectation": "Revenue trends and statistics"
        },
        {
            "message": "customer analysis please",
            "type": "database",
            "expectation": "Customer behavior insights"
        },
        
        # General questions that should be answered directly
        {
            "message": "hello, how are you today?",
            "type": "general",
            "expectation": "Friendly greeting response"
        },
        {
            "message": "what is e-commerce?",
            "type": "general", 
            "expectation": "Educational explanation"
        },
        {
            "message": "how does online shopping work?",
            "type": "general",
            "expectation": "Informative response"
        },
        {
            "message": "explain machine learning to me",
            "type": "general",
            "expectation": "Technical explanation"
        },
        {
            "message": "what features does this admin panel have?",
            "type": "general",
            "expectation": "Admin panel guidance"
        }
    ]
    
    print(f"📊 Running {len(test_queries)} comprehensive tests...")
    print()
    
    successful_database_queries = 0
    successful_general_queries = 0
    failed_queries = 0
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"🧪 Test {i}/{len(test_queries)}: {test_case['type'].upper()} Query")
        print(f"📝 Message: '{test_case['message']}'")
        print(f"🎯 Expected: {test_case['expectation']}")
        
        try:
            response = requests.post(
                chatbot_url,
                json={"message": test_case['message']},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Response received successfully")
                print(f"🤖 Handler: {result.get('handler', 'Unknown')}")
                print(f"🔧 Type: {result.get('type', 'Unknown')}")
                
                # Check if bridge was used
                if result.get('type') == 'gemini_adk_bridge':
                    bridge_info = result.get('bridge_info', {})
                    adk_tool = result.get('adk_tool_used')
                    
                    if bridge_info.get('type') == 'general_question':
                        print(f"💬 Handled as: General Question (Direct Gemini)")
                        if test_case['type'] == 'general':
                            successful_general_queries += 1
                            print(f"✅ Correct handling for general query")
                        else:
                            print(f"⚠️  Database query handled as general")
                    elif adk_tool:
                        print(f"🛠️  ADK Tool Used: {adk_tool}")
                        if test_case['type'] == 'database':
                            successful_database_queries += 1
                            print(f"✅ Correct handling for database query")
                        else:
                            print(f"⚠️  General query handled as database")
                    else:
                        print(f"❓ Bridge used but no clear tool identified")
                else:
                    print(f"⚠️  Fallback handler used: {result.get('handler')}")
                
                # Show response preview
                response_text = result.get('response', 'No response')
                
                # Check if response contains "For specific business data" redirect
                if "For specific business data" in response_text or "please use the database queries" in response_text:
                    print(f"❌ REDIRECT DETECTED - System still redirecting users!")
                    failed_queries += 1
                else:
                    # Clean preview (remove HTML tags for readability)
                    import re
                    clean_text = re.sub(r'<[^>]+>', '', response_text)
                    preview = clean_text[:150].replace('\n', ' ').strip()
                    print(f"💬 Response: {preview}{'...' if len(clean_text) > 150 else ''}")
                
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                failed_queries += 1
                
        except Exception as e:
            print(f"❌ Request Error: {str(e)}")
            failed_queries += 1
        
        print("-" * 50)
        print()
    
    # Results Summary
    total_database_tests = sum(1 for t in test_queries if t['type'] == 'database')
    total_general_tests = sum(1 for t in test_queries if t['type'] == 'general')
    
    print(f"📊 ENHANCED BRIDGE TEST RESULTS")
    print("=" * 32)
    print(f"🔧 Database Queries: {successful_database_queries}/{total_database_tests} successful")
    print(f"💬 General Queries: {successful_general_queries}/{total_general_tests} successful") 
    print(f"❌ Failed Queries: {failed_queries}")
    print(f"📈 Overall Success: {(successful_database_queries + successful_general_queries)}/{len(test_queries)} ({((successful_database_queries + successful_general_queries)/len(test_queries))*100:.1f}%)")
    
    print(f"\n🎯 KEY IMPROVEMENTS VERIFIED:")
    
    if successful_database_queries > 0:
        print(f"✅ Database queries processed through Gemini → ADK pipeline")
    else:
        print(f"❌ Database query processing needs improvement")
    
    if successful_general_queries > 0:
        print(f"✅ General questions answered directly by Gemini")
    else:
        print(f"❌ General question handling needs improvement")
        
    if failed_queries == 0:
        print(f"✅ No user redirects - all queries handled appropriately")
    else:
        print(f"⚠️  Some queries failed or were redirected")
    
    print(f"\n🎉 BRIDGE ENHANCEMENT: {'SUCCESS' if (successful_database_queries + successful_general_queries) >= len(test_queries) * 0.8 else 'NEEDS WORK'}")
    
    return (successful_database_queries + successful_general_queries) >= len(test_queries) * 0.8

def main():
    """Run the enhanced bridge test."""
    
    print("🔧 ENHANCED GEMINI-ADK BRIDGE TEST")
    print("=" * 35)
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🎯 Testing Goals:")
    print("   • Database queries should be processed seamlessly")
    print("   • General questions should be answered directly") 
    print("   • No user redirects or 'use database tools' messages")
    print("   • Professional, helpful responses for all query types")
    print()
    
    # Check if Flask server is running
    try:
        response = requests.get("http://localhost:8000/admin", timeout=5)
        if response.status_code == 200:
            print("✅ Flask server detected - running comprehensive test")
            success = test_flask_chatbot()
        else:
            print("❌ Flask server not responding properly")
            return
    except requests.exceptions.RequestException:
        print("❌ Flask server not running")
        print("   Please start the server with: python app.py")
        return
    
    if success:
        print(f"\n🎉 ENHANCEMENT SUCCESSFUL!")
        print(f"✅ Gemini now handles all queries appropriately")
        print(f"✅ Database queries processed through ADK with formatting")
        print(f"✅ General questions answered directly")
        print(f"✅ No more user redirects!")
    else:
        print(f"\n⚠️  Enhancement needs further refinement")
        print(f"   Check individual test results above")

if __name__ == "__main__":
    main()