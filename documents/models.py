from django.db import models
from projects.models import Project


class Document(models.Model):
    STATUS_CHOICES = [
        ("UPLOADED", "Uploaded"),
        ("PROCESSING", "Processing"),
        ("PROCESSED", "Processed"),
        ("REVIEW_REQUIRED", "Review Required"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    filename = models.CharField(max_length=255)

    file = models.FileField(upload_to="uploads/")

    document_type = models.CharField(
        max_length=50,
        default="UNKNOWN"
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="UPLOADED"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename