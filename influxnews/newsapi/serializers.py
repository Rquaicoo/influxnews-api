from rest_framework import serializers
from .models import News, Author

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'image']

class NewsSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    class Meta:
        model = News
        fields = ['id', 'title', 'description', 'url', 'publishedAt', 'content', 'category', 'country', 'language', 'date_scraped', 'author']