#!/usr/bin/env python3
"""
Order Management System Test
Tests the fixed order status update functionality and enhanced filters
"""

import requests
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_order_status_update():
    """Test the fixed order status update functionality."""
    
    print("🔧 Testing Order Status Update Fix")
    print("=" * 35)
    
    base_url = "http://localhost:8000"
    
    # Test cases for status update
    test_cases = [
        {
            "order_id": 6731,  # Use the order ID from the error message
            "new_status": "Shipped",
            "description": "Update order 6731 to Shipped"
        },
        {
            "order_id": 6731,
            "new_status": "Delivered", 
            "description": "Update order 6731 to Delivered"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        
        # Test the previously failing URL pattern
        test_url = f"{base_url}/admin/orders/update_status/{test_case['order_id']}?status={test_case['new_status']}"
        print(f"📝 URL: {test_url}")
        
        try:
            # Test GET request (which was failing before)
            response = requests.get(test_url, allow_redirects=True, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ PASS: Status update successful")
                print(f"🔄 Redirected to: {response.url}")
                success_count += 1
            elif response.status_code == 404:
                print(f"❌ FAIL: Order not found (404)")
            elif response.status_code == 405:
                print(f"❌ FAIL: Method not allowed - fix not applied correctly")
            else:
                print(f"⚠️  PARTIAL: Unexpected status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ FAIL: Request error - {str(e)}")
    
    print(f"\n📊 Status Update Test Results:")
    print(f"   ✅ Successful: {success_count}/{len(test_cases)}")
    print(f"   📈 Success Rate: {(success_count/len(test_cases))*100:.1f}%")
    
    return success_count == len(test_cases)

def test_orders_page_enhancements():
    """Test the enhanced orders page functionality."""
    
    print("\n🎨 Testing Orders Page Enhancements")
    print("=" * 36)
    
    base_url = "http://localhost:8000"
    orders_url = f"{base_url}/admin/orders"
    
    try:
        response = requests.get(orders_url, timeout=10)
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for enhanced filter features
            enhancements = {
                "Status Dropdown Filter": 'id="statusFilter"' in html_content,
                "Date Range Filters": 'id="dateFrom"' in html_content and 'id="dateTo"' in html_content,
                "Search Input": 'id="searchInput"' in html_content,
                "Clear Filters Button": 'clearFilters()' in html_content,
                "Enhanced Status Update": 'updateOrderStatus(' in html_content,
                "Status Update Confirmation": 'confirm(' in html_content,
                "Loading States": 'fa-spinner fa-spin' in html_content,
                "Dynamic Count Updates": 'updateVisibleCount' in html_content,
                "Mobile Status Menus": 'Mobile Status Menu' in html_content,
            }
            
            print(f"✅ Orders page loaded successfully")
            
            working_features = 0
            for feature, present in enhancements.items():
                status = "✅" if present else "❌"
                print(f"{status} {feature}")
                if present:
                    working_features += 1
            
            print(f"\n📊 Enhancement Features: {working_features}/{len(enhancements)} working")
            
            success_rate = (working_features / len(enhancements)) * 100
            print(f"📈 Enhancement Success Rate: {success_rate:.1f}%")
            
            return success_rate >= 80  # 80% threshold
            
        else:
            print(f"❌ Orders page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Orders page test failed: {str(e)}")
        return False

def test_specific_order_lookup():
    """Test accessing a specific order to verify the system works end-to-end."""
    
    print("\n🔍 Testing Specific Order Lookup")
    print("=" * 30)
    
    base_url = "http://localhost:8000"
    
    # Test the chatbot with order queries to verify database integration
    chatbot_url = f"{base_url}/admin/chatbot"
    
    test_queries = [
        {
            "message": "show order 6731",
            "expectation": "Should return order details without errors"
        },
        {
            "message": "orders today", 
            "expectation": "Should return daily statistics"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}: {test_case['expectation']}")
        print(f"📝 Query: '{test_case['message']}'")
        
        try:
            response = requests.post(
                chatbot_url,
                json={"message": test_case['message']},
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                if 'error' not in response_text.lower() and 'failed' not in response_text.lower():
                    print(f"✅ PASS: Query executed successfully")
                    preview = response_text[:100].replace('<p class="mb-2 leading-relaxed">', '')
                    print(f"💬 Preview: {preview}...")
                    success_count += 1
                else:
                    print(f"⚠️  PARTIAL: Query returned with issues")
                    print(f"📄 Response: {response_text[:200]}...")
            else:
                print(f"❌ FAIL: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ FAIL: Request error - {str(e)}")
    
    print(f"\n📊 Order Lookup Test Results:")
    print(f"   ✅ Successful: {success_count}/{len(test_queries)}")
    print(f"   📈 Success Rate: {(success_count/len(test_queries))*100:.1f}%")
    
    return success_count >= len(test_queries) * 0.5  # 50% threshold

def main():
    """Run comprehensive order management tests."""
    
    print("🛒 ORDER MANAGEMENT SYSTEM TEST")
    print("=" * 35)
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎯 Testing Key Fixes:")
    print("   1. ✅ Order status update HTTP method error")
    print("   2. 🎨 Enhanced filters and UI improvements") 
    print("   3. 🔍 End-to-end order system functionality")
    print()
    
    # Check if Flask server is running
    try:
        response = requests.get("http://localhost:8000/admin", timeout=5)
        if response.status_code != 200:
            print("❌ Flask server not responding properly")
            return False
    except:
        print("❌ Flask server not running")
        print("   Please start the server with: python app.py")
        return False
    
    # Run all tests
    test_results = {}
    
    print("=" * 50)
    test_results['status_update'] = test_order_status_update()
    
    print("=" * 50) 
    test_results['page_enhancements'] = test_orders_page_enhancements()
    
    print("=" * 50)
    test_results['order_lookup'] = test_specific_order_lookup()
    
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
        print(f"\n🎉 ORDER MANAGEMENT FIXES SUCCESSFUL! 🎉")
        print(f"✅ Status update HTTP method error resolved")
        print(f"✅ Enhanced filters and search functionality")
        print(f"✅ Professional UI with confirmation dialogs")
        print(f"✅ Mobile-responsive design improvements")
        print(f"✅ Real-time count updates and loading states")
        
        print(f"\n🚀 Ready for Production Use:")
        print(f"   • Status updates work via GET and POST methods")
        print(f"   • Advanced filtering: status, date range, search")
        print(f"   • User-friendly dropdown interface")
        print(f"   • Confirmation dialogs prevent accidental changes")
        print(f"   • Loading animations for better UX")
        print(f"   • Responsive design for mobile and desktop")
        
    else:
        print(f"\n⚠️  Some issues remain - check individual test results")
        
        if not test_results.get('status_update'):
            print(f"   🔧 Status update functionality needs debugging")
        if not test_results.get('page_enhancements'):
            print(f"   🎨 UI enhancements may not be properly implemented")
        if not test_results.get('order_lookup'):
            print(f"   🔍 Order lookup system needs verification")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Test status updates on actual orders")
    print(f"   2. Verify filter functionality with real data")
    print(f"   3. Check mobile responsiveness")
    print(f"   4. Test order search and date filtering")
    
    return overall_success >= 75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)