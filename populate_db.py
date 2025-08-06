#!/usr/bin/env python3
import json
import random
from datetime import datetime, timedelta
from app import app, db, Product, Order

def populate_database():
    with app.app_context():
        # Clear existing data
        Order.query.delete()
        Product.query.delete()
        db.session.commit()
        
        # Sample energy drink products
        products_data = [
            {
                'name': 'Thunder Strike Original',
                'description': 'Classic energy blend with caffeine and taurine for instant power',
                'price': 3.99,
                'stock': 120,
                'image_url': 'https://images.unsplash.com/photo-1544804981-33c9e2d9c9b6?w=300&h=300&fit=crop'
            },
            {
                'name': 'Voltage Boost Blue',
                'description': 'Blue raspberry flavor packed with B-vitamins and natural caffeine',
                'price': 4.49,
                'stock': 89,
                'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=300&h=300&fit=crop'
            },
            {
                'name': 'Lightning Fury Red',
                'description': 'Intense red fruit flavor with guarana extract and amino acids',
                'price': 4.29,
                'stock': 67,
                'image_url': 'https://images.unsplash.com/photo-1581636625402-29b2a704ef13?w=300&h=300&fit=crop'
            },
            {
                'name': 'Power Surge Green',
                'description': 'Green apple taste with organic ingredients and zero sugar',
                'price': 4.79,
                'stock': 45,
                'image_url': 'https://images.unsplash.com/photo-1570831739435-6601aa3fa4fb?w=300&h=300&fit=crop'
            },
            {
                'name': 'Energy Rush Premium',
                'description': 'Premium formula with ginseng, L-carnitine, and natural flavors',
                'price': 5.99,
                'stock': 78,
                'image_url': 'https://images.unsplash.com/photo-1591337676887-a217a6970a8a?w=300&h=300&fit=crop'
            },
            {
                'name': 'Adrenaline Max',
                'description': 'Maximum strength energy with 300mg caffeine and electrolytes',
                'price': 6.49,
                'stock': 23,
                'image_url': 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=300&h=300&fit=crop'
            },
            {
                'name': 'Cosmic Energy Purple',
                'description': 'Exotic grape flavor with cosmic berry blend and vitamins',
                'price': 4.99,
                'stock': 91,
                'image_url': 'https://images.unsplash.com/photo-1517312043935-d2c1d6b61ff7?w=300&h=300&fit=crop'
            },
            {
                'name': 'Nitro Blast Yellow',
                'description': 'Citrus explosion with nitric oxide boosters for enhanced performance',
                'price': 5.29,
                'stock': 56,
                'image_url': 'https://images.unsplash.com/photo-1624552184280-104464f8391c?w=300&h=300&fit=crop'
            },
            {
                'name': 'Extreme Focus',
                'description': 'Mental clarity formula with nootropics and sustained energy release',
                'price': 7.99,
                'stock': 34,
                'image_url': 'https://images.unsplash.com/photo-1609501676725-7186f34fa6aa?w=300&h=300&fit=crop'
            },
            {
                'name': 'Beast Mode Black',
                'description': 'Ultimate pre-workout energy with creatine and beta-alanine',
                'price': 8.99,
                'stock': 12,
                'image_url': 'https://images.unsplash.com/photo-1578320308978-a9ca0c46d8eb?w=300&h=300&fit=crop'
            }
        ]
        
        # Insert products
        products = []
        for product_data in products_data:
            product = Product(**product_data)
            db.session.add(product)
            products.append(product)
        
        db.session.commit()
        print(f"Inserted {len(products)} products")
        
        # Generate realistic customer names
        first_names = [
            'Alex', 'Jordan', 'Taylor', 'Casey', 'Morgan', 'Riley', 'Jamie', 'Blake',
            'Avery', 'Quinn', 'Sage', 'River', 'Skylar', 'Cameron', 'Drew', 'Emery',
            'Finley', 'Harper', 'Kendall', 'Logan', 'Peyton', 'Reese', 'Rowan', 'Sydney'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas',
            'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris'
        ]
        
        # Generate orders with patterns
        orders = []
        base_date = datetime.now() - timedelta(days=30)
        
        # Pattern 1: Popular products ordered more frequently
        popular_products = [1, 2, 3, 5, 7]  # IDs of popular products
        
        # Pattern 2: Different order patterns throughout the month
        for i in range(50):
            # Generate order date (spread over last 30 days)
            order_date = base_date + timedelta(days=random.randint(0, 29))
            
            # Generate customer info
            customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            customer_email = f"{customer_name.lower().replace(' ', '.')}@example.com"
            customer_phone = f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            
            # Generate address
            addresses = [
                "123 Main St, New York, NY 10001",
                "456 Oak Ave, Los Angeles, CA 90210",
                "789 Pine Rd, Chicago, IL 60601",
                "321 Elm St, Houston, TX 77001",
                "654 Maple Dr, Phoenix, AZ 85001",
                "987 Cedar Ln, Philadelphia, PA 19101",
                "147 Birch Way, San Antonio, TX 78201",
                "258 Willow St, San Diego, CA 92101",
                "369 Spruce Ave, Dallas, TX 75201",
                "741 Ash Blvd, San Jose, CA 95101"
            ]
            
            # Order items with patterns
            items = []
            total_amount = 0
            
            # 70% chance for 1-2 items, 20% for 3-4 items, 10% for 5+ items
            num_items = random.choices([1, 2, 3, 4, 5, 6], weights=[40, 30, 15, 10, 3, 2])[0]
            
            for _ in range(num_items):
                # Popular products have higher chance of being selected
                if random.random() < 0.6:
                    product_id = random.choice(popular_products)
                else:
                    product_id = random.randint(1, len(products))
                
                product = next(p for p in products if p.id == product_id)
                quantity = random.choices([1, 2, 3, 4], weights=[50, 30, 15, 5])[0]
                
                item = {
                    'product_id': product_id,
                    'name': product.name,
                    'price': float(product.price),
                    'quantity': quantity
                }
                items.append(item)
                total_amount += product.price * quantity
            
            # Order status patterns (most orders are delivered/shipped)
            status = random.choices(
                ['Pending', 'Shipped', 'Delivered', 'Cancelled'],
                weights=[15, 25, 55, 5]
            )[0]
            
            order = Order(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_address=random.choice(addresses),
                items=json.dumps(items),
                total_amount=total_amount,
                status=status,
                created_at=order_date
            )
            
            db.session.add(order)
            orders.append(order)
        
        db.session.commit()
        print(f"Inserted {len(orders)} orders")
        
        # Print summary
        print("\n=== DATABASE POPULATION COMPLETE ===")
        print(f"Total Products: {len(products)}")
        print(f"Total Orders: {len(orders)}")
        print(f"Total Revenue: ${sum(order.total_amount for order in orders):.2f}")
        print(f"Pending Orders: {len([o for o in orders if o.status == 'Pending'])}")
        print(f"Low Stock Products: {len([p for p in products if p.stock <= 20])}")

if __name__ == '__main__':
    populate_database()