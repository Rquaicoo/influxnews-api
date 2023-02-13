from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Create your views here.
class NewsAPIView():
    authentication_classes  = [AllowAny]

    def get(self, request):
        """
        Parameters:

        category (str)
        country (str)
        language (str)
        """
        category = request.GET.get("category")
        country = request.GET.get("country")
        language = request.GET.get("language")

        if not category:
            category = "general"
        if not country:
            country = "worldwide"
        if not language:
            language = "en"
