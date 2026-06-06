from django.shortcuts import render, get_object_or_404
from .models import *
from documents.models import *


def home(request):
    projects = Project.objects.all()

    return render(
        request,
        "home.html",
        {
            "projects": projects
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

