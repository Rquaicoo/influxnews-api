from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from newsapi.models import News
from django.contrib.auth.models import User
import re


def filter_by_user_content(user_id, num_recommendations):
    """
    This function takes in a user id and returns a list of news articles that are similar to the news articles that the user has viewed.
    """
    
    news_articles = News.objects.filter(viewed_by=user_id).order_by('-date_scraped')
    all_news_articles = News.objects.all().order_by('-date_scraped')

    viewed_news_content = [article.description for article in news_articles]
    all_news_content = [article.description for article in all_news_articles]

    combined_content = viewed_news_content + all_news_content 

    vectorizer = TfidfVectorizer(stop_words='english')

    tfidf_matrix = vectorizer.fit_transform(combined_content)

    # cosine_similarity = cosine_similarity(tfidf_matrix[-len(viewed_news_content):], tfidf_matrix)
    cosine_similarity = cosine_similarity(tfidf_matrix, tfidf_matrix)

    viewed_articles_index = [all_news_articles.index(article) for article in news_articles]

    avg_cosine_similarity = cosine_similarity.mean(axis=0)
    
    recommended_indices = sorted(range(len(avg_cosine_similarity)), key=lambda i: avg_cosine_similarity[i], reverse=True)

    recommendations = [all_news_articles[i] for i in recommended_indices if i not in viewed_articles_index]

    return recommendations



def filter_by_other_user_interests(user_id, num_recommendations):
    """
    This function takes in a user id and returns a list of news articles that are similar to the news articles that the user and other users have viewed.
    """

    user = User.objects.get(id=user_id)

    other_news_articles = News.objects.exclude(viewed_by=user_id).order_by('-date_scraped')

    all_news_articles = News.objects.all().order_by('-date_scraped')

    other_news_content = [article.description for article in other_news_articles]
    all_news_content = [article.description for article in all_news_articles]

    combined_content = other_news_content + all_news_content

    vectorizer = TfidfVectorizer(stop_words='english')

    tfidf_matrix = vectorizer.fit_transform(combined_content)

    # cosine_similarity = cosine_similarity(tfidf_matrix[-len(other_news_content):], tfidf_matrix)
    cosine_similarity = cosine_similarity(tfidf_matrix, tfidf_matrix)

    avg_cosine_similarity = cosine_similarity.mean(axis=0)

    recommended_indices = sorted(range(len(avg_cosine_similarity)), key=lambda i: avg_cosine_similarity[i], reverse=True)

    recommendations = [all_news_articles[i] for i in recommended_indices]

    return recommendations




def recommend_top_three_news(news_content, user):
    pass

