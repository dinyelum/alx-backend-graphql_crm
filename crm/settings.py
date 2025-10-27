# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... your existing apps ...
    'django_crontab',
]

# Add CRONJOBS configuration
CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),  # Your existing heartbeat job
    ('0 */12 * * *', 'crm.cron.update_low_stock'),  # New low-stock update job
]

# Optional: Specify where to store cron job logs
CRONTAB_COMMAND_SUFFIX = '2>&1'