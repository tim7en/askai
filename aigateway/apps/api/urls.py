from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("ai/generate", views.AIGenerateView.as_view(), name="ai_generate"),
    path("usage", views.UsageListView.as_view(), name="usage_list"),
    path("usage/export.csv", views.UsageExportCSVView.as_view(), name="usage_export"),
    path("templates", views.PromptTemplateListCreateView.as_view(), name="template_list"),
    path("templates/<uuid:pk>", views.PromptTemplateDetailView.as_view(), name="template_detail"),
    path("models", views.ModelsListView.as_view(), name="models_list"),
    path("models/<path:model_id>", views.ModelDetailView.as_view(), name="model_detail"),
    path("chat/completions", views.ChatCompletionsView.as_view(), name="chat_completions"),
    path("credits", views.CreditsView.as_view(), name="credits"),
    path("key", views.KeyInfoView.as_view(), name="key_info"),
]
