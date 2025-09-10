from celery.schedules import crontab
# from users.tasks import remove_expired_task
CELERY_BEAT_SCHEDULE = {
    'remove-expiredcode-every-10m':{
        'task': 'users.tasks.remove_expired_task',
        'schedule':crontab(minute='*/10'),
        'options':{'queue':'expired'},
    },
}