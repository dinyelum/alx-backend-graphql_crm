import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.exceptions import ValidationError
import re
from decimal import Decimal
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
    customer = graphene.Field(CustomerType)
    products = graphene.List(ProductType)
    
    class Meta:
        model = Order
        fields = "__all__"
    
    def resolve_items(self, info):
        return self.orderitem_set.all()
    
    def resolve_customer(self, info):
        return self.customer
    
    def resolve_products(self, info):
        return self.products.all()

# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class BulkCustomerInput(graphene.InputObjectType):
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

# Response Types with Error Handling
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

# Utility Functions
def validate_phone_number(phone):
    """Validate phone number format"""
    if not phone:
        return True
    phone_pattern = r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$'
    return bool(re.match(phone_pattern, phone))

def validate_email_unique(email):
    """Check if email already exists"""
    return not Customer.objects.filter(email=email).exists()

def get_user_friendly_error(field, value, error_type):
    """Generate user-friendly error messages"""
    error_messages = {
        'email_exists': f"Email '{value}' already exists",
        'invalid_phone': f"Phone number '{value}' must be in format: +1234567890 or 123-456-7890",
        'invalid_price': "Price must be a positive number",
        'invalid_stock': "Stock cannot be negative",
        'customer_not_found': f"Customer with ID '{value}' not found",
        'product_not_found': f"Product with ID '{value}' not found",
        'no_products': "At least one product is required",
        'required_field': f"{field} is required"
    }
    return error_messages.get(error_type, f"Validation error for {field}")

# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    Output = CustomerResponse

    @staticmethod
    def mutate(root, info, input):
        errors = []
        
        # Validate phone format
        if input.phone and not validate_phone_number(input.phone):
            errors.append(get_user_friendly_error('phone', input.phone, 'invalid_phone'))
        
        # Validate unique email
        if not validate_email_unique(input.email):
            errors.append(get_user_friendly_error('email', input.email, 'email_exists'))
        
        # Return errors if any
        if errors:
            return CustomerResponse(
                success=False,
                customer=None,
                message="Customer creation failed",
                errors=errors
            )
        
        try:
            # Create and save customer
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
            # Extract validation errors
            validation_errors = []
            for field, field_errors in e.message_dict.items():
                for error in field_errors:
                    validation_errors.append(f"{field}: {error}")
            
            return CustomerResponse(
                success=False,
                customer=None,
                message="Validation failed",
                errors=validation_errors
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
        inputs = graphene.List(BulkCustomerInput, required=True)

    Output = BulkCustomerResponse

    @staticmethod
    @transaction.atomic
    def mutate(root, info, inputs):
        created_customers = []
        errors = []
        
        for index, input_data in enumerate(inputs):
            try:
                # Validate required fields
                if not input_data.name:
                    errors.append(f"Record {index + 1}: {get_user_friendly_error('name', '', 'required_field')}")
                    continue
                
                if not input_data.email:
                    errors.append(f"Record {index + 1}: {get_user_friendly_error('email', '', 'required_field')}")
                    continue
                
                # Validate phone format
                if input_data.phone and not validate_phone_number(input_data.phone):
                    errors.append(f"Record {index + 1}: {get_user_friendly_error('phone', input_data.phone, 'invalid_phone')}")
                    continue
                
                # Validate unique email
                if not validate_email_unique(input_data.email):
                    errors.append(f"Record {index + 1}: {get_user_friendly_error('email', input_data.email, 'email_exists')}")
                    continue
                
                # Create customer
                customer = Customer(
                    name=input_data.name,
                    email=input_data.email,
                    phone=input_data.phone
                )
                customer.full_clean()
                customer.save()
                created_customers.append(customer)
                
            except ValidationError as e:
                error_msg = f"Record {index + 1}: " + ", ".join([f"{field}: {error}" for field, errors_list in e.message_dict.items() for error in errors_list])
                errors.append(error_msg)
            except Exception as e:
                errors.append(f"Record {index + 1}: {str(e)}")
        
        # Prepare response message
        if created_customers and errors:
            message = f"Successfully created {len(created_customers)} customers, {len(errors)} failed"
            success = True
        elif created_customers:
            message = f"Successfully created {len(created_customers)} customers"
            success = True
        else:
            message = "No customers were created"
            success = False
        
        return BulkCustomerResponse(
            success=success,
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
        errors = []
        
        # Validate price is positive
        if input.price <= Decimal('0'):
            errors.append(get_user_friendly_error('price', input.price, 'invalid_price'))
        
        # Validate stock is not negative
        if input.stock < 0:
            errors.append(get_user_friendly_error('stock', input.stock, 'invalid_stock'))
        
        # Return errors if any
        if errors:
            return ProductResponse(
                success=False,
                product=None,
                message="Product creation failed",
                errors=errors
            )
        
        try:
            # Create and save product
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
            validation_errors = []
            for field, field_errors in e.message_dict.items():
                for error in field_errors:
                    validation_errors.append(f"{field}: {error}")
            
            return ProductResponse(
                success=False,
                product=None,
                message="Validation failed",
                errors=validation_errors
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
        errors = []
        
        # Validate at least one product
        if not input.product_ids:
            errors.append(get_user_friendly_error('products', '', 'no_products'))
            return OrderResponse(
                success=False,
                order=None,
                message="Order creation failed",
                errors=errors
            )
        
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(id=input.customer_id)
            except Customer.DoesNotExist:
                errors.append(get_user_friendly_error('customer', input.customer_id, 'customer_not_found'))
                return OrderResponse(
                    success=False,
                    order=None,
                    message="Order creation failed",
                    errors=errors
                )
            
            # Validate products exist and calculate total
            products = []
            total_amount = Decimal('0')
            
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                    total_amount += product.price
                except Product.DoesNotExist:
                    errors.append(get_user_friendly_error('product', product_id, 'product_not_found'))
                    return OrderResponse(
                        success=False,
                        order=None,
                        message="Order creation failed",
                        errors=errors
                    )
            
            # Create order with accurate total_amount
            order = Order(
                customer=customer,
                total_amount=total_amount
            )
            
            if input.order_date:
                order.order_date = input.order_date
            
            order.full_clean()
            order.save()
            
            # Create order items and associate products
            for product in products:
                order_item = OrderItem(
                    order=order,
                    product=product,
                    quantity=1,
                    price=product.price  # Store price at time of order
                )
                order_item.save()
            
            # Set many-to-many relationship
            order.products.set(products)
            
            return OrderResponse(
                success=True,
                order=order,
                message="Order created successfully",
                errors=None
            )
            
        except ValidationError as e:
            validation_errors = []
            for field, field_errors in e.message_dict.items():
                for error in field_errors:
                    validation_errors.append(f"{field}: {error}")
            
            return OrderResponse(
                success=False,
                order=None,
                message="Validation failed",
                errors=validation_errors
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
    
    # Customer queries
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    
    # Product queries
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    
    # Order queries
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