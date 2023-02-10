def getNewsFromNewsAPI(query, source, apiKey):
    """
    Get news from NewsAPI
    endpoint: https://newsapi.org/v2/everything
    """
    pass


def getNewsFromMediaStack(query, source, apiKey):
    pass

def getNewsFromNewsData(query, source, apiKey):
    pass

def getNewsFromTheNewsAPI(query, source, apiKey):
    """
    Get news from TheNewsAPI
    endpoint: https://api.thenewsapi.com/v1/news/all HTTP/1.1/api_token=API_KEY&search=tesla&sort=published_on&categories=technology&language=en&country=us

    docs: https://www.thenewsapi.com/documentation

    returns:

    {
    "meta": {
        "found": 551151,
        "returned": 10,
        "limit": 10,
        "page": 1
    },
    "data": [
        {
            "uuid": "c242275b-7e30-4a25-b2cc-5b40e2704beb",
            "title": "From one gig to the next, Juston McKinney keeps the locals laughing",
            "description": "Nearly 30 years since it started, McKinney’s career is on a sustained upswing, and the jokes keep flowing. On the strength of his new YouTube special “On th...",
            "keywords": "",
            "snippet": "The fan still remembered ...,
            "url": "https://www.bostonglobe.com/2023/02/08/arts/one-gig-next-juston-mckinney-keeps-locals-laughing/?camp=bg:brief:rss:feedly&rss_id=feedly_rss_brief",
            "image_url": "https://bostonglobe-prod.cdn.arcpublishing.com/resizer/Ntp6q8btOH9YwXM-y65xig38hQg=/506x0/cloudfront-us-east-1.images.arcpublishing.com/bostonglobe/S24N6ZEIA7OSAHHLI55Q63FMHQ.JPG",
            "language": "en",
            "published_at": "2023-02-08T21:28:01.000000Z",
            "source": "bostonglobe.com",
            "categories": [
                "general"
            ],
            "relevance_score": null,
            "locale": "us"
        },...
    ]
    """
    pass

def searchNewsFromWorldAPI(query, source, sortBy, apiKey):
    """
    Search news from WorldAPI
    https://api.worldnewsapi.com/search-news?text=tesla&api-key=YOUR_API_KEY&sort=publish-time

    50 pts/day

    returns:
    
    "offset": 0,
    "number": 10,
    "available": 23125,
    "news": [
        {
            "id": 1878,
            "title": "Why China’s electric vehicles are all over Europe",
            "text": "On the Mediterranean island of Corsica, halfway between Marseilles and the Italian shore, stands a rental car lot fitted with Europe’s finest...",
            "url": "https://supchina.com/2022/03/04/why-chinas-electric-vehicles-are-all-over-europe/",
            "image": "https://supchina.com/wp-content/uploads/2022/03/SupChina-57-scaled.jpg",
            "publish_date": "2022-03-04 22:12:35",
            "author": "Alex Santafe",
            "language": "en",
            "source_country": "cn"
        },...
    ]
}
    """
    pass

def searchNewsFromTheNewsAPI(query, source, apiKey):
    pass


def searchNews(query):
    pass

def getNews(query):
    pass