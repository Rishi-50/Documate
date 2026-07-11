from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name="home"),
    path("project/<int:project_id>/", project_detail, name="project_detail"),
    path("projects/create/",create_project,name="create_project"),
    path("documents/<int:document_id>/delete/",delete_document,name="delete_document"),
    path("documents/<int:document_id>/",document_detail,name="document_detail"),
]
