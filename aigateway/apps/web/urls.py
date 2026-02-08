from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("playground/", views.playground_view, name="playground"),
    path("templates/", views.templates_view, name="templates"),
    path("templates/create/", views.template_create_view, name="template_create"),
    path("usage/", views.usage_view, name="usage"),
    path("usage/export.csv", views.usage_export_csv, name="usage_export_csv"),
    path("providers/", views.providers_view, name="providers"),
    path("providers/add/", views.provider_add_credential_view, name="provider_add"),
    path("members/", views.members_view, name="members"),
    path("members/invite/", views.member_invite_view, name="member_invite"),
    path("billing/", views.billing_view, name="billing"),
    path("settings/", views.settings_view, name="settings"),
]
