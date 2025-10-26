import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order, OrderItem

def seed_database():
    print("Seeding database...")
    
    # Clear existing data
    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    Product.objects.all().delete()
    Customer.objects.all().delete()
    
    # Create customers
    customers = [
        Customer(name="John Doe", email="john@example.com", phone="+1234567890"),
        Customer(name="Jane Smith", email="jane@example.com", phone="123-456-7890"),
        Customer(name="Bob Johnson", email="bob@example.com", phone="+447912345678"),
    ]
    
    for customer in customers:
        customer.save()
    
    print(f"Created {len(customers)} customers")
    
    # Create products
    products = [
        Product(name="Laptop", price=Decimal("999.99"), stock=10),
        Product(name="Mouse", price=Decimal("29.99"), stock=50),
        Product(name="Keyboard", price=Decimal("79.99"), stock=30),
        Product(name="Monitor", price=Decimal("299.99"), stock=15),
    ]
    
    for product in products:
        product.save()
    
    print(f"Created {len(products)} products")
    
    # Create orders
    customer1 = Customer.objects.get(email="john@example.com")
    customer2 = Customer.objects.get(email="jane@example.com")
    
    product1 = Product.objects.get(name="Laptop")
    product2 = Product.objects.get(name="Mouse")
    product3 = Product.objects.get(name="Keyboard")
    
    # Order 1
    order1 = Order(customer=customer1, total_amount=product1.price + product2.price)
    order1.save()
    order1.products.add(product1, product2)
    
    OrderItem.objects.create(order=order1, product=product1, quantity=1, price=product1.price)
    OrderItem.objects.create(order=order1, product=product2, quantity=1, price=product2.price)
    
    # Order 2
    order2 = Order(customer=customer2, total_amount=product3.price)
    order2.save()
    order2.products.add(product3)
    
    OrderItem.objects.create(order=order2, product=product3, quantity=1, price=product3.price)
    
    print("Created sample orders")
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()