#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Execute the Django command to delete inactive customers and capture output
DELETION_RESULT=$(python manage.py shell -c "
from django.utils import timezone
from datetime import timedelta
from your_app.models import Customer, Order  # Replace 'your_app' with your actual app name

# Calculate date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders in the last year
inactive_customers = Customer.objects.filter(
    order__isnull=True
).distinct() | Customer.objects.filter(
    order__created_at__lt=one_year_ago
).exclude(
    order__created_at__gte=one_year_ago
).distinct()

# Count before deletion
count_before = inactive_customers.count()

# Delete the inactive customers
inactive_customers.delete()

print(f'{count_before}')
" 2>/dev/null)

# Log the result
if [ -n "$DELETION_RESULT" ]; then
    echo "[$TIMESTAMP] Deleted $DELETION_RESULT inactive customers" >> /tmp/customer_cleanup_log.txt
else
    echo "[$TIMESTAMP] Error: Failed to execute cleanup script" >> /tmp/customer_cleanup_log.txt
fi