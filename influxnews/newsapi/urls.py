from django.urls import path
from .views import *

urlpatterns = [
    path("news/", NewsAPIView.as_view(), name="news_list"),
    
    path("news_scraper/", NewsScraperAPIView.as_view(), name="news_scraper"),

]