# ⚡️ EnergyRush – E-Commerce Platform for Energy Drinks

**EnergyRush** is a clean, locally-hosted e-commerce platform built for selling energy drinks with a powerful admin panel. Built on **Flask** with **Bootstrap**, it enables customers to shop as guests and allows administrators to manage inventory and orders, with intelligent forecasting and a powerful chatbot powered by **Hugging Face Transformers**.

---

## ✅ Key Features

### 🛍️ Customer Side (Guest Checkout Only)
- **Landing Page** – Welcoming intro for your brand.
- **About Page** – Tell your story.
- **Product List Page** – Browse energy drinks with images, prices, and stock availability.
- **Cart & Checkout** – No login required, just enter basic details (name, address, phone).
- **Cash on Delivery Only** – Simple and secure.
- **Order Confirmation Page** – Confirms successful order placement.

---

### 🛠️ Admin Panel

#### 1. 📦 Product & Inventory Management
- Add/edit/delete products.
- Update stock quantities.

#### 2. 📑 Order Management
- Track all orders placed by customers.
- Change order status (Pending → Shipped → Delivered/Cancelled).

#### 3. 📊 Intelligent Dashboard
- **Data Visualizations**:
  - Orders over time.
  - Current stock levels.
- **7-Day Forecasts**:
  - Predict next week’s order volume and stock requirements using `scikit-learn`.
- **🧠 NLP Agent (Chatbot)**:
  - Built using **Hugging Face Transformers** (`distilbert`, `bert`, `MiniLM`, etc.).
  - Can answer queries like:
    - “What’s the status of order 104?”
    - “How much stock is left for Ultra Boost?”
  - Queries are parsed locally and matched to your database.
  - Accessed via floating chatbot icon in the bottom-right corner of the admin panel.

---

## 🧰 Tech Stack

| Component       | Technology                           |
|----------------|---------------------------------------|
| Frontend        | HTML5 + Bootstrap 5 (via CDN)         |
| Backend         | Python Flask                          |
| Database        | SQLite (local file-based DB)          |
| ML Forecasting  | `scikit-learn`, `pandas`, `matplotlib`|
| NLP Agent       | Hugging Face `transformers`, `torch`  |
| Visualization   | `matplotlib` or `plotly`              |

> ⚠️ No payment processors, no Docker, no CI/CD — pure local development.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/energyrush-ecommerce.git
cd energyrush-ecommerce
