from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import rest_framework.status as status
from .models import News
from .news_utils import searchNews
from .serializers import NewsSerializer

# Create your views here.
class NewsAPIView():
    authentication_classes  = [AllowAny]

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

            #check if news is empty
            if not news:
                searchNews(query)

            news = News.objects.filter(language=language, country=country, category=category, title__icontains=query).order_by('-publishedAt')
            
            searialized_news = NewsSerializer(news, many=True)
            return Response(searialized_news.data, status=status.HTTP_200_OK)

        if latest:
            news = News.objects.filter(language=language, country=country, category=category).order_by('-publishedAt')[:10]
            searialized_news = NewsSerializer(news, many=True)
            return Response(searialized_news.data, status=status.HTTP_200_OK)

        news = News.objects.filter(language=language, country=country, category=category).order_by('-publishedAt')
        searialized_news = NewsSerializer(news, many=True)
        return Response(searialized_news.data, status=status.HTTP_200_OK)
