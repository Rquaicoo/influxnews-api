from django.db import models
import datetime
from django.contrib.auth.models import User


class UserInterests(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interests = models.CharField(max_length=1000, default="")
    
    def __str__(self):
        return self.user.username + " " + self.interests
    

class News(models.Model):
    title = models.CharField(max_length=9000)
    description = models.TextField()
    url = models.URLField()
    image = models.URLField(default="")
    publishedAt = models.DateTimeField(default=datetime.datetime.now)
    content = models.TextField(default="")
    category = models.CharField(max_length=100, default="general")
    country = models.CharField(max_length=100, default="worldwide")
    language = models.CharField(max_length=100, default="en")
    date_scraped = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, default=1, null=True)

    viewed_by = models.ManyToManyField(User, related_name="viewed_news", blank=True)
    liked_by = models.ManyToManyField(User, related_name="saved_news", blank=True)

    view_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title    

class Author(models.Model):
    name = models.CharField(max_length=100)
    image = models.URLField(default="")
    
    def __str__(self):
        return self.name
    
class BookmarkedNewsItem(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    news = models.ManyToManyField(News, related_name="bookmarked_news")
    
    def __str__(self):
        return self.user.username
