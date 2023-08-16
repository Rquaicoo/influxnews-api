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
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 70
    page_query_param = 'p'


class PaginationHandlerMixin(object):
    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        else:
            pass
        return self._paginator
    def paginate_queryset(self, queryset):
        
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset,
                   self.request, view=self)
    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)
    

class CreateUserAPIView(APIView):
    def post(self, request):
        pass

# Create your views here.
class NewsAPIView(APIView, PaginationHandlerMixin):
    permission_classes  = [AllowAny] #change this to firebase authentication
    pagination_class = NewsPagination
    serializer_class = NewsSerializer

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
            
            page = self.paginate_queryset(news)

            if page is not None:
                serialized_news = self.get_paginated_response(self.serializer_class(page, many=True).data)
            else:
                serialized_news = self.serializer_class(news, many=True)
            return Response(serialized_news.data, status=status.HTTP_200_OK)

        news = News.objects.all().order_by('-publishedAt')  
        
        page = self.paginate_queryset(news)
        if page is not None:
            serialized_news = self.get_paginated_response(self.serializer_class(page, many=True).data)

        else:
            serialized_news = self.serializer_class(news, many=True)
        
        print(serialized_news.data)

        return Response(serialized_news.data, status=status.HTTP_200_OK)
    

class LikedNewsAPIView(APIView):

    def post(self, request):
        """
        Parameters:
        news_id (int)
        """
        news_id = request.data.get('news_id')
        news = News.objects.get(id=news_id)
        news.likes += 1
        news.save()
        return Response("Liked", status=status.HTTP_200_OK)

class NewsScraperAPIView(APIView):
    permission_classes  = [AllowAny] #change this to firebase authentication

    def get(self, request):
        
        getBBCHeadlines()
        getBBCSportsHeadLines()
        getTechCruchHeadlines()
        return Response("News Scrapped", status=status.HTTP_200_OK)
    
