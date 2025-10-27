#!/usr/bin/env python3
import requests
from datetime import datetime, timedelta
import json
import os

# GraphQL endpoint
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"

# Calculate date 7 days ago
one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# GraphQL query to get pending orders from the last 7 days
GRAPHQL_QUERY = """
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
"""

# Alternative query if the above doesn't match your schema - adjust as needed
ALTERNATIVE_QUERY = """
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
"""

def send_order_reminders():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Prepare the GraphQL request
        variables = {
            "sinceDate": one_week_ago
        }
        
        payload = {
            "query": GRAPHQL_QUERY,
            "variables": variables
        }
        
        # Make the GraphQL request
        response = requests.post(
            GRAPHQL_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Log the response for debugging (optional)
            with open('/tmp/order_reminders_log.txt', 'a') as f:
                f.write(f"[{timestamp}] GraphQL Response: {json.dumps(data, indent=2)}\n")
            
            # Check for errors in GraphQL response
            if 'errors' in data:
                with open('/tmp/order_reminders_log.txt', 'a') as f:
                    f.write(f"[{timestamp}] GraphQL Errors: {data['errors']}\n")
                print("GraphQL query errors occurred. Check log for details.")
                return
            
            # Extract orders from response - adjust the path based on your schema
            orders = data.get('data', {}).get('pendingOrders', [])
            
            if not orders:
                # Try alternative query path
                orders = data.get('data', {}).get('orders', [])
            
            # Log each order
            with open('/tmp/order_reminders_log.txt', 'a') as f:
                f.write(f"[{timestamp}] Processing {len(orders)} pending orders\n")
                
                for order in orders:
                    order_id = order.get('id', 'N/A')
                    customer_email = order.get('customer', {}).get('email', 'N/A')
                    order_date = order.get('orderDate', 'N/A')
                    
                    f.write(f"[{timestamp}] Order ID: {order_id}, Customer Email: {customer_email}, Order Date: {order_date}\n")
            
            print("Order reminders processed!")
            
        else:
            # Log HTTP error
            with open('/tmp/order_reminders_log.txt', 'a') as f:
                f.write(f"[{timestamp}] HTTP Error: {response.status_code} - {response.text}\n")
            print(f"HTTP Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        with open('/tmp/order_reminders_log.txt', 'a') as f:
            f.write(f"[{timestamp}] Error: Could not connect to GraphQL endpoint at {GRAPHQL_ENDPOINT}\n")
        print("Connection error: Could not reach GraphQL endpoint")
        
    except requests.exceptions.Timeout:
        with open('/tmp/order_reminders_log.txt', 'a') as f:
            f.write(f"[{timestamp}] Error: Request timeout\n")
        print("Request timeout")
        
    except Exception as e:
        with open('/tmp/order_reminders_log.txt', 'a') as f:
            f.write(f"[{timestamp}] Unexpected error: {str(e)}\n")
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    send_order_reminders()