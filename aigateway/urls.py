from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("aigateway.apps.accounts.urls")),
    path("onboarding/", include("aigateway.apps.orgs.urls")),
    path("app/", include("aigateway.apps.web.urls")),
    path("api/v1/", include("aigateway.apps.api.urls")),
    path("legal/", include("aigateway.apps.web.legal_urls")),
    path("", include("aigateway.apps.web.landing_urls")),
]
