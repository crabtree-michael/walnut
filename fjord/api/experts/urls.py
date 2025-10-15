from django.urls import path

from .views import ExpertSearchView

urlpatterns = [
    path("", ExpertSearchView.as_view(), name="expert-search"),
]
