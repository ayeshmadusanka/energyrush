#!/usr/bin/env python3
"""
Optimized forecasting implementation for low MAE + high R² performance.
This will replace the existing Theta Model approach.
"""

def generate_optimized_forecast():
    """
    Optimized forecasting using Linear Regression with seasonal features.
    Designed specifically for the low MAE dataset pattern.
    """
    # Get historical data (all available data for better training)
    all_orders = Order.query.order_by(Order.created_at).all()
    
    if len(all_orders) < 30:  # Need minimum 30 days for reliable forecasting
        return {
            'message': 'Not enough data for forecasting (minimum 30 orders required)',
            'predictions': [],
            'model_type': 'Insufficient Data'
        }
    
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
    
    # Prepare historical data for display
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
        'predictions': predictions,
        'historical_data': historical_display,
        'model_type': 'Optimized Linear Regression',
        'accuracy': {
            'orders_r2': orders_r2,
            'orders_mae': orders_mae,
            'revenue_r2': revenue_r2,
            'revenue_mae': revenue_mae
        },
        'orders_r2': orders_r2,
        'orders_mae': orders_mae,
        'revenue_r2': revenue_r2,
        'revenue_mae': revenue_mae,
        'message': f'Forecast generated with Optimized Linear Regression (R²: Orders {orders_r2:.3f}, Revenue {revenue_r2:.3f})'
    }