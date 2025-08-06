#!/usr/bin/env python3
"""
Debug Theta Model to understand why R² is 0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Order, get_colombo_time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score

def debug_theta_model():
    """Debug the Theta Model implementation"""
    
    with app.app_context():
        print('🔍 DEBUGGING THETA MODEL IMPLEMENTATION')
        print('='*50)
        
        # Get historical data (same logic as generate_forecast)
        historical_days = 45
        cutoff_date = get_colombo_time() - timedelta(days=historical_days)
        
        # Get all historical orders
        all_orders = Order.query.filter(Order.created_at >= cutoff_date).order_by(Order.created_at).all()
        
        print(f'📊 Data Overview:')
        print(f'   Total orders found: {len(all_orders)}')
        print(f'   Cutoff date: {cutoff_date.strftime("%Y-%m-%d")}')
        print(f'   Historical days: {historical_days}')
        
        if len(all_orders) < 14:
            print('❌ Not enough orders for Theta Model')
            return
        
        # Create DataFrame
        order_data = []
        for order in all_orders:
            order_data.append({
                'date': order.created_at.date(),
                'amount': float(order.total_amount)
            })
        
        df = pd.DataFrame(order_data)
        
        # Group by date
        daily_data = df.groupby('date').agg({
            'amount': ['count', 'sum']
        }).reset_index()
        daily_data.columns = ['date', 'orders', 'revenue']
        daily_data = daily_data.sort_values('date')
        
        print(f'📅 Daily Data:')
        print(f'   Days with data: {len(daily_data)}')
        print(f'   Date range: {daily_data["date"].min()} to {daily_data["date"].max()}')
        print(f'   Order range: {daily_data["orders"].min()} to {daily_data["orders"].max()}')
        print(f'   Revenue range: ${daily_data["revenue"].min():.2f} to ${daily_data["revenue"].max():.2f}')
        
        # Check data patterns
        print(f'\n📈 Data Patterns:')
        print(f'   Orders mean: {daily_data["orders"].mean():.2f}')
        print(f'   Orders std: {daily_data["orders"].std():.2f}')
        print(f'   Revenue mean: ${daily_data["revenue"].mean():.2f}')
        print(f'   Revenue std: ${daily_data["revenue"].std():.2f}')
        
        # Check if we have enough data points
        orders_series = daily_data['orders']
        revenue_series = daily_data['revenue']
        
        print(f'\n🎯 Series Analysis:')
        print(f'   Orders series length: {len(orders_series)}')
        print(f'   Revenue series length: {len(revenue_series)}')
        print(f'   Orders variance: {orders_series.var():.4f}')
        print(f'   Revenue variance: {revenue_series.var():.4f}')
        
        # Test simple validation
        if len(orders_series) >= 14:
            # Use last 7 days as validation
            train_orders = orders_series[:-7]
            val_orders = orders_series[-7:]
            train_revenue = revenue_series[:-7]
            val_revenue = revenue_series[-7:]
            
            print(f'\n🔬 Validation Split:')
            print(f'   Training days: {len(train_orders)}')
            print(f'   Validation days: {len(val_orders)}')
            print(f'   Train orders mean: {train_orders.mean():.2f}')
            print(f'   Val orders mean: {val_orders.mean():.2f}')
            
            # Simple baseline prediction (mean)
            baseline_pred_orders = np.full(len(val_orders), train_orders.mean())
            baseline_pred_revenue = np.full(len(val_revenue), train_revenue.mean())
            
            print(f'\n📊 Baseline Performance:')
            orders_mae_baseline = mean_absolute_error(val_orders, baseline_pred_orders)
            orders_r2_baseline = r2_score(val_orders, baseline_pred_orders)
            revenue_mae_baseline = mean_absolute_error(val_revenue, baseline_pred_revenue)
            revenue_r2_baseline = r2_score(val_revenue, baseline_pred_revenue)
            
            print(f'   Baseline Orders MAE: {orders_mae_baseline:.2f}')
            print(f'   Baseline Orders R²: {orders_r2_baseline:.4f}')
            print(f'   Baseline Revenue MAE: ${revenue_mae_baseline:.2f}')
            print(f'   Baseline Revenue R²: {revenue_r2_baseline:.4f}')
            
            # Show actual vs predicted values
            print(f'\n🔍 Detailed Comparison (Orders):')
            print('   Day | Actual | Predicted | Diff')
            print('   ----|--------|-----------|-----')
            for i in range(len(val_orders)):
                actual = val_orders.iloc[i]
                predicted = baseline_pred_orders[i]
                diff = actual - predicted
                print(f'   {i+1:2d}  |   {actual:4.0f} |     {predicted:4.1f} | {diff:+5.1f}')
                
            print(f'\n📋 Validation Data Stats:')
            print(f'   Actual orders: {list(val_orders)}')
            print(f'   Variance in actual: {val_orders.var():.4f}')
            print(f'   Is constant? {val_orders.nunique() == 1}')
            
            # Check for constant values (causes R² = 0)
            if val_orders.nunique() == 1:
                print('⚠️  WARNING: Validation orders are constant - R² will be 0!')
            if val_revenue.nunique() == 1:
                print('⚠️  WARNING: Validation revenue is constant - R² will be 0!')
        else:
            print('❌ Not enough data for validation split')

if __name__ == "__main__":
    debug_theta_model()