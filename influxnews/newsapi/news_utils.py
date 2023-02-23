import requests
import os
from .models import News
import environ

env = environ.Env()
environ.Env.read_env()

def getLatestHeadLines(apiKey=env("NEWS_API_KEY")):
    """
    Get news from NewsAPI
    endpoint: https://newsapi.org/v2/everything
    """

    #get breaking news
    results = requests.get(f"https://newsapi.org/v2/top-headlines?pageSize=100&apiKey={apiKey}").json()

    if results["status"] == "ok":
        for result in results.json()["articles"]:
            if result["url"]:
                News.objects.create(
                    title=result["title"] if result["title"] else "",
                    description=result["description"] if result["description"] else "",
                    url=result["url"],
                    image=result["urlToImage"] if result["urlToImage"] else "",
                    publishedAt=result["publishedAt"],
                    content=result["content"] if result["content"] else "",
                    source=result["source"]["name"] if result["source"]["name"] else "Unknown",
                    category="general",
                    country="worldwide",
                    language="en",
                    author=result["author"] if result["author"] else ""
                )
    return results


def getNewsFromMediaStack(apiKey=env("MEDIA_STACK_API_KEY")):
    categories = ["business", "entertainment", "health", "science", "sports", "technology"]
    
    for category in categories:
        results = requests.get(f"http://api.mediastack.com/v1/news?access_key={apiKey}&categories={category}&languages=en&limit=100&sort=popularity").json()
        for result in results["data"]:
            if result["url"]:
                News.objects.create(
                    title=result["title"] if result["title"] else "",
                    description=result["description"] if result["description"] else "",
                    url=result["url"],
                    image=result["image"] if result["image"] else "",
                    publishedAt=result["published_at"],
                    content=result["description"] if result["description"] else "",
                    source=result["source"] if result["source"] else "Unknown",
                    category=category,
                    country=result["country"] if result["country"] else "worldwide",
                    language=result["language"] if result["language"] else "en",
                    author=result["author"] if result["author"] else ""
                )


def searchNewsFromWorldAPI(query, apiKey=env("WORLD_NEWS_API_KEY")):
    results = requests.get(f"https://api.worldnewsapi.com/search-news?text={query}&api-key={apiKey}&sort=publish-time").json()

    for result in results["news"]:
        News.objects.create(
            title=result["title"],
            description=result["text"],
            url=result["url"],
            image=result["image"],
            publishedAt=result["publish_date"],
            content=result["text"],
            source=result["source_country"],
            author=result["author"]
        )

def searchNewsFromNewsAPI(query, apiKey=env("NEWS_API_KEY")):
    results = requests.get(f"https://newsapi.org/v2/everything?q={query}&apiKey={apiKey}&pageSize=100&sortBy=popularity")

    if results.status == "ok":
        for result in results.json()["articles"]:
            News.objects.create(
                title=result["title"],
                description=result["description"],
                url=result["url"],
                image=result["urlToImage"],
                publishedAt=result["publishedAt"],
                content=result["content"],
                source=result["source"]["name"],
                category="general",
                country="worldwide",
                language="en",
                author=result["author"]
            )


def searchNews(query):
    world_api_results = searchNewsFromWorldAPI(query)
    news_api_results = searchNewsFromNewsAPI(query)
