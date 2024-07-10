from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

app_name = "admin_panel"   


urlpatterns = [
    path("statistic/", views.statistic, name="statistic"),
    path("statistic/statistic_api", views.statistic_api, name="statistic-api"),
    

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
