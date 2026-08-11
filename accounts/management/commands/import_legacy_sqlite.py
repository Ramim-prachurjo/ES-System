from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


APP_LABELS = ('accounts', 'teams', 'venues', 'tournaments', 'notifications')
SKIP_MODELS = {('accounts', 'platformbranding')}


class Command(BaseCommand):
    help = 'Copies existing application data from db.sqlite3 into PostgreSQL.'

    def handle(self, *args, **options):
        models = [
            model for app_label in APP_LABELS
            for model in apps.get_app_config(app_label).get_models()
            if (model._meta.app_label, model._meta.model_name) not in SKIP_MODELS
        ]
        populated = [model._meta.label for model in models if model.objects.using('default').exists()]
        if populated:
            raise CommandError('PostgreSQL already contains application data. Import cancelled: ' + ', '.join(populated))

        ordered, pending = [], list(models)
        while pending:
            progressed = False
            for model in pending[:]:
                dependencies = {
                    field.remote_field.model for field in model._meta.fields
                    if field.is_relation and field.remote_field and field.remote_field.model in pending
                    and field.remote_field.model is not model
                }
                if not dependencies:
                    ordered.append(model)
                    pending.remove(model)
                    progressed = True
            if not progressed:
                raise CommandError('Could not determine a safe import order for legacy data.')

        totals = {}
        with transaction.atomic(using='default'):
            for model in ordered:
                records = list(model.objects.using('legacy_sqlite').all().iterator())
                if records:
                    copies = []
                    for record in records:
                        copied = model()
                        for field in model._meta.concrete_fields:
                            setattr(copied, field.attname, getattr(record, field.attname))
                        copies.append(copied)
                    model.objects.using('default').bulk_create(copies, batch_size=500)
                totals[model._meta.label] = len(records)

        self.stdout.write(self.style.SUCCESS('Legacy SQLite data imported into PostgreSQL.'))
        for label, count in totals.items():
            self.stdout.write(f'  {label}: {count}')
