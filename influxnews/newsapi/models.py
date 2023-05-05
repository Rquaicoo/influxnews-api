from django.db import models
import datetime
from django.contrib.auth.models import User


# Create your models here.
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
    saved_by = models.ManyToManyField(User, related_name="saved_news", blank=True)

    view_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title
    

class Author(models.Model):
    name = models.CharField(max_length=100)
    image = models.URLField(default="")
    
    def __str__(self):
        return self.name
    
class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username + " " + self.news.title

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100)
    
    def __str__(self):
        return self.user.username + " " + self.action + " " + self.news.title