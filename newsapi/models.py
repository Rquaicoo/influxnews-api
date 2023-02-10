from django.db import models

# Create your models here.
class NewsO(models.Model):
    title = models.CharField(max_length=2000)
    description = models.TextField()
    url = models.URLField()
    image = models.URLField()
    publishedAt = models.DateTimeField()
    content = models.TextField()
    source = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    language = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    
    def __str__(self):
        return self.title