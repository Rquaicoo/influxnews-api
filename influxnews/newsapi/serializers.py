from rest_framework import serializers
from .models import News

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'description', 'url', 'urlToImage', 'publishedAt', 'content', 'source', 'category', 'country', 'language', 'date_scrapped', 'author']