from django.shortcuts import render, get_object_or_404
from .models import *
from documents.models import *
from .forms import ProjectForm
from django.shortcuts import redirect
from documents.models import Document
from django.shortcuts import redirect
from django.db.models import Q


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

            Document.objects.create(
                project=project,
                filename=uploaded_file.name,
                file=uploaded_file
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