import csv
from django.core.management.base import BaseCommand
from ...models import City


class Command(BaseCommand):
    help = 'Import cities from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file to import')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        City.objects.all().delete()
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                city, created = City.objects.update_or_create(
                    country_code=row['Country Code'],
                    city_code=row['City Code'],
                    state_code=row['State Code'],
                    country=row['Country'],
                    airport=row['Airport'],
                    airport_code=row['Airport Code'],
                    city_name=row['City Name'],
                    defaults={
                        'airport_code':row['Airport Code'],
                        'provider': row['Provider'],
                        'active': row['Active'].lower() in ['true', '1', 't', 'yes']
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Successfully created city {city.airport_code}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Successfully updated city {city.airport_code}"))
