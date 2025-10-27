from datetime import datetime
import os
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def log_crm_heartbeat():
    """
    CRM heartbeat cron job that logs every 5 minutes
    Optionally verifies GraphQL endpoint is responsive
    """
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    log_message = f"{timestamp} CRM is alive"
    
    try:
        # Log the heartbeat message
        with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
            f.write(log_message + '\n')
        
        # Optional: Verify GraphQL endpoint is responsive
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
            
            # Simple query to verify GraphQL endpoint
            query = gql("""
                query {
                    hello
                }
            """)
            
            # Execute the query
            result = client.execute(query)
            
            # Log successful GraphQL connection
            with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
                f.write(f"{timestamp} GraphQL endpoint verified: {result}\n")
                
        except Exception as graphql_error:
            # Log GraphQL connection error but don't fail the entire job
            with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
                f.write(f"{timestamp} GraphQL check failed: {str(graphql_error)}\n")
    
    except Exception as e:
        # Fallback log if file writing fails
        print(f"Error in heartbeat cron job: {str(e)}")

# Alternative simpler version without GraphQL check (if preferred):
def log_crm_heartbeat_simple():
    """
    Simple CRM heartbeat without GraphQL verification
    """
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    try:
        with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
            f.write(f"{timestamp} CRM is alive\n")
    except Exception as e:
        print(f"Error writing heartbeat log: {str(e)}")