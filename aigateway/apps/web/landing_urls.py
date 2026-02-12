from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing_view, name="landing"),
    path("pricing/", views.pricing_view, name="pricing"),
    path("models/", views.models_catalog_view, name="models_catalog"),
    path("models/<slug:provider_slug>/<path:model_slug>", views.model_detail_view, name="model_detail"),
]
