from django.core.management.base import BaseCommand
from api.tasks import ingest_customer_data, ingest_loan_data

class Command(BaseCommand):
    help = 'Ingest customer and loan data from Excel files into the database via Celery.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting data ingestion...'))

        # Queue the tasks to be executed by the Celery worker
        ingest_customer_data.delay()
        ingest_loan_data.delay()

        self.stdout.write(self.style.SUCCESS('Data ingestion tasks have been queued.'))