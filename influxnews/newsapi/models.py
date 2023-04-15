from django.db import models
import datetime

# Create your models here.
class News(models.Model):
    title = models.CharField(max_length=2000)
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
    
    def __str__(self):
        return self.title
    

class Author(models.Model):
    name = models.CharField(max_length=100)
    image = models.URLField(default="")
    
    def __str__(self):
        return self.name