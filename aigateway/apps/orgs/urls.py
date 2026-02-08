from django.urls import path

from . import views

app_name = "orgs"

urlpatterns = [
    path("", views.onboarding_view, name="onboarding"),
]
