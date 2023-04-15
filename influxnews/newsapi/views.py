from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import rest_framework.status as status
from rest_framework.views import APIView
from .models import News
from .news_utils import getBBCHeadlines, getBBCSportsHeadLines, getTechCruchHeadlines
from .serializers import NewsSerializer

# Create your views here.
class NewsAPIView(APIView):
    authentication_classes  = [] #change this to firebase authentication

    def get(self, request, language="en", country="worldwide", category="general", latest=False, query=None):
        """
        Parameters:

        language (str)
        country (str)
        category (str)
        latest (bool)
        """
        if query:
            news = News.objects.filter(language=language, country=country, category=category, title__icontains=query).order_by('-publishedAt')

            news = News.objects.filter(language=language, country=country, category=category, title__icontains=query).order_by('-publishedAt')
            
            searialized_news = NewsSerializer(news, many=True)
            return Response(searialized_news.data, status=status.HTTP_200_OK)

        if latest:
            news = News.objects.filter(language=language, country=country, category=category).order_by('-publishedAt')[:10]
            searialized_news = NewsSerializer(news, many=True)
            return Response(searialized_news.data, status=status.HTTP_200_OK)

        news = News.objects.all().order_by('-publishedAt')
        searialized_news = NewsSerializer(news, many=True)
        return Response(searialized_news.data, status=status.HTTP_200_OK)

class NewsScraperAPIView(APIView):
    permission_classes  = [AllowAny] #change this to firebase authentication

    def get(self, request):
        
        getBBCHeadlines()
        getBBCSportsHeadLines()
        getTechCruchHeadlines()
        return Response("News Scrapped", status=status.HTTP_200_OK)