from rest_framework import serializers
from rest_framework.fields import empty
from .models import News, Author

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'image']

class NewsSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    class Meta:
        model = News
        fields = ['id', 'title', 'description', 'url', 'image', 'publishedAt', 'content', 'category', 'country', 'language', 'date_scraped', 'author']


class UserFeedSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=..., **kwargs):
        super().__init__(instance, data, **kwargs)
    
    liked = serializers.SerializerMethodField()
    author = AuthorSerializer()

    class Meta:
        model = News
        fields = ['id', 'title', 'description', 'url', 'image', 'publishedAt', 'content', 'category', 'country', 'language', 'date_scraped', 'author', 'liked']

    def get_liked(self, obj):
        user = self.context['request'].user
        return user in obj.liked_by.all()