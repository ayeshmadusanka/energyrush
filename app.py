from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pytz
from pytz import timezone
import sqlite3
import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import statsmodels.api as sm
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Import enhanced chatbot with MCP integration
try:
    from enhanced_chatbot import create_enhanced_chatbot_handler
    enhanced_chatbot_available = True
    print("✅ Enhanced chatbot with MCP integration loaded")
except ImportError as e:
    print(f"⚠️ Enhanced chatbot not available: {e}")
    enhanced_chatbot_available = False

# Import Gemini chatbot for general conversation
try:
    from gemini_integration import create_gemini_chatbot
    gemini_chatbot_instance = create_gemini_chatbot()
    gemini_available = gemini_chatbot_instance is not None
    print("✅ Gemini chatbot loaded" if gemini_available else "⚠️ Gemini chatbot failed to load")
except ImportError as e:
    print(f"⚠️ Gemini chatbot not available: {e}")
    gemini_available = False
    gemini_chatbot_instance = None

# Import Gemini-ADK Bridge for intelligent query processing
try:
    from gemini_adk_bridge import create_gemini_adk_bridge
    bridge_instance = create_gemini_adk_bridge()
    bridge_available = bridge_instance is not None
    print("✅ Gemini-ADK Bridge loaded" if bridge_available else "⚠️ Gemini-ADK Bridge failed to load")
except ImportError as e:
    print(f"⚠️ Gemini-ADK Bridge not available: {e}")
    bridge_available = False
    bridge_instance = None

# Import markdown parser
try:
    import markdown
    markdown_available = True
    print("✅ Markdown parser loaded")
except ImportError:
    markdown_available = False
    print("⚠️ Markdown parser not available")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️ python-dotenv not available")
import os
from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering

app = Flask(__name__)
app.config['SECRET_KEY'] = 'energyrush-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///energyrush.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure timezone
COLOMBO_TZ = timezone('Asia/Colombo')
UTC_TZ = pytz.UTC

db = SQLAlchemy(app)

# Timezone utility functions
def get_colombo_time():
    """Get current time in Asia/Colombo timezone"""
    utc_now = datetime.utcnow().replace(tzinfo=UTC_TZ)
    return utc_now.astimezone(COLOMBO_TZ)

def utc_to_colombo(utc_dt):
    """Convert UTC datetime to Asia/Colombo timezone"""
    if utc_dt.tzinfo is None:
        utc_dt = UTC_TZ.localize(utc_dt)
    return utc_dt.astimezone(COLOMBO_TZ)

def colombo_to_utc(colombo_dt):
    """Convert Asia/Colombo datetime to UTC"""
    if colombo_dt.tzinfo is None:
        colombo_dt = COLOMBO_TZ.localize(colombo_dt)
    return colombo_dt.astimezone(UTC_TZ)

# Custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

@app.template_filter('colombo_datetime')
def colombo_datetime_filter(value, format='%Y-%m-%d %H:%M:%S'):
    """Format datetime in Asia/Colombo timezone"""
    if value is None:
        return ''
    
    # If datetime is naive (no timezone), assume it's already in Colombo time
    if value.tzinfo is None:
        colombo_dt = COLOMBO_TZ.localize(value)
    else:
        colombo_dt = value.astimezone(COLOMBO_TZ)
    
    return colombo_dt.strftime(format)

@app.template_filter('colombo_date')
def colombo_date_filter(value):
    """Format date in Asia/Colombo timezone"""
    return colombo_datetime_filter(value, '%Y-%m-%d')

@app.template_filter('colombo_time')
def colombo_time_filter(value):
    """Format time in Asia/Colombo timezone"""
    return colombo_datetime_filter(value, '%H:%M:%S')

# Add context processor for timezone info
@app.context_processor
def inject_timezone_context():
    return {
        'current_colombo_time': get_colombo_time(),
        'timezone_name': 'Asia/Colombo',
        'timezone_offset': '+05:30'
    }

# Database Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: get_colombo_time().replace(tzinfo=None))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=lambda: get_colombo_time().replace(tzinfo=None))
    items = db.Column(db.Text)  # JSON string of cart items

# Initialize NLP model (lazy loading)
nlp_pipeline = None

def get_nlp_pipeline():
    global nlp_pipeline
    if nlp_pipeline is None:
        try:
            nlp_pipeline = pipeline("question-answering", 
                                  model="distilbert-base-cased-distilled-squad",
                                  tokenizer="distilbert-base-cased-distilled-squad")
        except:
            nlp_pipeline = "error"
    return nlp_pipeline

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])
    
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if product already in cart
    for item in session['cart']:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            break
    else:
        session['cart'].append({
            'product_id': product_id,
            'quantity': quantity
        })
    
    session.modified = True
    flash('Product added to cart!', 'success')
    return redirect(url_for('products'))

@app.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = []
    
    cart_items = []
    total = 0
    
    for item in session['cart']:
        product = Product.query.get(item['product_id'])
        if product:
            item_total = product.price * item['quantity']
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'total': item_total
            })
            total += item_total
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])
    
    if 'cart' not in session:
        session['cart'] = []
    
    if quantity <= 0:
        # Remove item if quantity is 0 or less
        session['cart'] = [item for item in session['cart'] if item['product_id'] != product_id]
        flash('Item removed from cart', 'info')
    else:
        # Update quantity
        for item in session['cart']:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                break
        flash('Cart updated successfully', 'success')
    
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = int(request.form['product_id'])
    
    if 'cart' not in session:
        session['cart'] = []
    
    # Remove item from cart
    session['cart'] = [item for item in session['cart'] if item['product_id'] != product_id]
    session.modified = True
    flash('Item removed from cart', 'success')
    return redirect(url_for('cart'))

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    session['cart'] = []
    session.modified = True
    flash('Cart cleared', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        # Process order
        customer_name = request.form['name']
        customer_phone = request.form['phone']
        customer_address = request.form['address']
        
        if 'cart' not in session or not session['cart']:
            flash('Your cart is empty!', 'error')
            return redirect(url_for('products'))
        
        # Calculate total and prepare items
        total = 0
        cart_items = []
        
        for item in session['cart']:
            product = Product.query.get(item['product_id'])
            if product and product.stock >= item['quantity']:
                item_total = product.price * item['quantity']
                cart_items.append({
                    'product_id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'quantity': item['quantity'],
                    'total': item_total
                })
                total += item_total
                
                # Update stock
                product.stock -= item['quantity']
            else:
                flash(f'Insufficient stock for {product.name if product else "unknown product"}', 'error')
                return redirect(url_for('cart'))
        
        # Create order
        order = Order(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            total_amount=total,
            items=json.dumps(cart_items)
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Clear cart
        session['cart'] = []
        session.modified = True
        
        return render_template('order_confirmation.html', order=order)
    
    return render_template('checkout.html')

# Admin Routes
@app.route('/admin')
def admin_dashboard():
    # Get statistics
    total_orders = Order.query.count()
    total_products = Product.query.count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Low stock products
    low_stock_products = Product.query.filter(Product.stock < 10).all()
    
    return render_template('admin/dashboard.html', 
                         total_orders=total_orders,
                         total_products=total_products,
                         pending_orders=pending_orders,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products)

@app.route('/admin/products')
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            stock=int(request.form['stock']),
            image_url=request.form.get('image_url', '')
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/add_product.html')

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
def admin_edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.image_url = request.form.get('image_url', '')
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/products/delete/<int:id>')
def admin_delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/filter', methods=['POST'])
def admin_orders_filter():
    """AJAX endpoint for filtering orders without page reload."""
    try:
        data = request.get_json()
        
        # Start with base query
        query = Order.query
        
        # Apply status filter
        status = data.get('status')
        if status and status != 'all':
            query = query.filter(Order.status == status)
        
        # Apply date range filter
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from:
            from datetime import datetime
            try:
                start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(db.func.date(Order.created_at) >= start_date)
            except ValueError:
                pass
        
        if date_to:
            from datetime import datetime
            try:
                end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(db.func.date(Order.created_at) <= end_date)
            except ValueError:
                pass
        
        # Apply search filter
        search = data.get('search', '').strip()
        if search:
            query = query.filter(
                db.or_(
                    Order.customer_name.contains(search),
                    Order.customer_phone.contains(search),
                    Order.customer_address.contains(search),
                    db.cast(Order.id, db.String).contains(search)
                )
            )
        
        # Get filtered orders
        filtered_orders = query.order_by(Order.created_at.desc()).all()
        
        # Calculate statistics
        stats = {
            'total': len(filtered_orders),
            'pending': len([o for o in filtered_orders if o.status == 'Pending']),
            'shipped': len([o for o in filtered_orders if o.status == 'Shipped']),
            'delivered': len([o for o in filtered_orders if o.status == 'Delivered']),
            'completed': len([o for o in filtered_orders if o.status == 'Completed']),
            'cancelled': len([o for o in filtered_orders if o.status == 'Cancelled']),
            'total_revenue': sum(o.total_amount for o in filtered_orders)
        }
        
        # Convert orders to JSON-serializable format
        orders_data = []
        for order in filtered_orders:
            # Parse items safely
            items_data = []
            if order.items:
                try:
                    import json
                    items_list = json.loads(order.items)
                    items_data = items_list[:2]  # Show first 2 items
                    if len(items_list) > 2:
                        items_data.append({'more_count': len(items_list) - 2})
                except:
                    items_data = [{'name': 'Invalid items data', 'quantity': 0}]
            
            orders_data.append({
                'id': order.id,
                'customer_name': order.customer_name,
                'customer_phone': order.customer_phone,
                'customer_address': order.customer_address,
                'total_amount': float(order.total_amount),
                'status': order.status,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'created_date': order.created_at.strftime('%Y-%m-%d'),
                'created_time': order.created_at.strftime('%H:%M'),
                'items': items_data,
                'customer_initial': order.customer_name[0].upper() if order.customer_name else 'U'
            })
        
        return jsonify({
            'success': True,
            'orders': orders_data,
            'stats': stats,
            'message': f'Found {stats["total"]} orders'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error filtering orders'
        }), 500

@app.route('/admin/orders/update_status/<int:id>', methods=['GET', 'POST'])
def admin_update_order_status(id):
    order = Order.query.get_or_404(id)
    
    # Handle both GET and POST requests
    if request.method == 'GET':
        new_status = request.args.get('status')
    else:
        new_status = request.form.get('status')
    
    if new_status and new_status in ['Pending', 'Shipped', 'Delivered', 'Cancelled']:
        old_status = order.status
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status updated from {old_status} to {new_status}!', 'success')
    else:
        flash('Invalid status provided!', 'error')
    
    return redirect(url_for('admin_orders'))

@app.route('/admin/forecasting')
def admin_forecasting():
    try:
        # Generate forecasting data
        forecast_data = generate_forecast()
        return render_template('admin/forecasting.html', forecast_data=forecast_data)
    except Exception as e:
        flash(f'Error generating forecast: {str(e)}', 'error')
        return render_template('admin/forecasting.html', forecast_data=None)

@app.route('/admin/chatbot', methods=['POST'])
def admin_chatbot():
    try:
        message = request.json.get('message', '')
        
        # Use Gemini-ADK Bridge as primary handler
        if bridge_available and bridge_instance:
            try:
                import asyncio
                
                # Run bridge processing in async context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    bridge_result = loop.run_until_complete(
                        bridge_instance.process_user_query(message)
                    )
                finally:
                    loop.close()
                
                if bridge_result['success']:
                    formatted_response = parse_markdown_response(bridge_result['response'])
                    
                    return jsonify({
                        'response': formatted_response,
                        'raw_response': bridge_result['response'],
                        'type': 'gemini_adk_bridge',
                        'handler': 'Gemini-ADK Bridge',
                        'success': True,
                        'bridge_info': bridge_result.get('bridge_info', {}),
                        'adk_tool_used': bridge_result.get('bridge_info', {}).get('adk_tool_used'),
                        'gemini_translation': True
                    })
                else:
                    print(f"Bridge error: {bridge_result['response']}")
                    # Fall through to fallback handlers
                    
            except Exception as e:
                print(f"Bridge system error: {e}")
                # Fall through to fallback handlers
        
        # Fallback 1: Direct database query using ADK
        is_database_query = is_database_related_query(message)
        
        if is_database_query and enhanced_chatbot_available:
            try:
                enhanced_chatbot_handler = create_enhanced_chatbot_handler()
                raw_response = enhanced_chatbot_handler(message)
                formatted_response = parse_markdown_response(raw_response)
                
                return jsonify({
                    'response': formatted_response,
                    'raw_response': raw_response,
                    'type': 'adk_database',
                    'handler': 'ADK MCP (Direct)',
                    'success': True,
                    'fallback_used': 'bridge_failed'
                })
            except Exception as e:
                print(f"ADK MCP error: {e}")
                # Fall through to other handlers
        
        # Fallback 2: Gemini for general conversation
        elif gemini_available and gemini_chatbot_instance:
            try:
                gemini_result = gemini_chatbot_instance.generate_response(message)
                
                if gemini_result['success']:
                    formatted_response = parse_markdown_response(gemini_result['response'])
                    
                    return jsonify({
                        'response': formatted_response,
                        'raw_response': gemini_result['response'],
                        'type': 'gemini_chat',
                        'handler': 'Gemini AI (Direct)',
                        'success': True,
                        'usage': gemini_result.get('usage', {}),
                        'fallback_used': 'bridge_failed'
                    })
                else:
                    print(f"Gemini error: {gemini_result.get('error', 'Unknown error')}")
                    # Fall through to basic handler
                    
            except Exception as e:
                print(f"Gemini integration error: {e}")
                # Fall through to basic handler
        
        # Fallback to basic responses
        raw_response = handle_basic_chatbot_queries(message)
        formatted_response = parse_markdown_response(raw_response)
        
        return jsonify({
            'response': formatted_response,
            'raw_response': raw_response,
            'type': 'basic_fallback',
            'handler': 'Basic Handler',
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'response': f'❌ Sorry, I encountered an error: {str(e)}',
            'type': 'error',
            'success': False
        })

def is_database_related_query(message: str) -> bool:
    """Determine if the message requires database access (should use ADK MCP)."""
    
    # Use the same logic as Gemini integration for consistency
    if gemini_available and gemini_chatbot_instance:
        return gemini_chatbot_instance.is_database_query(message)
    
    # Fallback logic if Gemini is not available
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
    
    # Order ID patterns
    if re.search(r'show.*\d+|order.*\d+|find.*\d+', message_lower):
        return True
    
    # Customer name patterns
    if re.search(r'customer[_\s]+\w+', message_lower):
        return True
    
    return False

def parse_markdown_response(text: str) -> str:
    """Convert markdown text to HTML for better display."""
    if not markdown_available:
        return format_chatbot_response_fallback(text)
    
    try:
        # Pre-process the text to handle special cases
        processed_text = preprocess_chatbot_text(text)
        
        # Configure markdown with extensions for better formatting
        md = markdown.Markdown(extensions=[
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists'
        ])
        
        # Convert markdown to HTML
        html = md.convert(processed_text)
        
        # Post-process the HTML for better styling
        html = post_process_chatbot_html(html)
        
        return html
        
    except Exception as e:
        print(f"Markdown parsing error: {e}")
        return format_chatbot_response_fallback(text)

def preprocess_chatbot_text(text: str) -> str:
    """Pre-process text before markdown conversion."""
    
    # Convert bullet points to proper markdown lists
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        stripped = line.strip()
        original_line = line
        
        # Handle bullet points (•) - convert to markdown list
        if stripped.startswith('• '):
            # Ensure proper list formatting by adding empty line before if needed
            if processed_lines and processed_lines[-1].strip() != "" and not processed_lines[-1].strip().startswith(('- ', '* ')):
                processed_lines.append("")
            processed_lines.append(f"- {stripped[2:]}")  # Convert • to -
        # Handle other bullet formats
        elif stripped.startswith('- ') or stripped.startswith('* '):
            # Ensure proper list formatting
            if processed_lines and processed_lines[-1].strip() != "" and not processed_lines[-1].strip().startswith(('- ', '* ')):
                processed_lines.append("")
            processed_lines.append(stripped)
        else:
            processed_lines.append(original_line)
    
    processed_text = '\n'.join(processed_lines)
    
    # Handle Unicode line separators (━━━━━━━━)
    processed_text = processed_text.replace('━', '─')  # Convert to simpler dash
    
    return processed_text

def post_process_chatbot_html(html: str) -> str:
    """Post-process HTML after markdown conversion."""
    
    # Add styling classes for better presentation
    html = html.replace('<h1>', '<h1 class="text-xl font-bold mb-3 pb-2 border-b-2 border-gray-200">')
    html = html.replace('<h2>', '<h2 class="text-lg font-semibold mb-2">')
    html = html.replace('<h3>', '<h3 class="text-md font-semibold mb-2">')
    html = html.replace('<p>', '<p class="mb-2 leading-relaxed">')
    html = html.replace('<ul>', '<ul class="list-none pl-0 mb-3 space-y-1">')
    html = html.replace('<ol>', '<ol class="list-decimal pl-4 mb-3 space-y-1">')
    html = html.replace('<li>', '<li class="flex items-start mb-1"><span class="text-blue-500 mr-2 mt-0.5">•</span><span class="flex-1">')
    html = html.replace('</li>', '</span></li>')
    html = html.replace('<strong>', '<strong class="font-semibold text-gray-800">')
    html = html.replace('<em>', '<em class="italic text-gray-600">')
    html = html.replace('<code>', '<code class="bg-gray-100 px-2 py-1 rounded font-mono text-sm text-red-600">')
    html = html.replace('<pre>', '<pre class="bg-gray-50 border border-gray-200 p-3 rounded-md font-mono text-sm overflow-auto mb-3">')
    
    # Handle horizontal lines (converted from ━━━━━━━━)
    import re
    
    # First, handle lines inside paragraphs
    html = re.sub(r'<p class="mb-2 leading-relaxed">\s*─{20,}\s*</p>', 
                  '<div class="border-t-2 border-gray-300 my-3"></div>', html)
    
    # Handle lines with other content (remove the line part)
    html = re.sub(r'─{20,}<br />', '<div class="border-t-2 border-gray-300 my-2"></div>', html)
    html = re.sub(r'<br />\s*─{20,}', '<div class="border-t-2 border-gray-300 my-2"></div>', html)
    
    # Clean up any remaining long dash sequences
    html = re.sub(r'─{20,}', '<div class="border-t-2 border-gray-300 my-2"></div>', html)
    
    return html

def format_chatbot_response_fallback(text: str) -> str:
    """Fallback formatting when markdown is not available."""
    
    # Basic HTML escaping
    import html as html_module
    escaped_text = html_module.escape(text)
    
    # Convert line breaks to <br>
    formatted = escaped_text.replace('\n', '<br>')
    
    # Basic formatting for common patterns
    # Bold text (**text**)
    import re
    formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong class="font-semibold">\1</strong>', formatted)
    
    # Bullet points
    formatted = re.sub(r'<br>• (.*?)<br>', r'<br><div class="flex items-start mb-1"><span class="text-blue-500 mr-2">•</span><span>\1</span></div><br>', formatted)
    
    # Line separators
    formatted = re.sub(r'━{20,}', '<div class="border-t-2 border-gray-300 my-3"></div>', formatted)
    
    # Wrap in a container
    return f'<div class="leading-relaxed">{formatted}</div>'

def handle_basic_chatbot_queries(message: str) -> str:
    """Handle basic chatbot queries when enhanced chatbot is not available."""
    message_lower = message.lower()
    
    try:
        # Database connection
        conn = sqlite3.connect('instance/energyrush.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        # Basic order queries
        if 'order' in message_lower and any(char.isdigit() for char in message):
            # Extract number from message
            import re
            numbers = re.findall(r'\d+', message)
            if numbers:
                order_id = int(numbers[0])
                cursor.execute("""
                    SELECT id, customer_name, total_amount, status, created_at
                    FROM `order` WHERE id = ?
                """, (order_id,))
                order = cursor.fetchone()
                
                if order:
                    date_str = order[4].strftime('%Y-%m-%d %H:%M') if order[4] else 'N/A'
                    return f"📋 **Order {order[0]}**\n👤 Customer: {order[1]}\n💰 Amount: ${order[2]:.2f}\n📊 Status: {order[3]}\n📅 Date: {date_str}"
                else:
                    return f"❌ Order {order_id} not found."
        
        # Basic summary queries  
        elif any(word in message_lower for word in ['summary', 'total', 'count', 'how many']):
            cursor.execute("SELECT COUNT(*), AVG(total_amount), SUM(total_amount) FROM `order`")
            stats = cursor.fetchone()
            total_orders, avg_amount, total_revenue = stats
            
            return f"📊 **Order Summary**\n📈 Total Orders: {total_orders:,}\n💰 Total Revenue: ${total_revenue:.2f}\n📊 Average Order: ${avg_amount:.2f}"
        
        # Basic product queries
        elif 'product' in message_lower or 'inventory' in message_lower:
            cursor.execute("SELECT COUNT(*), SUM(stock) FROM product")
            product_stats = cursor.fetchone()
            product_count, total_stock = product_stats
            
            return f"📦 **Inventory Summary**\n🏷️ Products: {product_count}\n📊 Total Stock: {total_stock:,} units"
        
        # Default response with help
        else:
            return """🤖 **EnergyRush Admin Assistant**

I can help you with:
📋 **Orders:** "Show order 123" or "Order summary"  
📦 **Products:** "Show products" or "Inventory status"
💰 **Revenue:** "Revenue summary"

Try asking me about orders, products, or revenue!"""
        
    except Exception as e:
        return f"❌ Database query error: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()

# Theta Model Implementation
class ThetaModel:
    """Theta Model for time series forecasting - winner of M3 Competition."""
    
    def __init__(self, theta=2.0, alpha=0.5, seasonal_periods=7):
        self.theta = theta  # Theta parameter (2.0 is optimal for most series)
        self.alpha = alpha  # Smoothing parameter
        self.seasonal_periods = seasonal_periods  # Weekly seasonality
        self.model = None
        self.forecast_result = None
        
    def _apply_theta_transformation(self, data):
        """Apply Theta transformation to the time series."""
        # Theta line: theta * original + (1-theta) * linear trend
        n = len(data)
        time_index = np.arange(1, n + 1)
        
        # Fit linear trend
        slope, intercept = np.polyfit(time_index, data, 1)
        linear_trend = slope * time_index + intercept
        
        # Apply Theta transformation
        theta_line = self.theta * data + (1 - self.theta) * linear_trend
        return theta_line, slope, intercept
    
    def fit(self, data):
        """Fit the Theta model to the time series data."""
        try:
            # Apply Theta transformation
            theta_transformed, slope, intercept = self._apply_theta_transformation(data)
            
            # Use Exponential Smoothing on transformed data
            # Detect seasonality
            if len(data) >= self.seasonal_periods * 2:
                try:
                    # Try with seasonality
                    self.model = ExponentialSmoothing(
                        theta_transformed,
                        seasonal='add',
                        seasonal_periods=self.seasonal_periods,
                        trend='add',
                        damped_trend=True
                    ).fit(smoothing_level=self.alpha, optimized=True)
                    self.has_seasonality = True
                except:
                    # Fallback without seasonality
                    self.model = ExponentialSmoothing(
                        theta_transformed,
                        trend='add',
                        damped_trend=True
                    ).fit(smoothing_level=self.alpha, optimized=True)
                    self.has_seasonality = False
            else:
                # Simple exponential smoothing for short series
                self.model = ExponentialSmoothing(
                    theta_transformed,
                    trend='add'
                ).fit(smoothing_level=self.alpha, optimized=True)
                self.has_seasonality = False
                
            self.slope = slope
            self.intercept = intercept
            self.fitted_values = self.model.fittedvalues
            
            return self
            
        except Exception as e:
            print(f"Theta model fitting error: {e}")
            # Fallback to simple exponential smoothing
            self.model = ExponentialSmoothing(data, trend='add').fit(optimized=True)
            self.slope = 0
            self.intercept = np.mean(data)
            self.fitted_values = self.model.fittedvalues
            self.has_seasonality = False
            return self
    
    def forecast(self, steps=7):
        """Generate forecasts for the specified number of steps."""
        if self.model is None:
            raise ValueError("Model must be fitted before forecasting")
        
        # Generate forecast from the exponential smoothing model
        forecast = self.model.forecast(steps)
        
        # Apply inverse Theta transformation if needed
        # (In practice, Theta model often uses the transformed forecast directly)
        
        # Ensure non-negative forecasts
        forecast = np.maximum(forecast, 0)
        
        # Store forecast result
        self.forecast_result = forecast
        
        return forecast
    
    def get_model_info(self):
        """Return model information and statistics."""
        if self.model is None:
            return {}
            
        info = {
            'theta': self.theta,
            'alpha': self.alpha if hasattr(self, 'alpha') else self.model.params.get('smoothing_level', 0.3),
            'has_seasonality': getattr(self, 'has_seasonality', False),
            'seasonal_periods': self.seasonal_periods,
            'aic': self.model.aic if hasattr(self.model, 'aic') else None,
            'bic': self.model.bic if hasattr(self.model, 'bic') else None,
        }
        
        if hasattr(self.model, 'params'):
            params = self.model.params
            info.update({
                'smoothing_level': params.get('smoothing_level', None),
                'smoothing_trend': params.get('smoothing_trend', None),
                'smoothing_seasonal': params.get('smoothing_seasonal', None),
                'damping_trend': params.get('damping_trend', None)
            })
            
        return info

def generate_forecast():
    """
    Optimized forecasting using Linear Regression with seasonal features.
    Designed specifically for the low MAE dataset pattern to achieve high R² scores.
    """
    # Get historical data (all available data for better training)
    all_orders = Order.query.order_by(Order.created_at).all()
    
    if len(all_orders) < 30:  # Need minimum 30 days for reliable forecasting
        return {
            'message': 'Not enough data for forecasting (minimum 30 orders required)',
            'predictions': [],
            'model_type': 'Insufficient Data'
        }
    
    print("Fitting Optimized Linear Regression for orders and revenue...")
    
    # Create DataFrame with order data
    orders_df = pd.DataFrame([{
        'datetime': order.created_at,
        'date': order.created_at.date(),
        'amount': order.total_amount,
        'order_count': 1
    } for order in all_orders])
    
    # Aggregate by date
    daily_data = orders_df.groupby('date').agg({
        'amount': 'sum',
        'order_count': 'sum'
    }).reset_index()
    
    # Sort by date
    daily_data = daily_data.sort_values('date').reset_index(drop=True)
    
    # Create features for Linear Regression
    daily_data['date_pd'] = pd.to_datetime(daily_data['date'])
    daily_data['day_num'] = (daily_data['date_pd'] - daily_data['date_pd'].min()).dt.days
    daily_data['day_of_week'] = daily_data['date_pd'].dt.dayofweek
    daily_data['is_weekend'] = (daily_data['day_of_week'] >= 5).astype(int)
    daily_data['is_monday'] = (daily_data['day_of_week'] == 0).astype(int)
    daily_data['is_friday'] = (daily_data['day_of_week'] == 4).astype(int)
    daily_data['is_saturday'] = (daily_data['day_of_week'] == 5).astype(int)
    daily_data['is_sunday'] = (daily_data['day_of_week'] == 6).astype(int)
    
    # Add cyclical features for better seasonality capture
    daily_data['week_sin'] = np.sin(2 * np.pi * daily_data['day_of_week'] / 7)
    daily_data['week_cos'] = np.cos(2 * np.pi * daily_data['day_of_week'] / 7)
    daily_data['month_sin'] = np.sin(2 * np.pi * daily_data['day_num'] / 30)
    daily_data['month_cos'] = np.cos(2 * np.pi * daily_data['day_num'] / 30)
    
    # Feature columns for regression
    feature_cols = [
        'day_num', 'is_weekend', 'is_monday', 'is_friday', 'is_saturday', 'is_sunday',
        'week_sin', 'week_cos', 'month_sin', 'month_cos'
    ]
    
    X = daily_data[feature_cols].values
    y_orders = daily_data['order_count'].values
    y_revenue = daily_data['amount'].values
    
    # Split for validation (use last 7 days)
    if len(X) >= 14:  # Need at least 14 days total
        X_train, X_val = X[:-7], X[-7:]
        y_orders_train, y_orders_val = y_orders[:-7], y_orders[-7:]
        y_revenue_train, y_revenue_val = y_revenue[:-7], y_revenue[-7:]
        
        # Train models
        orders_model = LinearRegression()
        orders_model.fit(X_train, y_orders_train)
        
        revenue_model = LinearRegression()
        revenue_model.fit(X_train, y_revenue_train)
        
        # Validate models
        orders_pred_val = orders_model.predict(X_val)
        revenue_pred_val = revenue_model.predict(X_val)
        
        # Calculate metrics
        orders_mae = float(mean_absolute_error(y_orders_val, orders_pred_val))
        orders_r2 = float(r2_score(y_orders_val, orders_pred_val))
        revenue_mae = float(mean_absolute_error(y_revenue_val, revenue_pred_val))
        revenue_r2 = float(r2_score(y_revenue_val, revenue_pred_val))
        
    else:
        # Use full dataset for training if not enough data for validation
        orders_model = LinearRegression()
        orders_model.fit(X, y_orders)
        
        revenue_model = LinearRegression()  
        revenue_model.fit(X, y_revenue)
        
        # Use training performance as approximation
        orders_pred_train = orders_model.predict(X)
        revenue_pred_train = revenue_model.predict(X)
        
        orders_mae = float(mean_absolute_error(y_orders, orders_pred_train))
        orders_r2 = float(r2_score(y_orders, orders_pred_train))
        revenue_mae = float(mean_absolute_error(y_revenue, revenue_pred_train))
        revenue_r2 = float(r2_score(y_revenue, revenue_pred_train))
    
    print(f"Model Performance: Orders R²={orders_r2:.3f}, MAE={orders_mae:.2f} | Revenue R²={revenue_r2:.3f}, MAE=${revenue_mae:.2f}")
    
    # Generate future predictions (7 days)
    future_dates = []
    future_features = []
    start_date = daily_data['date_pd'].max() + timedelta(days=1)
    
    for i in range(7):
        future_date = start_date + timedelta(days=i)
        future_dates.append(future_date.strftime('%Y-%m-%d'))
        
        # Calculate features for future date
        day_num = (future_date - daily_data['date_pd'].min()).days
        day_of_week = future_date.weekday()
        is_weekend = int(day_of_week >= 5)
        is_monday = int(day_of_week == 0)
        is_friday = int(day_of_week == 4)
        is_saturday = int(day_of_week == 5)
        is_sunday = int(day_of_week == 6)
        
        week_sin = np.sin(2 * np.pi * day_of_week / 7)
        week_cos = np.cos(2 * np.pi * day_of_week / 7)
        month_sin = np.sin(2 * np.pi * day_num / 30)
        month_cos = np.cos(2 * np.pi * day_num / 30)
        
        future_features.append([
            day_num, is_weekend, is_monday, is_friday, is_saturday, is_sunday,
            week_sin, week_cos, month_sin, month_cos
        ])
    
    X_future = np.array(future_features)
    
    # Make predictions
    predicted_orders = orders_model.predict(X_future)
    predicted_revenue = revenue_model.predict(X_future)
    
    # Ensure non-negative predictions
    predicted_orders = np.maximum(predicted_orders, 0)
    predicted_revenue = np.maximum(predicted_revenue, 0)
    
    # Format predictions
    predictions = []
    for i in range(7):
        predictions.append({
            'date': future_dates[i],
            'predicted_orders': int(round(predicted_orders[i])),
            'predicted_revenue': float(round(predicted_revenue[i], 2)),
            'day_of_week': (start_date + timedelta(days=i)).strftime('%A')
        })
    
    # Prepare historical data for display (last 21 days)
    display_cutoff = get_colombo_time().date() - timedelta(days=21)
    historical_data = daily_data[daily_data['date'] >= display_cutoff].copy()
    
    historical_display = []
    for _, row in historical_data.iterrows():
        historical_display.append({
            'date': row['date'].strftime('%Y-%m-%d'),
            'orders': int(row['order_count']),
            'revenue': float(row['amount']),
            'day_of_week': row['date_pd'].strftime('%A')
        })
    
    return {
        'message': f'Optimized Linear Regression forecast (R²: Orders {orders_r2:.1%}, Revenue {revenue_r2:.1%})',
        'model_type': 'Optimized Linear Regression',
        'predictions': predictions,
        'chart_data': {
            'historical': {
                'dates': [item['date'] for item in historical_display],
                'orders': [item['orders'] for item in historical_display],
                'revenue': [item['revenue'] for item in historical_display]
            },
            'forecast': {
                'dates': future_dates,
                'orders': [int(round(orders)) for orders in predicted_orders],
                'revenue': [float(round(revenue, 2)) for revenue in predicted_revenue]
            }
        },
        'metrics': {
            'historical_avg_orders': float(round(historical_data['order_count'].mean(), 1)),
            'historical_avg_revenue': float(round(historical_data['amount'].mean(), 2)),
            'data_period': f'{len(daily_data)} days total, {len(historical_data)} days display',
            'prediction_period': '7 days',
            'model_accuracy': {
                'orders_mae': float(round(orders_mae, 2)),
                'orders_r2': float(round(orders_r2 * 100, 1)),
                'revenue_mae': float(round(revenue_mae, 2)),
                'revenue_r2': float(round(revenue_r2 * 100, 1))
            }
        },
        'orders_r2': orders_r2,
        'orders_mae': orders_mae,
        'revenue_r2': revenue_r2,
        'revenue_mae': revenue_mae,
        'historical_data': historical_display,
        'insights': generate_optimized_insights(predicted_orders, predicted_revenue, future_dates, orders_r2, revenue_r2)
    }

def generate_optimized_insights(predicted_orders, predicted_revenue, future_dates, orders_r2, revenue_r2):
    """Generate actionable insights from Optimized Linear Regression predictions."""
    insights = []
    
    # Model confidence assessment based on R²
    orders_confidence = max(0, min(100, orders_r2 * 100))
    revenue_confidence = max(0, min(100, revenue_r2 * 100))
    avg_confidence = (orders_confidence + revenue_confidence) / 2
    
    if avg_confidence > 85:
        insights.append(f"🎯 High model accuracy achieved! Orders: {orders_confidence:.1f}%, Revenue: {revenue_confidence:.1f}%")
    elif avg_confidence > 60:
        insights.append(f"📊 Good model performance: Orders: {orders_confidence:.1f}%, Revenue: {revenue_confidence:.1f}%")
    else:
        insights.append(f"⚠️ Model accuracy moderate: Orders: {orders_confidence:.1f}%, Revenue: {revenue_confidence:.1f}%")
    
    # Weekend vs Weekday analysis
    weekend_orders = []
    weekday_orders = []
    weekend_revenue = []
    weekday_revenue = []
    
    for i, date_str in enumerate(future_dates):
        date_obj = pd.to_datetime(date_str)
        if date_obj.dayofweek >= 5:  # Weekend
            weekend_orders.append(predicted_orders[i])
            weekend_revenue.append(predicted_revenue[i])
        else:  # Weekday
            weekday_orders.append(predicted_orders[i])
            weekday_revenue.append(predicted_revenue[i])
    
    if weekend_orders and weekday_orders:
        weekend_avg_orders = np.mean(weekend_orders)
        weekday_avg_orders = np.mean(weekday_orders)
        weekend_avg_revenue = np.mean(weekend_revenue)
        weekday_avg_revenue = np.mean(weekday_revenue)
        
        if weekend_avg_orders > weekday_avg_orders * 1.2:
            insights.append(f"📈 Weekend boost expected: {weekend_avg_orders:.0f} vs {weekday_avg_orders:.0f} weekday orders")
        elif weekday_avg_orders > weekend_avg_orders * 1.2:
            insights.append(f"💼 Stronger weekday performance: {weekday_avg_orders:.0f} vs {weekend_avg_orders:.0f} weekend orders")
        
        revenue_diff_pct = (weekend_avg_revenue / weekday_avg_revenue - 1) * 100
        if abs(revenue_diff_pct) > 20:
            insights.append(f"💰 Revenue pattern: Weekend {revenue_diff_pct:+.0f}% vs weekdays")
    
    # Trend analysis
    orders_trend = (predicted_orders[-1] - predicted_orders[0]) / len(predicted_orders)
    revenue_trend = (predicted_revenue[-1] - predicted_revenue[0]) / len(predicted_revenue)
    
    if orders_trend > 1:
        insights.append(f"📈 Growing order trend: +{orders_trend:.1f} orders/day")
    elif orders_trend < -1:
        insights.append(f"📉 Declining order trend: {orders_trend:.1f} orders/day")
    
    if revenue_trend > 50:
        insights.append(f"💹 Revenue growth trend: +${revenue_trend:.0f}/day")
    elif revenue_trend < -50:
        insights.append(f"💸 Revenue decline trend: ${revenue_trend:.0f}/day")
    
    # Peak performance insights
    max_orders_idx = np.argmax(predicted_orders)
    min_orders_idx = np.argmin(predicted_orders)
    max_date = pd.to_datetime(future_dates[max_orders_idx]).strftime('%A')
    min_date = pd.to_datetime(future_dates[min_orders_idx]).strftime('%A')
    
    if max_orders_idx != min_orders_idx:
        insights.append(f"🔝 Peak day: {max_date} ({predicted_orders[max_orders_idx]:.0f} orders)")
        insights.append(f"🔻 Slowest day: {min_date} ({predicted_orders[min_orders_idx]:.0f} orders)")
    
    # Business recommendations based on model quality
    if avg_confidence > 85:
        insights.append("✅ High confidence forecasts - suitable for inventory planning")
        insights.append("📦 Consider adjusting stock levels based on daily predictions")
    
    if not insights:
        insights.append("📊 Forecasts generated with optimized machine learning model")
    
    return insights

def generate_simple_forecast(display_data):
    """Fallback to simple linear regression when XGBoost cannot be used."""
    # This is the original simple forecast logic
    if len(display_data) < 7:
        return {
            'message': 'Insufficient data for forecasting',
            'predictions': [],
            'model_type': 'Insufficient Data'
        }
    
    display_data['date_numeric'] = pd.to_datetime(display_data['date']).astype(int) // 10**9
    X = display_data['date_numeric'].values.reshape(-1, 1)
    y_orders = display_data['order_count'].values
    y_revenue = display_data['amount'].values
    
    model_orders = LinearRegression().fit(X, y_orders)
    model_revenue = LinearRegression().fit(X, y_revenue)
    
    last_date = display_data['date'].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, 8)]
    future_numeric = [int(pd.to_datetime(date).timestamp()) for date in future_dates]
    
    predicted_orders = model_orders.predict(np.array(future_numeric).reshape(-1, 1))
    predicted_revenue = model_revenue.predict(np.array(future_numeric).reshape(-1, 1))
    
    return {
        'message': 'Forecast generated using Linear Regression (fallback)',
        'model_type': 'Linear Regression',
        'predictions': [
            {
                'date': date.strftime('%Y-%m-%d'),
                'predicted_orders': max(0, int(round(orders))),
                'predicted_revenue': max(0, round(revenue, 2))
            }
            for date, orders, revenue in zip(future_dates, predicted_orders, predicted_revenue)
        ],
        'chart_data': {
            'historical': {
                'dates': [date.strftime('%Y-%m-%d') for date in display_data['date']],
                'orders': display_data['order_count'].tolist(),
                'revenue': display_data['amount'].tolist()
            },
            'forecast': {
                'dates': [date.strftime('%Y-%m-%d') for date in future_dates],
                'orders': [max(0, int(round(orders))) for orders in predicted_orders],
                'revenue': [max(0, round(revenue, 2)) for revenue in predicted_revenue]
            }
        },
        'metrics': {
            'historical_avg_orders': round(display_data['order_count'].mean(), 1),
            'historical_avg_revenue': round(display_data['amount'].mean(), 2),
            'data_period': '21 days',
            'prediction_period': '7 days'
        }
    }

def generate_theta_insights(predicted_orders, predicted_revenue, future_dates, orders_r2, revenue_r2, orders_model_info, revenue_model_info):
    """Generate actionable insights from Theta Model predictions."""
    insights = []
    
    # Model confidence assessment based on R² and model characteristics
    orders_confidence = max(0, min(100, orders_r2 * 100))
    revenue_confidence = max(0, min(100, revenue_r2 * 100))
    
    avg_confidence = (orders_confidence + revenue_confidence) / 2
    
    if avg_confidence > 80:
        insights.append("🎯 High confidence Theta predictions - excellent for strategic planning")
    elif avg_confidence > 60:
        insights.append("⚡ Strong Theta model performance - reliable for business decisions")
    elif avg_confidence > 40:
        insights.append("📊 Moderate confidence predictions - good directional guidance")
    else:
        insights.append("⚠️ Lower confidence - use as trend indication only")
    
    # Seasonality insights
    if orders_model_info.get('has_seasonality', False) or revenue_model_info.get('has_seasonality', False):
        insights.append("📅 Theta model detected weekly seasonal patterns - leverage for planning")
    else:
        insights.append("📈 No strong seasonality detected - focus on trend-based strategies")
    
    # Weekend vs Weekday analysis
    weekend_orders = []
    weekday_orders = []
    weekend_revenue = []
    weekday_revenue = []
    
    for i, date in enumerate(future_dates):
        if pd.to_datetime(date).dayofweek >= 5:
            weekend_orders.append(predicted_orders[i])
            weekend_revenue.append(predicted_revenue[i])
        else:
            weekday_orders.append(predicted_orders[i])
            weekday_revenue.append(predicted_revenue[i])
    
    if weekend_orders and weekday_orders:
        weekend_avg_orders = np.mean(weekend_orders)
        weekday_avg_orders = np.mean(weekday_orders)
        weekend_avg_revenue = np.mean(weekend_revenue)
        weekday_avg_revenue = np.mean(weekday_revenue)
        
        if weekend_avg_orders > weekday_avg_orders * 1.15:
            insights.append(f"🏖️ Weekend surge expected: {weekend_avg_orders:.1f} vs {weekday_avg_orders:.1f} weekday orders")
        elif weekday_avg_orders > weekend_avg_orders * 1.15:
            insights.append(f"💼 Weekday dominance: {weekday_avg_orders:.1f} vs {weekend_avg_orders:.1f} weekend orders")
        
        # Revenue per order analysis
        if len(weekend_orders) > 0 and len(weekday_orders) > 0:
            weekend_aov = weekend_avg_revenue / weekend_avg_orders if weekend_avg_orders > 0 else 0
            weekday_aov = weekday_avg_revenue / weekday_avg_orders if weekday_avg_orders > 0 else 0
            
            if weekend_aov > weekday_aov * 1.1:
                insights.append(f"💰 Higher weekend AOV: ${weekend_aov:.2f} vs ${weekday_aov:.2f}")
            elif weekday_aov > weekend_aov * 1.1:
                insights.append(f"🎯 Higher weekday AOV: ${weekday_aov:.2f} vs ${weekend_aov:.2f}")
    
    # Theta model specific insights
    orders_alpha = orders_model_info.get('alpha', 0.3)
    if orders_alpha > 0.7:
        insights.append("📈 Theta detects rapidly changing order patterns - stay agile")
    elif orders_alpha < 0.3:
        insights.append("📊 Theta shows stable order patterns - predictable demand")
    
    # Peak day identification
    peak_day_idx = int(np.argmax(predicted_orders))
    peak_date = future_dates[peak_day_idx]
    peak_day_name = pd.to_datetime(peak_date).strftime('%A')
    peak_orders = int(predicted_orders[peak_day_idx])
    insights.append(f"🎯 Theta identifies {peak_day_name} as peak: {peak_orders} orders")
    
    # Revenue trend analysis
    total_predicted_revenue = float(sum(predicted_revenue))
    daily_avg_revenue = total_predicted_revenue / len(predicted_revenue)
    
    # Check for growth/decline trend
    early_revenue = np.mean(predicted_revenue[:3]) if len(predicted_revenue) >= 3 else predicted_revenue[0]
    late_revenue = np.mean(predicted_revenue[-3:]) if len(predicted_revenue) >= 3 else predicted_revenue[-1]
    
    if late_revenue > early_revenue * 1.1:
        growth_rate = ((late_revenue / early_revenue) - 1) * 100
        insights.append(f"🚀 Revenue acceleration trend: +{growth_rate:.1f}% growth detected")
    elif early_revenue > late_revenue * 1.1 and late_revenue > 0:
        decline_rate = ((early_revenue / late_revenue) - 1) * 100
        insights.append(f"📉 Revenue deceleration: -{decline_rate:.1f}% decline trend")
    else:
        insights.append(f"💰 Stable revenue pattern: ${total_predicted_revenue:.0f} weekly (${daily_avg_revenue:.0f}/day)")
    
    # Model quality insight
    orders_aic = orders_model_info.get('aic')
    if orders_aic and orders_aic < 100:
        insights.append("✨ Excellent Theta model fit - high forecast reliability")
    
    return insights

def generate_forecast_insights(predicted_orders, predicted_revenue, future_dates):
    """Generate actionable insights from predictions (fallback function)."""
    insights = []
    
    # Weekend vs Weekday analysis
    weekend_orders = []
    weekday_orders = []
    for i, date in enumerate(future_dates):
        if pd.to_datetime(date).dayofweek >= 5:
            weekend_orders.append(predicted_orders[i])
        else:
            weekday_orders.append(predicted_orders[i])
    
    if weekend_orders and weekday_orders:
        weekend_avg = np.mean(weekend_orders)
        weekday_avg = np.mean(weekday_orders)
        if weekend_avg > weekday_avg * 1.2:
            insights.append("📈 Weekend demand expected to be significantly higher - ensure adequate staffing")
        elif weekday_avg > weekend_avg * 1.2:
            insights.append("💼 Weekday demand stronger - consider weekday promotions to boost weekend sales")
    
    # Trend analysis
    if len(predicted_orders) > 1:
        trend = np.polyfit(range(len(predicted_orders)), predicted_orders, 1)[0]
        if trend > 0.5:
            insights.append("📊 Strong upward trend detected - consider increasing inventory")
        elif trend < -0.5:
            insights.append("📉 Declining trend predicted - review marketing strategies")
    
    # Peak day identification
    peak_day_idx = int(np.argmax(predicted_orders))
    peak_date = future_dates[peak_day_idx]
    peak_day_name = pd.to_datetime(peak_date).strftime('%A')
    insights.append(f"🎯 Peak demand expected on {peak_day_name} with {int(float(predicted_orders[peak_day_idx]))} orders")
    
    # Revenue insights
    total_predicted_revenue = float(sum(predicted_revenue))
    daily_avg_revenue = total_predicted_revenue / len(predicted_revenue)
    insights.append(f"💰 Expected weekly revenue: ${total_predicted_revenue:.2f} (avg ${daily_avg_revenue:.2f}/day)")
    
    return insights


def generate_context_for_nlp():
    # Generate context from database for NLP queries
    context_parts = []
    
    # Orders information
    orders = Order.query.all()
    for order in orders[-10:]:  # Last 10 orders
        context_parts.append(f"Order {order.id}: Customer {order.customer_name}, Status: {order.status}, Amount: ${order.total_amount}, Date: {order.created_at.strftime('%Y-%m-%d')}")
    
    # Products information
    products = Product.query.all()
    for product in products:
        context_parts.append(f"Product {product.name}: Price ${product.price}, Stock: {product.stock} units")
    
    return ". ".join(context_parts)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Add sample data if database is empty
        if Product.query.count() == 0:
            sample_products = [
                Product(name="Red Bull Energy Drink", description="The original energy drink that gives you wings", price=2.99, stock=50, image_url="https://via.placeholder.com/300x300?text=Red+Bull"),
                Product(name="Monster Energy", description="Unleash the beast within", price=3.49, stock=30, image_url="https://via.placeholder.com/300x300?text=Monster"),
                Product(name="Ultra Boost Energy", description="Maximum energy for maximum performance", price=4.99, stock=25, image_url="https://via.placeholder.com/300x300?text=Ultra+Boost"),
                Product(name="Lightning Strike", description="Strike fast with instant energy", price=3.99, stock=40, image_url="https://via.placeholder.com/300x300?text=Lightning"),
                Product(name="Power Surge", description="Surge ahead with powerful energy", price=3.29, stock=35, image_url="https://via.placeholder.com/300x300?text=Power+Surge"),
            ]
            
            for product in sample_products:
                db.session.add(product)
            
            db.session.commit()
    
    app.run(debug=True, port=8000)