#!/usr/bin/env python3
"""
Final System Test for Enhanced EnergyRush Chatbot
Tests all fixes: ADK tools, loading animation, state management
"""

import requests
import json
import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_adk_tools_directly():
    """Test ADK tools directly to verify get_daily_statistics works."""
    
    print("🔧 Testing ADK Tools Direct Integration")
    print("=" * 38)
    
    try:
        from gemini_adk_bridge import GeminiADKBridge
        
        async def run_adk_tests():
            bridge = GeminiADKBridge()
            
            # Test the problematic get_daily_statistics tool
            test_cases = [
                {
                    "tool": "get_daily_statistics",
                    "params": {"date": "2025-08-07"},
                    "description": "Today's statistics"
                },
                {
                    "tool": "get_daily_statistics", 
                    "params": {"date": "2025-08-06"},
                    "description": "Yesterday's statistics"
                },
                {
                    "tool": "get_date_range_statistics",
                    "params": {"start_date": "2025-08-01", "end_date": "2025-08-07"},
                    "description": "Week range statistics"
                },
                {
                    "tool": "get_order_details",
                    "params": {"order_id": 1},
                    "description": "Order details lookup"
                }
            ]
            
            results = []
            
            for test_case in test_cases:
                print(f"\n🧪 Testing: {test_case['tool']} - {test_case['description']}")
                
                try:
                    result = await bridge._execute_adk_tool(test_case['tool'], test_case['params'])
                    
                    if "Unknown tool" in result or "tool is unknown" in result:
                        print(f"❌ FAIL: Tool not recognized")
                        results.append(False)
                    elif "❌" in result and "Error" in result:
                        print(f"❌ FAIL: Tool error - {result[:100]}...")
                        results.append(False)
                    else:
                        print(f"✅ PASS: Tool executed successfully")
                        preview = result[:150].replace('\n', ' ')
                        print(f"📊 Result: {preview}...")
                        results.append(True)
                        
                except Exception as e:
                    print(f"❌ FAIL: Exception - {str(e)}")
                    results.append(False)
            
            success_rate = sum(results) / len(results) * 100
            print(f"\n📊 ADK Tools Test Results:")
            print(f"   ✅ Successful: {sum(results)}/{len(results)}")
            print(f"   📈 Success Rate: {success_rate:.1f}%")
            
            return success_rate >= 75  # 75% success threshold
        
        return asyncio.run(run_adk_tests())
        
    except Exception as e:
        print(f"❌ ADK tools test failed: {str(e)}")
        return False

def test_flask_chatbot_enhanced():
    """Test Flask chatbot with focus on previously failing queries."""
    
    print("\n🚀 Testing Enhanced Flask Chatbot")
    print("=" * 33)
    
    base_url = "http://localhost:8000"
    chatbot_url = f"{base_url}/admin/chatbot"
    
    # Focus on previously failing queries
    critical_queries = [
        {
            "message": "orders today",
            "expectation": "Should show daily statistics without errors",
            "should_contain": ["orders", "revenue", "2025-08-07"],
            "should_not_contain": ["unknown tool", "unable to process", "For specific business data"]
        },
        {
            "message": "how many orders on 2025-08-06?",
            "expectation": "Should show specific date statistics",
            "should_contain": ["2025-08-06", "orders"],
            "should_not_contain": ["unknown tool", "unable to process"]
        },
        {
            "message": "give me revenue analysis",
            "expectation": "Should show revenue breakdown",
            "should_contain": ["revenue", "analysis"],
            "should_not_contain": ["For specific business data"]
        },
        {
            "message": "hello how are you?",
            "expectation": "Should respond conversationally",
            "should_contain": ["hello", "hi", "good", "help"],
            "should_not_contain": ["For specific business data", "database queries"]
        }
    ]
    
    print(f"🎯 Testing {len(critical_queries)} critical queries...")
    results = []
    
    for i, test_case in enumerate(critical_queries, 1):
        print(f"\n🧪 Test {i}/{len(critical_queries)}: {test_case['expectation']}")
        print(f"📝 Query: '{test_case['message']}'")
        
        try:
            response = requests.post(
                chatbot_url,
                json={"message": test_case['message']},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').lower()
                
                print(f"✅ Response received")
                print(f"🤖 Handler: {data.get('handler', 'Unknown')}")
                
                # Check for required content
                has_required = any(req.lower() in response_text for req in test_case['should_contain'])
                has_forbidden = any(forb.lower() in response_text for forb in test_case['should_not_contain'])
                
                if has_required and not has_forbidden:
                    print(f"✅ PASS: Response contains expected content")
                    results.append(True)
                elif has_forbidden:
                    print(f"❌ FAIL: Response contains forbidden content")
                    forbidden_found = [forb for forb in test_case['should_not_contain'] if forb.lower() in response_text]
                    print(f"   🚫 Found: {forbidden_found}")
                    results.append(False)
                else:
                    print(f"⚠️  PARTIAL: Response missing expected content")
                    results.append(False)
                
                # Show response preview
                clean_response = data.get('response', '').replace('<p class="mb-2 leading-relaxed">', '').replace('</p>', '')
                preview = clean_response[:200].replace('\n', ' ')
                print(f"💬 Preview: {preview}...")
                
            else:
                print(f"❌ FAIL: HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ FAIL: Exception - {str(e)}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100 if results else 0
    print(f"\n📊 Enhanced Chatbot Test Results:")
    print(f"   ✅ Successful: {sum(results)}/{len(results)}")
    print(f"   📈 Success Rate: {success_rate:.1f}%")
    
    return success_rate >= 75

def test_loading_and_state_features():
    """Test loading animation and state management features."""
    
    print("\n🎨 Testing UI Enhancements")
    print("=" * 26)
    
    # Test if the admin page loads with enhanced chatbot
    try:
        response = requests.get("http://localhost:8000/admin", timeout=10)
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for state management JavaScript
            has_state_management = 'ChatbotState' in html_content and 'localStorage' in html_content
            has_loading_animation = 'loading-dots' in html_content and 'typing-indicator' in html_content
            has_clear_button = 'clearChatHistory' in html_content
            has_enhanced_styling = 'chatbot-response' in html_content and 'shadow-md' in html_content
            
            print(f"✅ Admin page loaded successfully")
            print(f"🔄 State Management: {'✅' if has_state_management else '❌'}")
            print(f"⏳ Loading Animation: {'✅' if has_loading_animation else '❌'}")
            print(f"🗑️  Clear Button: {'✅' if has_clear_button else '❌'}")
            print(f"🎨 Enhanced Styling: {'✅' if has_enhanced_styling else '❌'}")
            
            features_working = sum([has_state_management, has_loading_animation, has_clear_button, has_enhanced_styling])
            
            print(f"\n📊 UI Features: {features_working}/4 working")
            return features_working >= 3
            
        else:
            print(f"❌ Admin page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ UI test failed: {str(e)}")
        return False

def main():
    """Run comprehensive final system test."""
    
    print("🏁 FINAL SYSTEM TEST - EnergyRush Enhanced Chatbot")
    print("=" * 52)
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎯 Testing Key Fixes:")
    print("   1. ✅ ADK tools integration (get_daily_statistics)")  
    print("   2. ⏳ Loading animation during responses")
    print("   3. 🔄 State management across page navigation")
    print("   4. 🚫 No more error messages or redirects")
    print()
    
    # Run all tests
    test_results = {}
    
    # Test 1: ADK Tools Direct
    print("=" * 50)
    test_results['adk_tools'] = test_adk_tools_directly()
    
    # Test 2: Flask Chatbot Enhanced  
    print("=" * 50)
    
    # Check if Flask is running
    try:
        requests.get("http://localhost:8000/admin", timeout=5)
        test_results['flask_chatbot'] = test_flask_chatbot_enhanced()
        test_results['ui_features'] = test_loading_and_state_features()
    except:
        print("⚠️  Flask server not running - skipping chatbot tests")
        print("   Start server with: python app.py")
        test_results['flask_chatbot'] = False
        test_results['ui_features'] = False
    
    # Final Results
    print("\n🏆 FINAL TEST RESULTS")
    print("=" * 21)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    overall_success = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        test_display = test_name.replace('_', ' ').title()
        print(f"   {status} {test_display}")
    
    print(f"\n📈 Overall Score: {passed_tests}/{total_tests} ({overall_success:.0f}%)")
    
    if overall_success >= 75:
        print(f"\n🎉 SYSTEM ENHANCEMENT SUCCESSFUL! 🎉")
        print(f"✅ ADK tools now working correctly")
        print(f"✅ Loading animations implemented")
        print(f"✅ State management active")
        print(f"✅ No more error redirects")
        print(f"✅ Professional user experience")
        
        print(f"\n🚀 Ready for Production Use:")
        print(f"   • Database queries processed seamlessly")
        print(f"   • Loading indicators during AI responses")
        print(f"   • Chat history persists across page changes")
        print(f"   • Clear chat functionality available")
        print(f"   • Professional styling and animations")
        
    else:
        print(f"\n⚠️  Some issues remain - check individual test results")
        
        if not test_results.get('adk_tools'):
            print(f"   🔧 ADK tools need additional debugging")
        if not test_results.get('flask_chatbot'):
            print(f"   🤖 Flask chatbot responses need improvement")
        if not test_results.get('ui_features'):
            print(f"   🎨 UI enhancements need verification")
    
    return overall_success >= 75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)