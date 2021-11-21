from django.urls import path
from .views import apify
urlpatterns = [
    path("<string:path>", view=apify, name='apify_view')
]
