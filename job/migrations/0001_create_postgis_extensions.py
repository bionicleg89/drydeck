from django.db import migrations
from django.contrib.postgres.operations import CreateExtension


class Migration(migrations.Migration):

    dependencies = [
        
    ]

    operations = [
        CreateExtension("postgis"),
        CreateExtension("fuzzystrmatch"),
        CreateExtension("postgis_tiger_geocoder"),
        CreateExtension("address_standardizer"),
    ]
