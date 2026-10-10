import logging

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from pydantic import ValidationError

from .models import *
from documents.models import *
from .forms import ProjectForm
from django.shortcuts import redirect
from documents.models import Document
from django.shortcuts import redirect
from django.db.models import Q

from ai_processing.models import DocumentIntelligence
from ai_processing.services.processing_manager import ProcessingManager
from ai_processing.services.ocr_service import OCRService
from ai_processing.services.intelligence_service import IntelligenceService
from ai_processing.services.organization_service import OrganizationService
from ai_processing.services.embedding_service import EmbeddingService
from ai_processing.schemas.assistant_schema import AssistantQuestion
from ai_processing.services.assistant_service import AssistantService
from ai_processing.services.processing_manager import *
from ai_processing.services.intelligence_service import IntelligenceService

logger = logging.getLogger(__name__)


def home(request):

    query = request.GET.get("q", "")

    projects = Project.objects.all().prefetch_related(
        "documents"
    )   

    if query:
        projects = projects.filter(
            Q(name__icontains=query) |
            Q(client_name__icontains=query)
        )

    total_projects = Project.objects.count()

    total_documents = Document.objects.count()

    recent_documents = (
        Document.objects
        .select_related("project")
        .order_by("-uploaded_at")[:5]
    )   

    return render(
        request,
        "home.html",
        {
            "projects": projects,
            "total_projects": total_projects,
            "total_documents": total_documents,
            "recent_documents": recent_documents,
            "query": query,
        }
)


def project_detail(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id
    )

    if request.method == "POST":

        uploaded_file = request.FILES.get(
            "document_file"
        )

        if uploaded_file:

            document = Document.objects.create(
                project=project,
                filename=uploaded_file.name,
                file=uploaded_file
            )

            processing_manager = ProcessingManager(
                pipeline=[
                    OCRService(),
                    IntelligenceService(),
                    OrganizationService(),
                    EmbeddingService(),
                ]
            )

            processing_manager.process_document(
                document=document,
                intelligence=document.intelligence,
            )   

    documents = project.documents.all()

    return render(
        request,
        "project_detail.html",
        {
            "project": project,
            "documents": documents
        }
    )


@require_POST
def project_assistant(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    question = request.POST.get("question", "").strip()

    if not question:
        return JsonResponse(
            {"error": "Please enter a question before sending."},
            status=400,
        )

    if len(question) > 2000:
        return JsonResponse(
            {"error": "Keep your question to 2000 characters or fewer."},
            status=400,
        )

    try:
        assistant_question = AssistantQuestion(question=question)
    except ValidationError:
        return JsonResponse(
            {"error": "The question is invalid. Please edit it and try again."},
            status=400,
        )

    try:
        answer = AssistantService().answer_question(
            project=project,
            question=assistant_question.question,
        )
    except Exception:
        logger.exception(
            "Project assistant failed | project=%s",
            project.id,
        )
        return JsonResponse(
            {"error": "The assistant is temporarily unavailable. Please try again."},
            status=502,
        )

    return JsonResponse(answer.model_dump(mode="json"))


def create_project(request):

    if request.method == "POST":

        form = ProjectForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("home")

    else:
        form = ProjectForm()

    return render(
        request,
        "create_project.html",
        {
            "form": form
        }
    )


def delete_document(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id
    )

    project_id = document.project.id

    document.file.delete()

    document.delete()

    return redirect(
        "project_detail",
        project_id=project_id
    )

def document_detail(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id
    )

    return render(
        request,
        "document_detail.html",
        {
            "document": document
        }
    )
