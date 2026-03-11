from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venues', '0002_remove_complex_address_remove_complex_ciudad_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE venues_complex DROP COLUMN IF EXISTS address;",
                "ALTER TABLE venues_complex DROP COLUMN IF EXISTS ciudad;",
                "ALTER TABLE venues_complex DROP COLUMN IF EXISTS nombre_complejo;",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
