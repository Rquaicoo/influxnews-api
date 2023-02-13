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
    source = models.CharField(max_length=100, default="")
    category = models.CharField(max_length=100, default="general")
    country = models.CharField(max_length=100, default="worldwide")
    language = models.CharField(max_length=100, default="en")
    date_scraped = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=100)
    
    def __str__(self):
        return self.title