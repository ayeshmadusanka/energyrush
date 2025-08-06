#!/usr/bin/env python3
"""
Verify the generated dummy orders in the database.
"""

from app import app, db, Order
from datetime import datetime

def verify_orders():
    with app.app_context():
        # Check total orders
        total_orders = Order.query.count()
        print(f"📊 Total Orders in Database: {total_orders}")
        
        # Check order distribution by month
        print('\n📊 Order Distribution by Month:')
        
        # Get monthly counts using SQLAlchemy text
        from sqlalchemy import text
        monthly_data = db.session.execute(text('''
            SELECT strftime('%Y-%m', created_at) as month,
                   COUNT(*) as order_count,
                   ROUND(SUM(total_amount), 2) as revenue
            FROM "order"
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month
        ''')).fetchall()
        
        for row in monthly_data:
            print(f'  {row[0]}: {row[1]} orders, ${row[2]} revenue')
        
        # Check recent orders
        print('\n📅 Recent Orders (Last 5):')
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        for order in recent_orders:
            print(f'  Order #{order.id}: {order.customer_name} - ${order.total_amount} - {order.status} ({order.created_at.strftime("%Y-%m-%d %H:%M")})')
            
        # Check status distribution
        print('\n📈 Status Distribution:')
        statuses = ['Pending', 'Shipped', 'Delivered']
        for status in statuses:
            count = Order.query.filter_by(status=status).count()
            percentage = (count / total_orders) * 100 if total_orders > 0 else 0
            print(f'  {status}: {count} ({percentage:.1f}%)')
        
        # Check date range
        oldest = Order.query.order_by(Order.created_at.asc()).first()
        newest = Order.query.order_by(Order.created_at.desc()).first()
        
        if oldest and newest:
            print(f'\n📅 Date Range:')
            print(f'  Oldest Order: {oldest.created_at.strftime("%Y-%m-%d %H:%M")}')
            print(f'  Newest Order: {newest.created_at.strftime("%Y-%m-%d %H:%M")}')
            
        # Check total revenue
        total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar()
        print(f'\n💰 Total Revenue: ${total_revenue:.2f}')

if __name__ == "__main__":
    verify_orders()