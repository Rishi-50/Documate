from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name="home"),
    path("project/<int:project_id>/", project_detail, name="project_detail"),
]