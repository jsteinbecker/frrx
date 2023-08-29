from django.urls import path, include
from .api import VersionApiViews

app_name = "ver-api"


urlpatterns = [

    path("<ver>/api/version-solve-progress/", VersionApiViews.version_solving_progress, name="ver-solve-progress"),

]
