import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_processing", "0001_initial"),
        ("documents", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentEmbedding",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("chunk_index", models.PositiveIntegerField()),
                ("page_number", models.PositiveIntegerField(blank=True, null=True)),
                ("text", models.TextField()),
                ("vector", models.JSONField()),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="embeddings",
                        to="documents.document",
                    ),
                ),
            ],
            options={
                "ordering": ["document_id", "chunk_index"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("document", "chunk_index"),
                        name="unique_document_embedding_chunk",
                    ),
                ],
            },
        ),
    ]
