from django.db import migrations
import uuid


def generate_tokens(apps, schema_editor):
    QuoteRequest = apps.get_model('quote_requests', 'QuoteRequest')
    for quote in QuoteRequest.objects.all():
        if not quote.response_token:
            quote.response_token = uuid.uuid4()
            quote.save()


class Migration(migrations.Migration):

    dependencies = [
        ('quote_requests', '0007_quoterequest_response_token'),
    ]

    operations = [
        migrations.RunPython(generate_tokens, migrations.RunPython.noop),
    ]
