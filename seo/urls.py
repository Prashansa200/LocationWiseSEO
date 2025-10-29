from django.urls import path
from .views import index, SEOByCoordsView

urlpatterns = [
    path("", index, name="index"),
    path("api/seo-by-coords/", SEOByCoordsView.as_view(), name="seo_by_coords"),
]
