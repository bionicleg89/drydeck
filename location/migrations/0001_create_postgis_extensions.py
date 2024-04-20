from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        
    ]

    operations = [
        CreateExtension("postgis"),
        CreateExtension("fuzzystrmatch"),
        CreateExtension("postgis_tiger_geocoder"),
        CreateExtension("address_standardizer"),
    ]
