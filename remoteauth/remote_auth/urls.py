from django.urls import path
from .views import apify
urlpatterns = [
    path("<str:path>", view=apify, name='apify_view')
]
