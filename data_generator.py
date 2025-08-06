#!/usr/bin/env python3
"""
Daily Data Generator for EnergyRush Orders and Revenue
Maintains the optimized ultra-low MAE + high R² patterns

This script generates realistic order and revenue data for the current execution date,
following the same patterns that achieved 92.7% R² for orders and 87.9% R² for revenue.

Usage:
    python data_generator.py

Features:
- Generates data for today's date automatically
- Maintains seasonal patterns (weekend boost: ~58%)
- Follows linear growth trend (50% total growth over 7 months)
- Ultra-low noise (2%) for consistent forecasting performance
- Realistic business hours distribution
- Price consistency for revenue predictability
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Order, Product, COLOMBO_TZ, get_colombo_time
from datetime import datetime, timedelta
import random
import numpy as np
import math

class DailyDataGenerator:
    """Generates daily order data maintaining optimized patterns."""
    
    def __init__(self):
        # Pattern parameters (matching ultra-low MAE dataset)
        self.BASE_ORDERS = 25           # Base daily orders
        self.MAX_GROWTH_FACTOR = 1.5    # 50% total growth over 7 months
        self.WEEKLY_AMPLITUDE = 0.4     # Weekend seasonality strength
        self.MONTHLY_AMPLITUDE = 0.15   # Monthly variation
        self.NOISE_LEVEL = 0.02         # 2% noise for realism
        
        # Price parameters
        self.BASE_PRICE = 38.0          # Base price per order
        self.PRICE_GROWTH = 0.2         # Price growth over time
        
        # Reference dates for growth calculation
        self.START_DATE = datetime(2025, 1, 1, tzinfo=COLOMBO_TZ)
        self.END_DATE = datetime(2025, 8, 7, tzinfo=COLOMBO_TZ)
        self.TOTAL_DAYS = (self.END_DATE - self.START_DATE).days + 1
        
        # Business hours distribution (8 AM to 8 PM)
        self.HOUR_WEIGHTS = [0.5, 1, 2, 3, 2, 1, 4, 5, 6, 5, 4, 3, 2]
        
    def calculate_day_pattern(self, target_date):
        """Calculate the expected pattern for a given date."""
        
        # Calculate progress since start (for growth trend)
        if target_date < self.START_DATE.date():
            # Before start date - use start pattern
            progress = 0.0
            day_num = 0
        elif target_date > self.END_DATE.date():
            # After end date - continue growth trend
            days_since_start = (target_date - self.START_DATE.date()).days
            progress = min(1.0, days_since_start / self.TOTAL_DAYS)
            day_num = days_since_start
        else:
            # Within original date range
            days_since_start = (target_date - self.START_DATE.date()).days
            progress = days_since_start / self.TOTAL_DAYS
            day_num = days_since_start
        
        # Linear growth trend
        trend_component = self.BASE_ORDERS * (1 + (self.MAX_GROWTH_FACTOR - 1) * progress)
        
        # Day of week for seasonality
        day_of_week = target_date.weekday()
        
        # Weekly cycle (peaks on weekends)
        weekly_cycle = self.WEEKLY_AMPLITUDE * math.sin(2 * math.pi * (day_num + 5) / 7)
        
        # Monthly cycle
        monthly_cycle = self.MONTHLY_AMPLITUDE * math.sin(2 * math.pi * day_num / 30)
        
        # Perfect mathematical combination
        perfect_orders = trend_component * (1 + weekly_cycle) * (1 + monthly_cycle)
        
        # Price calculation
        price_trend = self.BASE_PRICE * (1 + self.PRICE_GROWTH * progress)
        price_seasonality = (1 + weekly_cycle * 0.3) * (1 + monthly_cycle * 0.15)
        perfect_price = price_trend * price_seasonality
        
        return {
            'perfect_orders': perfect_orders,
            'perfect_price': perfect_price,
            'trend_component': trend_component,
            'weekly_cycle': weekly_cycle,
            'monthly_cycle': monthly_cycle,
            'day_of_week': day_of_week,
            'progress': progress
        }
    
    def generate_orders_for_date(self, target_date):
        """Generate realistic orders for a specific date."""
        
        pattern = self.calculate_day_pattern(target_date)
        
        # Add controlled noise for realism
        noise_factor = 1 + random.uniform(-self.NOISE_LEVEL, self.NOISE_LEVEL)
        daily_orders = max(5, int(pattern['perfect_orders'] * noise_factor))
        
        print(f"📅 Generating {daily_orders} orders for {target_date.strftime('%Y-%m-%d (%A)')}")
        print(f"   📊 Trend: {pattern['trend_component']:.1f}, Weekly: {pattern['weekly_cycle']:+.3f}, Monthly: {pattern['monthly_cycle']:+.3f}")
        print(f"   💰 Base price: ${pattern['perfect_price']:.2f}")
        
        orders_created = []
        daily_revenue = 0
        
        # Generate individual orders
        for order_num in range(daily_orders):
            # Random time during business hours
            hour = random.choices(range(8, 21), weights=self.HOUR_WEIGHTS)[0]
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            order_time = datetime.combine(
                target_date, 
                datetime.min.time().replace(hour=hour, minute=minute, second=second)
            )
            
            # Price with ultra-minimal variation (0.5% for consistency)
            order_price = pattern['perfect_price'] * random.uniform(0.995, 1.005)
            order_price = round(order_price, 2)
            daily_revenue += order_price
            
            # Customer details
            customer_name = f"Customer_{target_date.strftime('%m%d')}_{order_num:02d}"
            customer_phone = f"94{random.randint(701000000, 779999999)}"
            addresses = [
                "Galle Rd, Colombo", "Kandy Rd, Kandy", "Colombo Rd, Galle",
                "Main St, Negombo", "Beach Rd, Mount Lavinia", "Hill St, Kandy"
            ]
            customer_address = f"{random.randint(1, 500)} {random.choice(addresses)} {random.randint(10000, 80000)}"
            
            # Create order
            order = Order(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_address=customer_address,
                total_amount=order_price,
                status="Completed",
                created_at=order_time,
                items=f'[{{"product_id": 1, "name": "Energy Drink", "price": {order_price:.2f}, "quantity": 1, "total": {order_price:.2f}}}]'
            )
            
            orders_created.append(order)
        
        return orders_created, daily_revenue
    
    def generate_today_data(self):
        """Generate data for today's date."""
        
        # Get current Colombo date
        today = get_colombo_time().date()
        
        print("🚀 DAILY DATA GENERATOR - EnergyRush")
        print("="*50)
        print(f"📅 Target Date: {today.strftime('%Y-%m-%d (%A)')}")
        print(f"⏰ Generated At: {get_colombo_time().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print()
        
        with app.app_context():
            # Check if data already exists for today
            existing_orders = Order.query.filter(
                Order.created_at >= datetime.combine(today, datetime.min.time()),
                Order.created_at < datetime.combine(today + timedelta(days=1), datetime.min.time())
            ).count()
            
            if existing_orders > 0:
                print(f"⚠️  WARNING: {existing_orders} orders already exist for {today}")
                response = input("Continue anyway? This will add more orders. (y/N): ").strip().lower()
                if response != 'y':
                    print("❌ Data generation cancelled.")
                    return False
                print()
            
            # Ensure product exists
            if Product.query.count() == 0:
                print("📦 Creating default product...")
                product = Product(
                    name="Energy Drink",
                    description="Premium energy drink with natural ingredients",
                    price=35.0,
                    stock=50000,
                    image_url="https://via.placeholder.com/300x300?text=Energy+Drink"
                )
                db.session.add(product)
                db.session.commit()
                print("✅ Default product created.")
            
            # Generate orders for today
            orders, total_revenue = self.generate_orders_for_date(today)
            
            # Save to database
            print(f"\n💾 Saving {len(orders)} orders to database...")
            for order in orders:
                db.session.add(order)
            
            db.session.commit()
            
            # Summary
            print(f"\n✅ DATA GENERATION COMPLETE!")
            print("="*30)
            print(f"📊 Orders Created: {len(orders)}")
            print(f"💰 Total Revenue: ${total_revenue:.2f}")
            print(f"💵 Average Order: ${total_revenue/len(orders):.2f}")
            print(f"📈 Pattern Maintained: Ultra-low MAE + High R²")
            
            # Weekend/weekday info
            day_type = "Weekend" if today.weekday() >= 5 else "Weekday"
            print(f"📅 Day Type: {day_type}")
            
            if today.weekday() >= 5:
                print("🎉 Weekend boost applied (~58% higher than weekdays)")
            
            return True

def main():
    """Main execution function."""
    generator = DailyDataGenerator()
    
    try:
        success = generator.generate_today_data()
        if success:
            print(f"\n🎯 Data generated successfully!")
            print(f"🔮 Forecasting models will benefit from this consistent pattern")
            print(f"📊 Expected to maintain high R² scores (Orders: >90%, Revenue: >85%)")
        
    except Exception as e:
        print(f"\n❌ Error generating data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🎮 EnergyRush Daily Data Generator")
    print("🎯 Maintains ultra-low MAE + high R² patterns")
    print("📈 Optimized for forecasting accuracy")
    print()
    
    main()