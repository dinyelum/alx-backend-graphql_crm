import graphene
from graphene_django import DjangoObjectType
from .models import Product  # Replace 'your_app' with your actual app name

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "stock", "price")

class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        pass  # No arguments needed for this mutation

    success = graphene.Boolean()
    message = graphene.String()
    updated_products = graphene.List(ProductType)

    def mutate(self, info):
        try:
            # Query products with stock less than 10
            low_stock_products = Product.objects.filter(stock__lt=10)
            
            # Update stock for each low-stock product
            updated_products = []
            for product in low_stock_products:
                product.stock += 10  # Increment stock by 10
                product.save()
                updated_products.append(product)
            
            return UpdateLowStockProducts(
                success=True,
                message=f"Successfully updated {len(updated_products)} low-stock products",
                updated_products=updated_products
            )
            
        except Exception as e:
            return UpdateLowStockProducts(
                success=False,
                message=f"Error updating low-stock products: {str(e)}",
                updated_products=[]
            )

class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()

# Add this to your existing schema class or create one
class Query(graphene.ObjectType):
    # Add your existing queries here
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)