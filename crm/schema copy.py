import graphene
from graphene_django import DjangoObjectType, DjangoFilterConnectionField
from django.db import transaction
from django.core.exceptions import ValidationError
import re
from decimal import Decimal
from .models import Customer, Product, Order, OrderItem
from .filters import CustomerFilter, ProductFilter, OrderFilter

# Node Types with Relay
class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        fields = "__all__"
        filterset_class = CustomerFilter

class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        fields = "__all__"
        filterset_class = ProductFilter

class OrderItemNode(DjangoObjectType):
    class Meta:
        model = OrderItem
        interfaces = (graphene.relay.Node,)
        fields = "__all__"

class OrderNode(DjangoObjectType):
    items = graphene.List(OrderItemNode)
    customer = graphene.Field(CustomerNode)
    products = graphene.List(ProductNode)
    
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        fields = "__all__"
        filterset_class = OrderFilter
    
    def resolve_items(self, info):
        return self.orderitem_set.all()
    
    def resolve_customer(self, info):
        return self.customer
    
    def resolve_products(self, info):
        return self.products.all()

# Input Types for Filtering
class CustomerFilterInput(graphene.InputObjectType):
    name = graphene.String()
    email = graphene.String()
    created_at_gte = graphene.Date()
    created_at_lte = graphene.Date()
    phone_pattern = graphene.String()

class ProductFilterInput(graphene.InputObjectType):
    name = graphene.String()
    price_gte = graphene.Decimal()
    price_lte = graphene.Decimal()
    stock_gte = graphene.Int()
    stock_lte = graphene.Int()
    low_stock = graphene.Boolean()

class OrderFilterInput(graphene.InputObjectType):
    total_amount_gte = graphene.Decimal()
    total_amount_lte = graphene.Decimal()
    order_date_gte = graphene.Date()
    order_date_lte = graphene.Date()
    customer_name = graphene.String()
    product_name = graphene.String()
    product_id = graphene.ID()

# Order By Enum
class OrderByEnum(graphene.Enum):
    NAME_ASC = 'name'
    NAME_DESC = '-name'
    EMAIL_ASC = 'email'
    EMAIL_DESC = '-email'
    CREATED_AT_ASC = 'created_at'
    CREATED_AT_DESC = '-created_at'
    PRICE_ASC = 'price'
    PRICE_DESC = '-price'
    STOCK_ASC = 'stock'
    STOCK_DESC = '-stock'
    TOTAL_AMOUNT_ASC = 'total_amount'
    TOTAL_AMOUNT_DESC = '-total_amount'
    ORDER_DATE_ASC = 'order_date'
    ORDER_DATE_DESC = '-order_date'

# Existing Input Types (keep from previous implementation)
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

# Response Types (keep from previous implementation)
class CustomerResponse(graphene.ObjectType):
    success = graphene.Boolean()
    customer = graphene.Field(CustomerNode)
    message = graphene.String()
    errors = graphene.List(graphene.String)

class BulkCustomerResponse(graphene.ObjectType):
    success = graphene.Boolean()
    customers = graphene.List(CustomerNode)
    errors = graphene.List(graphene.String)
    message = graphene.String()

class ProductResponse(graphene.ObjectType):
    success = graphene.Boolean()
    product = graphene.Field(ProductNode)
    message = graphene.String()
    errors = graphene.List(graphene.String)

class OrderResponse(graphene.ObjectType):
    success = graphene.Boolean()
    order = graphene.Field(OrderNode)
    message = graphene.String()
    errors = graphene.List(graphene.String)

# Utility Functions (keep from previous implementation)
def validate_phone_number(phone):
    if not phone:
        return True
    phone_pattern = r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$'
    return bool(re.match(phone_pattern, phone))

def validate_email_unique(email):
    return not Customer.objects.filter(email=email).exists()

def get_user_friendly_error(field, value, error_type):
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

# Mutations (keep from previous implementation - shortened for brevity)
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    Output = CustomerResponse

    @staticmethod
    def mutate(root, info, input):
        errors = []
        
        if input.phone and not validate_phone_number(input.phone):
            errors.append(get_user_friendly_error('phone', input.phone, 'invalid_phone'))
        
        if not validate_email_unique(input.email):
            errors.append(get_user_friendly_error('email', input.email, 'email_exists'))
        
        if errors:
            return CustomerResponse(
                success=False,
                customer=None,
                message="Customer creation failed",
                errors=errors
            )
        
        try:
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
                if not input_data.name:
                    errors.append(f"Record {index + 1}: {get_user_friendly_error('name', '', 'required_field')}")
                    continue
                
                if not input_data.email:
                    errors.append(f"Record {index + 1}: {get_user_friendly_error('email', '', 'required_field')}")
                    continue
                
                if input_data.phone and not validate_phone_number(input_data.phone):
                    errors.append(f"Record {index + 1}: {get_user_friendly_error('phone', input_data.phone, 'invalid_phone')}")
                    continue
                
                if not validate_email_unique(input_data.email):
                    errors.append(f"Record {index + 1}: {get_user_friendly_error('email', input_data.email, 'email_exists')}")
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
                error_msg = f"Record {index + 1}: " + ", ".join([f"{field}: {error}" for field, errors_list in e.message_dict.items() for error in errors_list])
                errors.append(error_msg)
            except Exception as e:
                errors.append(f"Record {index + 1}: {str(e)}")
        
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
        
        if input.price <= Decimal('0'):
            errors.append(get_user_friendly_error('price', input.price, 'invalid_price'))
        
        if input.stock < 0:
            errors.append(get_user_friendly_error('stock', input.stock, 'invalid_stock'))
        
        if errors:
            return ProductResponse(
                success=False,
                product=None,
                message="Product creation failed",
                errors=errors
            )
        
        try:
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
        
        if not input.product_ids:
            errors.append(get_user_friendly_error('products', '', 'no_products'))
            return OrderResponse(
                success=False,
                order=None,
                message="Order creation failed",
                errors=errors
            )
        
        try:
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
            
            order = Order(
                customer=customer,
                total_amount=total_amount
            )
            
            if input.order_date:
                order.order_date = input.order_date
            
            order.full_clean()
            order.save()
            
            for product in products:
                order_item = OrderItem(
                    order=order,
                    product=product,
                    quantity=1,
                    price=product.price
                )
                order_item.save()
            
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

# Updated Query Class with Filtering
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    
    # Filtered queries with DjangoFilterConnectionField
    all_customers = DjangoFilterConnectionField(
        CustomerNode,
        filterset_class=CustomerFilter,
        filter=CustomerFilterInput(),
        order_by=graphene.List(OrderByEnum)
    )
    
    all_products = DjangoFilterConnectionField(
        ProductNode,
        filterset_class=ProductFilter,
        filter=ProductFilterInput(),
        order_by=graphene.List(OrderByEnum)
    )
    
    all_orders = DjangoFilterConnectionField(
        OrderNode,
        filterset_class=OrderFilter,
        filter=OrderFilterInput(),
        order_by=graphene.List(OrderByEnum)
    )
    
    # Single object queries
    customer = graphene.relay.Node.Field(CustomerNode)
    product = graphene.relay.Node.Field(ProductNode)
    order = graphene.relay.Node.Field(OrderNode)
    
    # Resolve methods for filtered queries
    def resolve_all_customers(self, info, **kwargs):
        queryset = Customer.objects.all()
        order_by = kwargs.get('order_by')
        if order_by:
            queryset = queryset.order_by(*order_by)
        return queryset
    
    def resolve_all_products(self, info, **kwargs):
        queryset = Product.objects.all()
        order_by = kwargs.get('order_by')
        if order_by:
            queryset = queryset.order_by(*order_by)
        return queryset
    
    def resolve_all_orders(self, info, **kwargs):
        queryset = Order.objects.all()
        order_by = kwargs.get('order_by')
        if order_by:
            queryset = queryset.order_by(*order_by)
        return queryset

# Mutation Class
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()