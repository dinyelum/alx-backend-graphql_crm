# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... your existing apps ...
    'django_crontab',
]

# Add CRONJOBS configuration
CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
]

# Optional: Specify where to store cron job logs
CRONTAB_COMMAND_SUFFIX = '2>&1'