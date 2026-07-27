from django.db import models

from ai_processing.schemas.base import ProcessingStage, ProcessingStatus


class DocumentIntelligence(models.Model):
    """
    Stores AI-generated intelligence and processing state for a document.
    """

    document = models.OneToOneField(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="intelligence",
    )

    processing_stage = models.CharField(
        max_length=50,
        choices=[(stage.value, stage.value) for stage in ProcessingStage],
        default=ProcessingStage.PENDING.value,
    )

    processing_status = models.CharField(
        max_length=20,
        choices=[(status.value, status.value) for status in ProcessingStatus],
        default=ProcessingStatus.PENDING.value,
    )

    processing_started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_processed = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_error = models.TextField(
        blank=True,
    )

    document_type = models.CharField(
        max_length=100,
        blank=True,
    )

    confidence_score = models.FloatField(
        default=0.0,
    )

    ocr_text = models.TextField(
        blank=True,
    )

    ocr_pages = models.JSONField(
        default=list,
        blank=True,
    )

    extracted_metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    embeddings_created = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Document Intelligence"
        verbose_name_plural = "Document Intelligence"

    def __str__(self):
        return f"Intelligence - {self.document}"


class ProcessingLog(models.Model):
    """
    Stores the execution history of each processing stage.
    """

    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="processing_logs",
    )

    stage = models.CharField(
        max_length=50,
        choices=[(stage.value, stage.value) for stage in ProcessingStage],
    )

    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.value) for status in ProcessingStatus],
    )

    message = models.TextField()

    execution_time = models.FloatField(
        default=0.0,
        help_text="Execution time in seconds.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Processing Log"
        verbose_name_plural = "Processing Logs"

    def __str__(self):
        return f"{self.document} | {self.stage} | {self.status}"