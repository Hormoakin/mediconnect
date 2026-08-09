# ══════════════════════════════════════════════════════════════
# backend/apps/accounts/migrations/0002_receptionist_role.py
#
# Migration: adds 'receptionist' to User.Role choices and
# creates the ReceptionistProfile model.
#
# Place this file at:
#   backend/apps/accounts/migrations/0002_receptionist_role.py
#
# Then run:
#   python manage.py migrate
# OR inside Kubernetes:
#   kubectl exec -n mediconnect <backend-pod> -- python manage.py migrate
# ══════════════════════════════════════════════════════════════

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # Replace '0001_initial' with the actual name of your last migration
        # Run: python manage.py showmigrations accounts
        # to see what your latest migration is
        ('accounts', '0001_initial'),
    ]

    operations = [

        # ── Step 1: Add 'receptionist' choice to User.role field ──
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('patient',      'Patient'),
                    ('doctor',       'Doctor'),
                    ('pharmacist',   'Pharmacist'),
                    ('receptionist', 'Receptionist'),
                    ('admin',        'Administrator'),
                ],
                default='patient',
                max_length=20,
                verbose_name='Role',
            ),
        ),

        # ── Step 2: Create ReceptionistProfile model ──────────────
        migrations.CreateModel(
            name='ReceptionistProfile',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                ('department', models.CharField(
                    blank=True,
                    max_length=100,
                    verbose_name='Department',
                    help_text='e.g. General Outpatient, Maternity, Paediatrics',
                )),
                ('staff_id', models.CharField(
                    blank=True,
                    null=True,
                    max_length=50,
                    unique=True,
                    verbose_name='Staff ID',
                )),
                ('is_available', models.BooleanField(
                    default=True,
                    verbose_name='Is Available',
                    help_text='Whether the receptionist is currently on duty',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='receptionist_profile',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='User',
                )),
            ],
            options={
                'db_table': 'receptionist_profiles',
                'verbose_name': 'Receptionist Profile',
                'verbose_name_plural': 'Receptionist Profiles',
                'ordering': ['user__full_name'],
            },
        ),

        # ── Step 3: Add index on user for fast profile lookup ──────
        migrations.AddIndex(
            model_name='receptionistprofile',
            index=models.Index(
                fields=['user'],
                name='receptionist_user_idx',
            ),
        ),
    ]
