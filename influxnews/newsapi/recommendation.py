from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from newsapi.models import News


def check_article_similarity(article1, article2):
    '''
    Check if the articles are similar with cosine similarity

    :param article1: Article 1
    :param article2: Article 2
    '''

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform([article1, article2])
    cosine_similarity = linear_kernel(matrix[0:1], matrix).flatten()
    return cosine_similarity[1]

def get_similar_articles(article_id):
    '''
    Get similar articles

    :param article_id: Article ID
    '''

    for article in News.objects.all():
        similarity = check_article_similarity(article_id, article.id)
        if similarity > 0.5:
            return article.id
    pass

def get_recommended_articles(article_id):
    # Get recommended articles
    pass

def get_recommended_articles_for_user(user_id):
    # Get recommended articles for user
    pass

def get_recommended_articles_for_user_by_category(user_id, category):
    # Get recommended articles for user by category
    pass

def get_recommended_articles_for_user_by_country(user_id, country):
    # Get recommended articles for user by country
    pass

def get_recommended_articles_for_user_by_language(user_id, language):
    # Get recommended articles for user by language
    pass







def check_article_popularity(article_id):
    # Check if the article is popular
    pass

def get_popular_articles():
    # Get popular articles
    pass

def get_popular_articles_by_category(category):
    # Get popular articles by category
    pass

def get_popular_articles_by_country(country):
    # Get popular articles by country
    pass
