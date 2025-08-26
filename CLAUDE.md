# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EnergyRush** is a Flask-based e-commerce platform for selling energy drinks with advanced AI features including ML forecasting, NLP chatbot, and MCP database integration.

## Development Commands

### Setup and Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (if needed)
python populate_db.py  # Seeds sample products
python populate_dummy_orders.py  # Adds sample orders for forecasting

# Run the application
python app.py
```

### Development Server
- **Local server**: `python app.py` (runs on http://localhost:5000)
- **Debug mode**: Already enabled in app.py for development
- **Database**: SQLite (energyrush.db) - automatically created on first run
- **Timezone**: Asia/Colombo (UTC+05:30) configured throughout

## Architecture Overview

### Backend Components
- **Framework**: Flask with SQLAlchemy ORM
- **Database Models**:
  - `Product`: Energy drink products with stock management
  - `Order`: Customer orders with JSON items storage
  - `AdkChatHistory`: Stores AI chatbot interactions
  - `AdkMemory`: Contextual memory for chatbot sessions
- **AI/ML Integration**:
  - **Forecasting**: scikit-learn (LinearRegression) + statsmodels (ETS, Exponential Smoothing)
  - **Chatbot Systems**:
    - Enhanced Chatbot with MCP integration (`enhanced_chatbot.py`)
    - Gemini API integration for conversational AI (`gemini_integration.py`)
    - ADK Bridge for intelligent query processing (`gemini_adk_bridge.py`)
  - **NLP**: Hugging Face transformers (DistilBERT for Q&A)

### Frontend Structure
- **Templates**: Jinja2 templates with Bootstrap 5
- **Customer Pages**: Landing, About, Products, Cart, Checkout (guest-only)
- **Admin Panel** (`/admin`):
  - Dashboard with visualizations
  - Product CRUD operations
  - Order management with status updates
  - ML-powered 7-day sales forecasting
  - Integrated AI chatbot (bottom-right corner)

### Key Features
1. **Customer Experience**:
   - Guest checkout only (no user registration)
   - Shopping cart with session storage
   - Cash on delivery payment
   - Real-time stock checking

2. **Admin Intelligence**:
   - ML forecasting with multiple models (Linear Regression, ETS, Exponential Smoothing)
   - Multi-model chatbot system (MCP + Gemini + ADK Bridge)
   - Data visualization with matplotlib
   - Timezone-aware operations (Asia/Colombo)

3. **Database Operations**:
   - MCP database server support (`mcp_database_server.py`)
   - Automated data generation (`data_generator.py`)
   - Order verification utilities (`verify_orders.py`)

## Testing Commands

```bash
# Test chatbot systems
python test_enhanced_chatbot.py
python test_hybrid_chatbot.py
python test_final_system.py
python test_complete_system.py

# Test forecasting models
python test_theta_performance.py
python debug_theta_model.py

# Test order management
python test_orders_management.py
```

## Key Routes
- **Customer**: `/`, `/about`, `/products`, `/cart`, `/checkout`, `/order-confirmation`
- **Admin**: `/admin`, `/admin/products`, `/admin/orders`, `/admin/forecasting`
- **API Endpoints**:
  - `/admin/chatbot` (POST) - AI assistant
  - `/add_to_cart` (POST) - Cart management
  - `/update_cart` (POST) - Update quantities
  - `/remove_from_cart` (POST) - Remove items

## Environment Variables
Create a `.env` file with:
```
GEMINI_API_KEY=your_api_key_here
```

## Database Schema
- Products table: id, name, description, price, stock, image_url, created_at
- Orders table: id, customer_name, customer_phone, customer_address, total_amount, status, created_at, items (JSON)
- AdkChatHistory: Tracks AI interactions with confirmation/execution states
- AdkMemory: Maintains contextual memory across chat sessions

## Production Considerations
- Change `app.config['SECRET_KEY']` for production
- Set `debug=False` in production
- Consider PostgreSQL for production database
- Implement admin authentication (currently no auth for local development)
- Configure proper logging and error handling