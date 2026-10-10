from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "client_name"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. North Tower Renovation",
                    "autocomplete": "organization",
                }
            ),
            "client_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Client or organization",
                    "autocomplete": "organization",
                }
            ),
        }