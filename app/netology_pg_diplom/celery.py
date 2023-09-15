import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "netology_pg_diplom.settings")
app = Celery("netology_pg_diplom")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()