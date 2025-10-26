import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.exceptions import ValidationError
import re
from .models import Customer, Product, Order, OrderItem

# Node Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"

class OrderItemType(DjangoObjectType):
    class Meta:
        model = OrderItem
        fields = "__all__"

class OrderType(DjangoObjectType):
    items = graphene.List(OrderItemType)
    
    class Meta:
        model = Order
        fields = "__all__"
    
    def resolve_items(self, info):
        return self.orderitem_set.all()

# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(default_value=0)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

# Response Types
class CustomerResponse(graphene.ObjectType):
    success = graphene.Boolean()
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

class BulkCustomerResponse(graphene.ObjectType):
    success = graphene.Boolean()
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    message = graphene.String()

class ProductResponse(graphene.ObjectType):
    success = graphene.Boolean()
    product = graphene.Field(ProductType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

class OrderResponse(graphene.ObjectType):
    success = graphene.Boolean()
    order = graphene.Field(OrderType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    Output = CustomerResponse

    @staticmethod
    def mutate(root, info, input):
        try:
            # Validate phone format if provided
            if input.phone:
                phone_pattern = r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$'
                if not re.match(phone_pattern, input.phone):
                    return CustomerResponse(
                        success=False,
                        customer=None,
                        message="Validation failed",
                        errors=["Phone number must be in format: +1234567890 or 123-456-7890"]
                    )
            
            # Check for unique email
            if Customer.objects.filter(email=input.email).exists():
                return CustomerResponse(
                    success=False,
                    customer=None,
                    message="Validation failed",
                    errors=["Email already exists"]
                )
            
            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.phone
            )
            customer.full_clean()
            customer.save()
            
            return CustomerResponse(
                success=True,
                customer=customer,
                message="Customer created successfully",
                errors=None
            )
            
        except ValidationError as e:
            return CustomerResponse(
                success=False,
                customer=None,
                message="Validation failed",
                errors=list(e.message_dict.values())
            )
        except Exception as e:
            return CustomerResponse(
                success=False,
                customer=None,
                message="Failed to create customer",
                errors=[str(e)]
            )

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)

    Output = BulkCustomerResponse

    @staticmethod
    @transaction.atomic
    def mutate(root, info, inputs):
        created_customers = []
        errors = []
        
        for index, input_data in enumerate(inputs):
            try:
                # Validate phone format if provided
                if input_data.phone:
                    phone_pattern = r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$'
                    if not re.match(phone_pattern, input_data.phone):
                        errors.append(f"Record {index + 1}: Invalid phone format")
                        continue
                
                # Check for unique email
                if Customer.objects.filter(email=input_data.email).exists():
                    errors.append(f"Record {index + 1}: Email already exists")
                    continue
                
                customer = Customer(
                    name=input_data.name,
                    email=input_data.email,
                    phone=input_data.phone
                )
                customer.full_clean()
                customer.save()
                created_customers.append(customer)
                
            except ValidationError as e:
                error_msg = f"Record {index + 1}: " + ", ".join(list(e.message_dict.values()))
                errors.append(error_msg)
            except Exception as e:
                errors.append(f"Record {index + 1}: {str(e)}")
        
        message = f"Created {len(created_customers)} customers successfully"
        if errors:
            message += f", {len(errors)} failed"
        
        return BulkCustomerResponse(
            success=len(created_customers) > 0,
            customers=created_customers,
            errors=errors if errors else None,
            message=message
        )

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    Output = ProductResponse

    @staticmethod
    def mutate(root, info, input):
        try:
            # Validate price is positive
            if input.price <= 0:
                return ProductResponse(
                    success=False,
                    product=None,
                    message="Validation failed",
                    errors=["Price must be positive"]
                )
            
            # Validate stock is not negative
            if input.stock < 0:
                return ProductResponse(
                    success=False,
                    product=None,
                    message="Validation failed",
                    errors=["Stock cannot be negative"]
                )
            
            product = Product(
                name=input.name,
                price=input.price,
                stock=input.stock
            )
            product.full_clean()
            product.save()
            
            return ProductResponse(
                success=True,
                product=product,
                message="Product created successfully",
                errors=None
            )
            
        except ValidationError as e:
            return ProductResponse(
                success=False,
                product=None,
                message="Validation failed",
                errors=list(e.message_dict.values())
            )
        except Exception as e:
            return ProductResponse(
                success=False,
                product=None,
                message="Failed to create product",
                errors=[str(e)]
            )

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    Output = OrderResponse

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(id=input.customer_id)
            except Customer.DoesNotExist:
                return OrderResponse(
                    success=False,
                    order=None,
                    message="Validation failed",
                    errors=["Customer not found"]
                )
            
            # Validate at least one product
            if not input.product_ids:
                return OrderResponse(
                    success=False,
                    order=None,
                    message="Validation failed",
                    errors=["At least one product is required"]
                )
            
            # Validate products exist and get their prices
            products = []
            total_amount = 0
            
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                    total_amount += product.price
                except Product.DoesNotExist:
                    return OrderResponse(
                        success=False,
                        order=None,
                        message="Validation failed",
                        errors=[f"Product with ID {product_id} not found"]
                    )
            
            # Create order
            order = Order(
                customer=customer,
                total_amount=total_amount
            )
            if input.order_date:
                order.order_date = input.order_date
            
            order.full_clean()
            order.save()
            
            # Create order items
            for product in products:
                order_item = OrderItem(
                    order=order,
                    product=product,
                    quantity=1,
                    price=product.price
                )
                order_item.save()
            
            # Add products to order (many-to-many)
            order.products.set(products)
            
            return OrderResponse(
                success=True,
                order=order,
                message="Order created successfully",
                errors=None
            )
            
        except ValidationError as e:
            return OrderResponse(
                success=False,
                order=None,
                message="Validation failed",
                errors=list(e.message_dict.values())
            )
        except Exception as e:
            return OrderResponse(
                success=False,
                order=None,
                message="Failed to create order",
                errors=[str(e)]
            )

# Query Class
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    
    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    
    def resolve_customers(self, info):
        return Customer.objects.all()
    
    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None
    
    def resolve_products(self, info):
        return Product.objects.all()
    
    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_orders(self, info):
        return Order.objects.all()
    
    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None

# Mutation Class
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()