from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def update_low_stock():
    """
    Cron job that runs every 12 hours to update low-stock products
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Set up GraphQL client
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            use_json=True,
        )
        
        client = Client(
            transport=transport,
            fetch_schema_from_transport=True
        )
        
        # GraphQL mutation to update low-stock products
        mutation = gql("""
            mutation UpdateLowStockProducts {
                updateLowStockProducts {
                    success
                    message
                    updatedProducts {
                        id
                        name
                        stock
                    }
                }
            }
        """)
        
        # Execute the mutation
        result = client.execute(mutation)
        
        # Extract the mutation result
        mutation_result = result.get('updateLowStockProducts', {})
        
        # Log the results
        with open('/tmp/low_stock_updates_log.txt', 'a') as f:
            f.write(f"[{timestamp}] {mutation_result.get('message', 'No message returned')}\n")
            
            if mutation_result.get('success'):
                updated_products = mutation_result.get('updatedProducts', [])
                f.write(f"[{timestamp}] Updated {len(updated_products)} products:\n")
                
                for product in updated_products:
                    product_name = product.get('name', 'Unknown')
                    new_stock = product.get('stock', 0)
                    f.write(f"[{timestamp}] - {product_name}: New stock level: {new_stock}\n")
            else:
                f.write(f"[{timestamp}] Mutation failed: {mutation_result.get('message', 'Unknown error')}\n")
    
    except Exception as e:
        # Log any errors
        with open('/tmp/low_stock_updates_log.txt', 'a') as f:
            f.write(f"[{timestamp}] Error executing low-stock update: {str(e)}\n")