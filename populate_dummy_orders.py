#!/usr/bin/env python3
"""
Dummy Order Generator for EnergyRush Database
Generates realistic orders from 2024-01-01 to today with seasonal patterns and variations.
"""

import random
import json
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys
import os

# Add current directory to path so we can import from app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Product, Order

# Configuration
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime.now()
TOTAL_DAYS = (END_DATE - START_DATE).days + 1

# Realistic customer names
CUSTOMER_NAMES = [
    "John Smith", "Sarah Johnson", "Mike Davis", "Emily Brown", "David Wilson",
    "Jessica Miller", "Robert Garcia", "Ashley Martinez", "Chris Anderson", "Amanda Taylor",
    "Jason Lee", "Jennifer White", "Kevin Thompson", "Lisa Jackson", "Mark Harris",
    "Rachel Clark", "Daniel Lewis", "Michelle Robinson", "Ryan Walker", "Laura Hall",
    "Brandon Young", "Nicole Allen", "Tyler King", "Stephanie Wright", "Justin Lopez",
    "Megan Hill", "Andrew Green", "Samantha Adams", "Eric Baker", "Heather Nelson",
    "Jonathan Carter", "Brittany Mitchell", "Matthew Perez", "Kimberly Roberts", "Joshua Turner",
    "Vanessa Phillips", "Nathan Campbell", "Christina Parker", "Cameron Evans", "Alexis Edwards",
    "Jordan Collins", "Danielle Stewart", "Austin Sanchez", "Kayla Morris", "Sean Rogers",
    "Tiffany Reed", "Cody Cook", "Monica Bailey", "Trevor Cooper", "Jasmine Richardson",
    "Blake Cox", "Sierra Ward", "Evan Torres", "Destiny Peterson", "Lucas Gray",
    "Bianca Ramirez", "Mason James", "Mariah Watson", "Cole Brooks", "Jenna Kelly",
    "Caleb Sanders", "Paige Price", "Ian Bennett", "Mackenzie Wood", "Preston Barnes"
]

# Phone number prefixes (realistic area codes)
PHONE_PREFIXES = [
    "555-0", "555-1", "555-2", "555-3", "555-4", "555-5", "555-6", "555-7", "555-8", "555-9",
    "212-5", "213-4", "310-2", "415-3", "312-6", "713-8", "214-9", "305-1", "404-7", "206-3"
]

# Realistic addresses
ADDRESSES = [
    "123 Main Street, Springfield, IL 62701",
    "456 Oak Avenue, Denver, CO 80202",
    "789 Pine Road, Austin, TX 73301",
    "321 Elm Street, Seattle, WA 98101",
    "654 Maple Drive, Phoenix, AZ 85001",
    "987 Cedar Lane, Portland, OR 97201",
    "147 Birch Street, San Diego, CA 92101",
    "258 Willow Avenue, Las Vegas, NV 89101",
    "369 Spruce Road, Miami, FL 33101",
    "741 Cherry Street, Boston, MA 02101",
    "852 Walnut Drive, Chicago, IL 60601",
    "963 Hickory Lane, New York, NY 10001",
    "159 Poplar Avenue, Los Angeles, CA 90001",
    "357 Sycamore Street, Houston, TX 77001",
    "486 Magnolia Road, Atlanta, GA 30301",
    "624 Dogwood Drive, Nashville, TN 37201",
    "735 Redwood Lane, Sacramento, CA 95814",
    "846 Aspen Street, Salt Lake City, UT 84101",
    "951 Juniper Avenue, Oklahoma City, OK 73101",
    "162 Cypress Road, Tampa, FL 33601",
    "273 Hawthorn Street, Charlotte, NC 28201",
    "384 Laurel Drive, Indianapolis, IN 46201",
    "495 Chestnut Lane, Columbus, OH 43215",
    "516 Beech Avenue, Milwaukee, WI 53202",
    "627 Ash Street, Kansas City, MO 64108"
]

def generate_phone_number():
    """Generate a realistic phone number."""
    prefix = random.choice(PHONE_PREFIXES)
    suffix = f"{random.randint(100, 999)}"
    return f"{prefix}{suffix}"

def get_seasonal_multiplier(date):
    """Get seasonal demand multiplier based on date."""
    month = date.month
    
    # Higher demand in summer months and around holidays
    if month in [6, 7, 8]:  # Summer
        return 1.4
    elif month in [12, 1]:  # Holiday season
        return 1.3
    elif month in [3, 4, 5]:  # Spring
        return 1.2
    elif month in [9, 10, 11]:  # Fall
        return 1.1
    else:
        return 1.0

def get_weekly_multiplier(date):
    """Get weekly demand multiplier (weekends are busier)."""
    if date.weekday() in [5, 6]:  # Saturday and Sunday
        return 1.3
    elif date.weekday() in [0, 4]:  # Monday and Friday
        return 1.1
    else:
        return 1.0

def generate_order_items(products, date):
    """Generate realistic order items based on products and date."""
    # Determine number of items (weighted towards smaller orders)
    num_items_weights = [0.4, 0.3, 0.15, 0.1, 0.05]  # 1-5 items
    num_items = random.choices(range(1, 6), weights=num_items_weights)[0]
    
    selected_products = random.sample(products, min(num_items, len(products)))
    items = []
    total = 0
    
    for product in selected_products:
        # Quantity weighted towards 1-2 items
        quantity_weights = [0.6, 0.25, 0.1, 0.05]  # 1-4 quantity
        quantity = random.choices(range(1, 5), weights=quantity_weights)[0]
        
        item = {
            'product_id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': quantity
        }
        items.append(item)
        total += product.price * quantity
    
    return items, total

def generate_orders_for_date(date, products):
    """Generate orders for a specific date."""
    orders = []
    
    # Base number of orders per day (3-8 orders)
    base_orders = random.randint(3, 8)
    
    # Apply seasonal and weekly multipliers
    seasonal_mult = get_seasonal_multiplier(date)
    weekly_mult = get_weekly_multiplier(date)
    
    # Calculate actual number of orders for this date
    target_orders = int(base_orders * seasonal_mult * weekly_mult)
    target_orders = max(1, min(target_orders, 15))  # Clamp between 1 and 15
    
    for _ in range(target_orders):
        # Generate order
        customer_name = random.choice(CUSTOMER_NAMES)
        customer_phone = generate_phone_number()
        customer_address = random.choice(ADDRESSES)
        
        # Generate items and calculate total
        items, total_amount = generate_order_items(products, date)
        
        # Determine order status based on how old the order is
        days_old = (datetime.now() - date).days
        
        if days_old < 1:
            status_weights = [0.8, 0.15, 0.05]  # Pending, Shipped, Delivered
            status_options = ['Pending', 'Shipped', 'Delivered']
        elif days_old < 3:
            status_weights = [0.3, 0.5, 0.2]  # Pending, Shipped, Delivered
            status_options = ['Pending', 'Shipped', 'Delivered']
        elif days_old < 7:
            status_weights = [0.1, 0.3, 0.6]  # Pending, Shipped, Delivered
            status_options = ['Pending', 'Shipped', 'Delivered']
        else:
            status_weights = [0.05, 0.15, 0.8]  # Pending, Shipped, Delivered
            status_options = ['Pending', 'Shipped', 'Delivered']
        
        status = random.choices(status_options, weights=status_weights)[0]
        
        # Create order with random time during the day
        order_datetime = date.replace(
            hour=random.randint(8, 22),  # 8 AM to 10 PM
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
        
        order = Order(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            total_amount=total_amount,
            status=status,
            items=json.dumps(items),
            created_at=order_datetime
        )
        
        orders.append(order)
    
    return orders

def populate_dummy_orders():
    """Populate the database with dummy orders."""
    with app.app_context():
        # Check if we have products
        products = Product.query.all()
        if not products:
            print("❌ No products found in database. Please run the main app first to create sample products.")
            return
        
        print(f"📊 Found {len(products)} products in database")
        
        # Check existing orders
        existing_orders = Order.query.count()
        if existing_orders > 0:
            print(f"⚠️  Found {existing_orders} existing orders in database.")
            print("🗑️  Deleting all existing orders to start fresh...")
            Order.query.delete()
            db.session.commit()
            print("✅ Deleted all existing orders")
        
        # Generate orders for each date
        print(f"🚀 Generating dummy orders from {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
        print(f"📅 Processing {TOTAL_DAYS} days...")
        
        total_orders = 0
        current_date = START_DATE
        
        while current_date <= END_DATE:
            # Generate orders for this date
            daily_orders = generate_orders_for_date(current_date, products)
            
            # Add orders to database
            for order in daily_orders:
                db.session.add(order)
            
            total_orders += len(daily_orders)
            
            # Show progress every 30 days
            if (current_date - START_DATE).days % 30 == 0:
                progress = ((current_date - START_DATE).days / TOTAL_DAYS) * 100
                print(f"📈 Progress: {progress:.1f}% - Generated {total_orders} orders so far...")
            
            current_date += timedelta(days=1)
        
        # Commit all orders to database
        try:
            db.session.commit()
            print(f"\n✅ Successfully generated {total_orders} dummy orders!")
            
            # Show statistics
            print("\n📊 Order Statistics:")
            print(f"   Total Orders: {total_orders}")
            print(f"   Average Orders per Day: {total_orders / TOTAL_DAYS:.1f}")
            
            # Status breakdown
            pending_count = Order.query.filter_by(status='Pending').count()
            shipped_count = Order.query.filter_by(status='Shipped').count()
            delivered_count = Order.query.filter_by(status='Delivered').count()
            
            print(f"   Pending: {pending_count}")
            print(f"   Shipped: {shipped_count}")
            print(f"   Delivered: {delivered_count}")
            
            # Revenue calculation
            total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar()
            print(f"   Total Revenue: ${total_revenue:.2f}")
            
            print(f"\n🎉 Database successfully populated with realistic order data!")
            print(f"💡 You can now test the forecasting and analytics features with real data.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving orders to database: {e}")

if __name__ == "__main__":
    print("🚀 EnergyRush Dummy Order Generator")
    print("=" * 50)
    populate_dummy_orders()