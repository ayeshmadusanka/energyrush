#!/usr/bin/env python3
"""
MCP Database Server for EnergyRush
Provides database analysis capabilities through Model Context Protocol
"""

import asyncio
import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio
import mcp.types as types


class EnergyRushMCPServer:
    """MCP Server for EnergyRush database operations."""
    
    def __init__(self, db_path: str = "instance/energyrush.db"):
        self.db_path = db_path
        self.server = Server("energyrush-database")
        self.setup_tools()
    
    def get_db_connection(self):
        """Get SQLite database connection."""
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    
    def setup_tools(self):
        """Setup MCP tools for database operations."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available database tools."""
            return [
                Tool(
                    name="get_order_details",
                    description="Get detailed information about a specific order by ID or customer name",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "integer",
                                "description": "Order ID to search for"
                            },
                            "customer_name": {
                                "type": "string", 
                                "description": "Customer name to search for (partial match supported)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_order_summary",
                    description="Get summary statistics about orders (total, recent, by status)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of recent days to analyze (default: 30)",
                                "default": 30
                            }
                        }
                    }
                ),
                Tool(
                    name="search_orders_by_date",
                    description="Search orders within a specific date range",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD format)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD format)"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                ),
                Tool(
                    name="get_product_details",
                    description="Get detailed information about products and inventory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "integer",
                                "description": "Specific product ID to query"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_revenue_analysis",
                    description="Analyze revenue patterns and trends",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer", 
                                "description": "Number of days to analyze (default: 30)",
                                "default": 30
                            },
                            "group_by": {
                                "type": "string",
                                "enum": ["day", "week", "month"],
                                "description": "How to group the analysis (default: day)",
                                "default": "day"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_customer_analysis",
                    description="Analyze customer behavior and order patterns",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "customer_name": {
                                "type": "string",
                                "description": "Specific customer to analyze (optional)"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to analyze (default: 30)", 
                                "default": 30
                            }
                        }
                    }
                ),
                Tool(
                    name="get_daily_statistics",
                    description="Get total orders and revenue for a specific date",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format (e.g., '2025-08-06')"
                            }
                        },
                        "required": ["date"]
                    }
                ),
                Tool(
                    name="get_date_range_statistics",
                    description="Get orders and revenue statistics for a date range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                ),
                Tool(
                    name="execute_custom_query",
                    description="Execute a custom SQL query (SELECT only for safety)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL SELECT query to execute"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls."""
            
            try:
                if name == "get_order_details":
                    return [types.TextContent(type="text", text=await self.get_order_details(arguments))]
                elif name == "get_order_summary":
                    return [types.TextContent(type="text", text=await self.get_order_summary(arguments))]
                elif name == "search_orders_by_date":
                    return [types.TextContent(type="text", text=await self.search_orders_by_date(arguments))]
                elif name == "get_product_details":
                    return [types.TextContent(type="text", text=await self.get_product_details(arguments))]
                elif name == "get_revenue_analysis":
                    return [types.TextContent(type="text", text=await self.get_revenue_analysis(arguments))]
                elif name == "get_customer_analysis":
                    return [types.TextContent(type="text", text=await self.get_customer_analysis(arguments))]
                elif name == "get_daily_statistics":
                    return [types.TextContent(type="text", text=await self.get_daily_statistics(arguments))]
                elif name == "get_date_range_statistics":
                    return [types.TextContent(type="text", text=await self.get_date_range_statistics(arguments))]
                elif name == "execute_custom_query":
                    return [types.TextContent(type="text", text=await self.execute_custom_query(arguments))]
                else:
                    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
                    
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
    
    async def get_order_details(self, args: Dict[str, Any]) -> str:
        """Get detailed order information."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            if "order_id" in args and args["order_id"]:
                # Search by order ID
                cursor.execute("""
                    SELECT id, customer_name, customer_phone, customer_address, 
                           total_amount, status, created_at, items
                    FROM `order`
                    WHERE id = ?
                """, (args["order_id"],))
                
                order = cursor.fetchone()
                if not order:
                    return f"❌ Order with ID {args['order_id']} not found."
                
                # Handle date formatting properly
                order_date = 'N/A'
                if order[6]:
                    if hasattr(order[6], 'strftime'):
                        order_date = order[6].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        order_date = str(order[6])
                
                return f"""
📋 **Order Details - ID: {order[0]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **Customer Information:**
   • Name: {order[1]}
   • Phone: {order[2]}
   • Address: {order[3]}

💰 **Order Information:**
   • Total Amount: ${order[4]:.2f}
   • Status: {order[5]}
   • Order Date: {order_date}

📦 **Items:** {order[7]}
"""
            
            elif "customer_name" in args and args["customer_name"]:
                # Search by customer name (partial match)
                cursor.execute("""
                    SELECT id, customer_name, customer_phone, customer_address, 
                           total_amount, status, created_at, items
                    FROM `order`
                    WHERE customer_name LIKE ? 
                    ORDER BY created_at DESC
                    LIMIT 10
                """, (f"%{args['customer_name']}%",))
                
                orders = cursor.fetchall()
                if not orders:
                    return f"❌ No orders found for customer name containing '{args['customer_name']}'."
                
                result = f"🔍 **Orders for customers matching '{args['customer_name']}' (showing up to 10):**\n"
                result += "━" * 80 + "\n\n"
                
                for order in orders:
                    result += f"""📋 **Order ID: {order[0]}**
   👤 Customer: {order[1]} | 📞 {order[2]}
   💰 Amount: ${order[4]:.2f} | 📊 Status: {order[5]}
   📅 Date: {order[6].strftime('%Y-%m-%d %H:%M:%S') if order[6] else 'N/A'}
   🏠 Address: {order[3]}
   
"""
                return result
            else:
                return "❌ Please provide either order_id or customer_name parameter."
                
        finally:
            conn.close()
    
    async def get_order_summary(self, args: Dict[str, Any]) -> str:
        """Get order summary statistics."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        days = args.get("days", 30)
        
        try:
            # Total orders
            cursor.execute("SELECT COUNT(*) FROM `order`")
            total_orders = cursor.fetchone()[0]
            
            # Recent orders
            cursor.execute("""
                SELECT COUNT(*), AVG(total_amount), SUM(total_amount)
                FROM `order`
                WHERE created_at >= datetime('now', '-{} days')
            """.format(days))
            
            recent_stats = cursor.fetchone()
            recent_count = recent_stats[0] if recent_stats[0] else 0
            avg_amount = recent_stats[1] if recent_stats[1] else 0
            total_revenue = recent_stats[2] if recent_stats[2] else 0
            
            # Status breakdown
            cursor.execute("""
                SELECT status, COUNT(*), SUM(total_amount)
                FROM `order`
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY status
            """.format(days))
            
            status_breakdown = cursor.fetchall()
            
            # Daily average
            daily_avg = recent_count / days if days > 0 else 0
            
            result = f"""
📊 **Order Summary (Last {days} Days)**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 **Overall Statistics:**
   • Total Orders (All Time): {total_orders:,}
   • Recent Orders ({days} days): {recent_count:,}
   • Daily Average: {daily_avg:.1f} orders/day
   • Average Order Value: ${avg_amount:.2f}
   • Total Revenue ({days} days): ${total_revenue:.2f}

📋 **Status Breakdown:**"""
            
            for status, count, revenue in status_breakdown:
                result += f"\n   • {status}: {count:,} orders (${revenue:.2f})"
            
            return result
            
        finally:
            conn.close()
    
    async def search_orders_by_date(self, args: Dict[str, Any]) -> str:
        """Search orders within date range."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            start_date = args["start_date"]
            end_date = args["end_date"]
            
            cursor.execute("""
                SELECT id, customer_name, total_amount, status, created_at
                FROM `order`
                WHERE DATE(created_at) BETWEEN ? AND ?
                ORDER BY created_at DESC
                LIMIT 50
            """, (start_date, end_date))
            
            orders = cursor.fetchall()
            
            if not orders:
                return f"❌ No orders found between {start_date} and {end_date}."
            
            # Calculate summary stats
            total_orders = len(orders)
            total_revenue = sum(order[2] for order in orders)
            avg_order = total_revenue / total_orders if total_orders > 0 else 0
            
            result = f"""
📅 **Orders from {start_date} to {end_date}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Summary:**
   • Total Orders: {total_orders:,}
   • Total Revenue: ${total_revenue:.2f}
   • Average Order: ${avg_order:.2f}

📋 **Order List (showing up to 50):**
"""
            
            for order in orders:
                order_date = order[4].strftime('%Y-%m-%d %H:%M') if order[4] else 'N/A'
                result += f"\n🔸 ID: {order[0]} | {order[1]} | ${order[2]:.2f} | {order[3]} | {order_date}"
            
            return result
            
        finally:
            conn.close()
    
    async def get_product_details(self, args: Dict[str, Any]) -> str:
        """Get product and inventory information."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            if "product_id" in args and args["product_id"]:
                cursor.execute("""
                    SELECT id, name, description, price, stock, image_url
                    FROM product
                    WHERE id = ?
                """, (args["product_id"],))
                
                product = cursor.fetchone()
                if not product:
                    return f"❌ Product with ID {args['product_id']} not found."
                
                # Get order count for this product
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM `order`
                    WHERE items LIKE ?
                """, (f'%"product_id": {product[0]}%',))
                
                order_count = cursor.fetchone()[0]
                
                return f"""
📦 **Product Details - ID: {product[0]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️  **Product Information:**
   • Name: {product[1]}
   • Description: {product[2]}
   • Price: ${product[3]:.2f}
   • Stock Level: {product[4]:,} units
   • Image URL: {product[5]}

📈 **Sales Information:**
   • Total Orders: {order_count:,}
   • Stock Status: {'✅ In Stock' if product[4] > 0 else '⚠️ Out of Stock'}
"""
            else:
                # Get all products
                cursor.execute("""
                    SELECT id, name, description, price, stock, image_url
                    FROM product
                    ORDER BY id
                """)
                
                products = cursor.fetchall()
                
                if not products:
                    return "❌ No products found in the database."
                
                result = "📦 **All Products Inventory**\n"
                result += "━" * 50 + "\n\n"
                
                for product in products:
                    stock_status = "✅ In Stock" if product[4] > 0 else "⚠️ Out of Stock"
                    result += f"""🏷️  **{product[1]}** (ID: {product[0]})
   • Price: ${product[3]:.2f}
   • Stock: {product[4]:,} units
   • Status: {stock_status}
   • Description: {product[2]}

"""
                
                return result
                
        finally:
            conn.close()
    
    async def get_revenue_analysis(self, args: Dict[str, Any]) -> str:
        """Analyze revenue patterns and trends."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        days = args.get("days", 30)
        group_by = args.get("group_by", "day")
        
        try:
            if group_by == "day":
                cursor.execute("""
                    SELECT DATE(created_at) as period,
                           COUNT(*) as orders,
                           SUM(total_amount) as revenue,
                           AVG(total_amount) as avg_order
                    FROM `order`
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY DATE(created_at)
                    ORDER BY period DESC
                    LIMIT 30
                """.format(days))
            elif group_by == "week":
                cursor.execute("""
                    SELECT strftime('%Y-W%W', created_at) as period,
                           COUNT(*) as orders,
                           SUM(total_amount) as revenue,
                           AVG(total_amount) as avg_order
                    FROM `order`
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY strftime('%Y-W%W', created_at)
                    ORDER BY period DESC
                """.format(days))
            else:  # month
                cursor.execute("""
                    SELECT strftime('%Y-%m', created_at) as period,
                           COUNT(*) as orders,
                           SUM(total_amount) as revenue,
                           AVG(total_amount) as avg_order
                    FROM `order`
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY strftime('%Y-%m', created_at)
                    ORDER BY period DESC
                """.format(days))
            
            revenue_data = cursor.fetchall()
            
            if not revenue_data:
                return f"❌ No revenue data found for the last {days} days."
            
            total_revenue = sum(row[2] for row in revenue_data)
            total_orders = sum(row[1] for row in revenue_data)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            result = f"""
💰 **Revenue Analysis (Last {days} Days - Grouped by {group_by})**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Summary:**
   • Total Revenue: ${total_revenue:.2f}
   • Total Orders: {total_orders:,}
   • Average Order Value: ${avg_order_value:.2f}
   • Periods Analyzed: {len(revenue_data)}

📈 **Period Breakdown:**
"""
            
            for period, orders, revenue, avg_order in revenue_data:
                result += f"\n📅 {period}: {orders:,} orders | ${revenue:.2f} revenue | ${avg_order:.2f} avg"
            
            return result
            
        finally:
            conn.close()
    
    async def get_customer_analysis(self, args: Dict[str, Any]) -> str:
        """Analyze customer behavior and patterns."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        days = args.get("days", 30)
        customer_name = args.get("customer_name")
        
        try:
            if customer_name:
                # Specific customer analysis
                cursor.execute("""
                    SELECT id, customer_phone, customer_address, total_amount, 
                           status, created_at
                    FROM `order`
                    WHERE customer_name LIKE ?
                    AND created_at >= datetime('now', '-{} days')
                    ORDER BY created_at DESC
                """.format(days), (f"%{customer_name}%",))
                
                orders = cursor.fetchall()
                
                if not orders:
                    return f"❌ No orders found for customer '{customer_name}' in the last {days} days."
                
                total_spent = sum(order[3] for order in orders)
                avg_order = total_spent / len(orders)
                
                result = f"""
👤 **Customer Analysis: {customer_name}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Summary ({days} days):**
   • Total Orders: {len(orders):,}
   • Total Spent: ${total_spent:.2f}
   • Average Order: ${avg_order:.2f}
   • Phone: {orders[0][1] if orders else 'N/A'}
   • Address: {orders[0][2] if orders else 'N/A'}

📋 **Recent Orders:**
"""
                
                for order in orders[:10]:  # Show last 10 orders
                    order_date = order[5].strftime('%Y-%m-%d %H:%M') if order[5] else 'N/A'
                    result += f"\n🔸 Order {order[0]}: ${order[3]:.2f} | {order[4]} | {order_date}"
                
                return result
                
            else:
                # General customer analysis
                cursor.execute("""
                    SELECT customer_name, COUNT(*) as order_count, 
                           SUM(total_amount) as total_spent,
                           AVG(total_amount) as avg_order,
                           MAX(created_at) as last_order
                    FROM `order`
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY customer_name
                    ORDER BY total_spent DESC
                    LIMIT 20
                """.format(days))
                
                customers = cursor.fetchall()
                
                if not customers:
                    return f"❌ No customer data found for the last {days} days."
                
                # Overall stats
                cursor.execute("""
                    SELECT COUNT(DISTINCT customer_name), 
                           COUNT(*) as total_orders,
                           SUM(total_amount) as total_revenue
                    FROM `order`
                    WHERE created_at >= datetime('now', '-{} days')
                """.format(days))
                
                overall_stats = cursor.fetchone()
                unique_customers = overall_stats[0]
                total_orders = overall_stats[1]
                total_revenue = overall_stats[2]
                
                result = f"""
👥 **Customer Analysis (Last {days} Days)**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Overview:**
   • Unique Customers: {unique_customers:,}
   • Total Orders: {total_orders:,}
   • Total Revenue: ${total_revenue:.2f}
   • Orders per Customer: {total_orders/unique_customers:.1f}

🏆 **Top Customers (by spending):**
"""
                
                for customer, order_count, total_spent, avg_order, last_order in customers:
                    last_order_str = last_order.strftime('%Y-%m-%d') if last_order else 'N/A'
                    result += f"\n👤 {customer}: {order_count} orders | ${total_spent:.2f} | avg ${avg_order:.2f} | last: {last_order_str}"
                
                return result
                
        finally:
            conn.close()
    
    async def execute_custom_query(self, args: Dict[str, Any]) -> str:
        """Execute custom SQL query (SELECT only for safety)."""
        query = args["query"].strip()
        
        # Safety check - only allow SELECT queries
        if not query.upper().startswith("SELECT"):
            return "❌ Only SELECT queries are allowed for security reasons."
        
        # Additional safety checks
        dangerous_keywords = ["DELETE", "DROP", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return f"❌ Query contains dangerous keyword '{keyword}'. Only SELECT queries are allowed."
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            
            if not results:
                return "❌ Query returned no results."
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            result = f"""
🔍 **Custom Query Results**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 **Query:** {query}

📊 **Results:** ({len(results)} rows)
"""
            
            # Format results as table
            for i, row in enumerate(results[:100]):  # Limit to 100 rows
                result += f"\n**Row {i+1}:**"
                for col_name, value in zip(column_names, row):
                    result += f"\n   • {col_name}: {value}"
                result += "\n"
            
            if len(results) > 100:
                result += f"\n⚠️ Showing first 100 rows out of {len(results)} total results."
            
            return result
            
        except Exception as e:
            return f"❌ Query error: {str(e)}"
            
        finally:
            conn.close()
    
    async def get_daily_statistics(self, args: Dict[str, Any]) -> str:
        """Get total orders and revenue for a specific date."""
        date_str = args["date"]
        
        # Validate date format
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return "❌ Invalid date format. Please use YYYY-MM-DD format (e.g., '2025-08-06')."
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get daily statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_order_value,
                    MIN(total_amount) as min_order,
                    MAX(total_amount) as max_order,
                    MIN(created_at) as first_order_time,
                    MAX(created_at) as last_order_time
                FROM `order`
                WHERE DATE(created_at) = ?
            """, (date_str,))
            
            stats = cursor.fetchone()
            
            if not stats or stats[0] == 0:
                return f"📅 No orders found for {date_str}."
            
            total_orders = stats[0]
            total_revenue = stats[1] or 0
            avg_order_value = stats[2] or 0
            min_order = stats[3] or 0
            max_order = stats[4] or 0
            first_order = stats[5] or ''
            last_order = stats[6] or ''
            
            # Format times
            if first_order:
                first_time = datetime.fromisoformat(first_order.replace('Z', '+00:00')) if isinstance(first_order, str) else first_order
                first_order_formatted = first_time.strftime('%H:%M:%S') if hasattr(first_time, 'strftime') else str(first_order)
            else:
                first_order_formatted = 'N/A'
                
            if last_order:
                last_time = datetime.fromisoformat(last_order.replace('Z', '+00:00')) if isinstance(last_order, str) else last_order
                last_order_formatted = last_time.strftime('%H:%M:%S') if hasattr(last_time, 'strftime') else str(last_order)
            else:
                last_order_formatted = 'N/A'
            
            # Get hourly distribution
            cursor.execute("""
                SELECT 
                    strftime('%H', created_at) as hour,
                    COUNT(*) as orders,
                    SUM(total_amount) as revenue
                FROM `order`
                WHERE DATE(created_at) = ?
                GROUP BY strftime('%H', created_at)
                ORDER BY hour
            """, (date_str,))
            
            hourly_data = cursor.fetchall()
            
            result = f"""
📅 **Daily Statistics for {date_str}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Summary:**
   • Total Orders: {total_orders:,}
   • Total Revenue: ${total_revenue:.2f}
   • Average Order Value: ${avg_order_value:.2f}
   • Min Order: ${min_order:.2f}
   • Max Order: ${max_order:.2f}
   • First Order: {first_order_formatted}
   • Last Order: {last_order_formatted}

⏰ **Hourly Breakdown:**
"""
            
            if hourly_data:
                for hour, orders, revenue in hourly_data:
                    result += f"\n🕐 {hour}:00-{hour}:59: {orders} orders | ${revenue:.2f} revenue"
            else:
                result += "\n   No hourly data available."
            
            return result
            
        finally:
            conn.close()
    
    async def get_date_range_statistics(self, args: Dict[str, Any]) -> str:
        """Get orders and revenue statistics for a date range."""
        start_date = args["start_date"]
        end_date = args["end_date"]
        
        # Validate date formats
        try:
            from datetime import datetime
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return "❌ Invalid date format. Please use YYYY-MM-DD format for both dates."
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get overall statistics for the date range
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_order_value,
                    MIN(total_amount) as min_order,
                    MAX(total_amount) as max_order,
                    COUNT(DISTINCT DATE(created_at)) as unique_days,
                    COUNT(DISTINCT customer_name) as unique_customers
                FROM `order`
                WHERE DATE(created_at) BETWEEN ? AND ?
            """, (start_date, end_date))
            
            overall_stats = cursor.fetchone()
            
            if not overall_stats or overall_stats[0] == 0:
                return f"📅 No orders found between {start_date} and {end_date}."
            
            total_orders = overall_stats[0]
            total_revenue = overall_stats[1] or 0
            avg_order_value = overall_stats[2] or 0
            min_order = overall_stats[3] or 0
            max_order = overall_stats[4] or 0
            unique_days = overall_stats[5] or 0
            unique_customers = overall_stats[6] or 0
            
            # Get daily breakdown
            cursor.execute("""
                SELECT 
                    DATE(created_at) as order_date,
                    COUNT(*) as orders,
                    SUM(total_amount) as revenue,
                    AVG(total_amount) as avg_order
                FROM `order`
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY DATE(created_at)
                ORDER BY order_date DESC
                LIMIT 30
            """, (start_date, end_date))
            
            daily_breakdown = cursor.fetchall()
            
            result = f"""
📅 **Date Range Statistics: {start_date} to {end_date}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Overall Summary:**
   • Total Orders: {total_orders:,}
   • Total Revenue: ${total_revenue:.2f}
   • Average Order Value: ${avg_order_value:.2f}
   • Min Order: ${min_order:.2f}
   • Max Order: ${max_order:.2f}
   • Active Days: {unique_days}
   • Unique Customers: {unique_customers:,}
   • Average Orders per Day: {total_orders/unique_days:.1f}
   • Average Revenue per Day: ${total_revenue/unique_days:.2f}

📈 **Daily Breakdown (Last 30 days):**
"""
            
            if daily_breakdown:
                for order_date, orders, revenue, avg_order in daily_breakdown:
                    # Parse date to get day of week
                    try:
                        date_obj = datetime.strptime(str(order_date), '%Y-%m-%d')
                        day_name = date_obj.strftime('%A')[:3]  # Mon, Tue, etc.
                        result += f"\n📅 {order_date} ({day_name}): {orders} orders | ${revenue:.2f} revenue | ${avg_order:.2f} avg"
                    except:
                        result += f"\n📅 {order_date}: {orders} orders | ${revenue:.2f} revenue | ${avg_order:.2f} avg"
            else:
                result += "\n   No daily data available."
            
            return result
            
        finally:
            conn.close()


async def main():
    """Main server function."""
    
    # Check if database exists
    db_path = Path("instance/energyrush.db")
    if not db_path.exists():
        print("❌ Database file not found. Please make sure the Flask app has been run at least once.")
        return
    
    # Create and run MCP server
    mcp_server = EnergyRushMCPServer(str(db_path))
    
    print("🚀 Starting EnergyRush MCP Database Server...")
    print("📊 Available tools: order details, summaries, date search, products, revenue analysis, customer analysis")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await mcp_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="energyrush-database",
                server_version="1.0.0",
                capabilities=mcp_server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())