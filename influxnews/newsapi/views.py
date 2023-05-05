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


# Create your views here.
class NewsAPIView(APIView):
    permission_classes  = [AllowAny] #change this to firebase authentication
    pagination_class = NewsPagination

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

            all_news_items = News.objects.filter(language=language, country=country, category=category)

            search_results = all_news_items.order_by('-publishedAt').filter(title__icontains=query)

            searialized_news = NewsSerializer(news, many=True)

            return Response(searialized_news.data, status=status.HTTP_200_OK)

        if latest:
            news = News.objects.filter(language=language, country=country, category=category).order_by('-publishedAt')[:10]
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
    

class CorrectUrlsAPIView(APIView):

    def get(self, request):
        #get news from bbc and bbc sport
        bbc_news = Author.objects.get(name='BBC News')
        bbc_sport = Author.objects.get(name='BBC Sport')
        news = News.objects.filter(author=bbc_news)
        sports = News.objects.filter(author=bbc_sport)

        for n in news:
            if n.url.split("//")[1][0:3] != "bbc" or n.url.split("//")[1][0:3] != 'www':
                n.url = n.url.split("//")[0] + "//bbc.com/" + n.url.split("//")[1]
                n.save()

        for n in sports:
            if n.url.split("//")[1][0:3] != "bbc" or n.url.split("//")[1][0:3] != 'www':
                n.url = n.url.split("//")[0] + "//bbc.com/" + n.url.split("//")[1]
                n.save()

        return Response("Urls Corrected", status=status.HTTP_200_OK)