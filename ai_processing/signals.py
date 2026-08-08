from django.db.models.signals import post_save
from django.dispatch import receiver

from ai_processing.models import DocumentIntelligence
from documents.models import Document
from ai_processing.schemas.base import (
    ProcessingStage,
    ProcessingStatus,
)


@receiver(post_save, sender=Document)
def create_document_intelligence(sender, instance, created, **kwargs):
    """
    Automatically create a DocumentIntelligence record
    whenever a new document is uploaded.
    """

    if not created:
        return

    DocumentIntelligence.objects.create(
        document=instance,
        processing_stage=ProcessingStage.PENDING.value,
        processing_status=ProcessingStatus.PENDING.value,
    )