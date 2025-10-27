#!/usr/bin/env python3
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, timedelta
import os

# GraphQL endpoint
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"

# Calculate date 7 days ago
one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# GraphQL query to get pending orders from the last 7 days
QUERY = gql("""
query GetPendingOrders($sinceDate: String!) {
  pendingOrders(sinceDate: $sinceDate) {
    id
    orderDate
    customer {
      email
    }
    status
  }
}
""")

# Alternative query if the above doesn't match your schema
ALTERNATIVE_QUERY = gql("""
query GetRecentOrders($sinceDate: String!) {
  orders(where: {orderDate_gte: $sinceDate, status: "pending"}) {
    id
    orderDate
    customer {
      email
    }
    status
  }
}
""")

def send_order_reminders():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Set up GraphQL client
        transport = RequestsHTTPTransport(
            url=GRAPHQL_ENDPOINT,
            use_json=True,
        )
        
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Execute the query
        variables = {"sinceDate": one_week_ago}
        result = client.execute(QUERY, variable_values=variables)
        
        # Extract orders from response
        orders = result.get('pendingOrders', [])
        
        # If no orders found with first query, try alternative
        if not orders:
            result = client.execute(ALTERNATIVE_QUERY, variable_values=variables)
            orders = result.get('orders', [])
        
        # Log each order
        with open('/tmp/order_reminders_log.txt', 'a') as f:
            f.write(f"[{timestamp}] Processing {len(orders)} pending orders\n")
            
            for order in orders:
                order_id = order.get('id', 'N/A')
                customer_email = order.get('customer', {}).get('email', 'N/A')
                order_date = order.get('orderDate', 'N/A')
                
                f.write(f"[{timestamp}] Order ID: {order_id}, Customer Email: {customer_email}, Order Date: {order_date}\n")
        
        print("Order reminders processed!")
        
    except Exception as e:
        # Log any errors
        with open('/tmp/order_reminders_log.txt', 'a') as f:
            f.write(f"[{timestamp}] Error: {str(e)}\n")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    send_order_reminders()