import uuid

from django.conf import settings
from django.db import models


class PromptTemplate(models.Model):
    class TaskType(models.TextChoices):
        CHAT = "chat", "Chat"
        SUMMARIZE = "summarize", "Summarize"
        TRANSLATE = "translate", "Translate"
        CODE = "code", "Code"
        EXTRACT = "extract", "Extract"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("orgs.Organization", on_delete=models.CASCADE, related_name="prompt_templates")
    name = models.CharField(max_length=200)
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.CHAT)
    system_text = models.TextField(blank=True, default="")
    user_text = models.TextField(blank=True, default="")
    variables_json = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "prompt_templates_prompttemplate"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
