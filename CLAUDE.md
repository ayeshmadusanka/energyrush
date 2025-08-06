# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EnergyRush** is a complete Flask-based e-commerce platform for selling energy drinks with advanced AI features including ML forecasting and NLP chatbot capabilities.

## Development Commands

### Setup and Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Development Server
- **Local server**: `python app.py` (runs on http://localhost:5000)
- **Debug mode**: Already enabled in app.py for development
- **Database**: SQLite (energyrush.db) - automatically created on first run

## Architecture Overview

### Backend Structure
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite with two main models:
  - `Product`: Energy drink products with stock management
  - `Order`: Customer orders with JSON items storage
- **AI Features**:
  - ML forecasting using scikit-learn Linear Regression
  - NLP chatbot using Hugging Face transformers (DistilBERT)

### Frontend Structure
- **Templates**: Jinja2 templates with Bootstrap 5
- **Customer Pages**: Landing, About, Products, Cart, Checkout, Order Confirmation
- **Admin Panel**: Dashboard, Products Management, Orders Management, Forecasting
- **Styling**: Bootstrap 5 CDN + custom CSS for energy drink branding

### Key Features
1. **Customer Experience**:
   - Guest checkout only (no user registration required)
   - Shopping cart with session storage
   - Cash on delivery payment method
   - Real-time stock checking

2. **Admin Panel**:
   - Product CRUD operations with image support
   - Order management with status updates
   - ML-powered 7-day sales forecasting
   - AI chatbot for business queries (bottom-right corner)

3. **AI/ML Components**:
   - **Forecasting**: Uses pandas + scikit-learn for sales predictions
   - **Chatbot**: Hugging Face transformers for natural language queries
   - **Data Visualization**: matplotlib for forecast charts

### File Structure
```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   ├── base.html         # Customer site base template
│   ├── index.html        # Landing page
│   ├── about.html        # About page
│   ├── products.html     # Product listing
│   ├── cart.html         # Shopping cart
│   ├── checkout.html     # Checkout form
│   ├── order_confirmation.html
│   └── admin/
│       ├── base.html     # Admin panel base template
│       ├── dashboard.html # Admin dashboard
│       ├── products.html # Product management
│       ├── add_product.html
│       ├── edit_product.html
│       ├── orders.html   # Order management
│       └── forecasting.html # ML forecasting
└── static/
    ├── css/              # Custom stylesheets
    ├── js/               # Custom JavaScript
    └── charts/           # Generated forecast charts
```

## Development Notes

### Database
- SQLite database is created automatically on first run
- Sample products are seeded if database is empty
- No migrations needed - SQLAlchemy handles schema creation

### AI Features Setup
- Hugging Face models download automatically on first use
- Forecasting requires minimum 7 orders for meaningful predictions
- Charts are generated in `static/charts/` directory

### Admin Access
- Access admin panel at `/admin`
- No authentication implemented (local development focus)
- Chatbot available via floating button in admin panel

### Key Routes
- **Customer**: `/`, `/about`, `/products`, `/cart`, `/checkout`
- **Admin**: `/admin`, `/admin/products`, `/admin/orders`, `/admin/forecasting`
- **API**: `/admin/chatbot` (POST - for AI assistant)

### Customization Guidelines
- Product images: Use 300x300px for best display
- Brand colors: Primary (purple gradient), Success (green), Warning (amber)
- Modify sample products in `app.py` if needed
- Admin panel expandable via `templates/admin/base.html`

## Production Deployment Notes

- Change `app.config['SECRET_KEY']` for production
- Consider PostgreSQL for production database
- Set `debug=False` in production
- Configure proper logging and error handling
- Implement admin authentication for production use