from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import rest_framework.status as status
from rest_framework.views import APIView
from .models import News, Author
from .news_utils import getBBCHeadlines, getBBCSportsHeadLines, getTechCruchHeadlines
from .serializers import NewsSerializer
from rest_framework.pagination import PageNumberPagination


class NewsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 20
    page_query_param = 'p'

# Create your views here.
class NewsAPIView(APIView):
    permission_classes  = [AllowAny] #change this to firebase authentication
    pagination_class = NewsPagination

    authentication_classes  = [] #change this to firebase authentication

    def get(self, request):
        """
        Parameters:

        language (str)
        country (str) 
        category (str)
        latest (bool) 
        """

        language = request.GET.get('language', 'en')
        country = request.GET.get('country', 'worldwide')
        category = request.GET.get('category')
        latest = request.GET.get('latest', False)
        query = request.GET.get('query')

        if query:

            all_news_items = News.objects.filter(language=language, country=country)

            search_results = all_news_items.order_by('-publishedAt').filter(title__icontains=query)

            searialized_news = NewsSerializer(search_results, many=True)

            return Response(searialized_news.data, status=status.HTTP_200_OK)

        if latest:
            news = News.objects.filter(language=language, country=country, category=category).order_by('-publishedAt')[:10]
            searialized_news = NewsSerializer(news, many=True)
            return Response(searialized_news.data, status=status.HTTP_200_OK)
        
        if category:
            news = News.objects.filter(language=language, country=country, category=category)
            searialized_news = NewsSerializer(news, many=True)
            return Response(searialized_news.data, status=status.HTTP_200_OK)

        news = News.objects.all().order_by('-publishedAt')  
        searialized_news = NewsSerializer(news, many=True)
        print(searialized_news.data)
        return Response(searialized_news.data, status=status.HTTP_200_OK)

class NewsScraperAPIView(APIView):
    permission_classes  = [AllowAny] #change this to firebase authentication

    def get(self, request):
        
        getBBCHeadlines()
        getBBCSportsHeadLines()
        getTechCruchHeadlines()
        return Response("News Scrapped", status=status.HTTP_200_OK)
    
