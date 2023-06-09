import requests
import os
from .models import News, Author
import environ
from bs4 import BeautifulSoup
import re

env = environ.Env()
environ.Env.read_env()


#authors
bbc_news = Author.objects.get(name='BBC News')
tech_crunch = Author.objects.get(name='TechCrunch')
bbc_sport = Author.objects.get(name='BBC Sport')



def getBBCHeadlines():
    respose = requests.get('https://www.bbc.com/', headers={'Referer': 'https://www.google.com/'})
    soup = BeautifulSoup(respose.text, 'html.parser')

    #get undordered list with class 'media-list'
    news_list = soup.find('ul', {'class': 'media-list'})

    #for each list item get the link, image, title and description
    news = []
    for li in news_list.find_all('li'):
        link = li.find('a')['href']
        image = li.find('img')['src']
        tag = li.find('a', {'class': 'media__tag'}).text if li.find('a', {'class': 'media__tag'}) else ''
        title = re.sub('\s+', " ", li.find('h3').text) if li.find('h3') else li.find('h4').text
        description = re.sub('\s+', " ", li.find('p').text) if li.find('p') else ''

        print(link, image, title, description, tag)

        news, created = News.objects.get_or_create(
            title=title,
            description=description,
            url=link,
            image=image,
            category=tag,
            country='worldwide',
            language='en',

            author=bbc_news
        )


def getBBCSportsHeadLines():
    football_news = "https://www.bbc.com/sport/football"
    response = requests.get(football_news, headers={'Referer': 'https://www.bbc.com/sport/football'})
    soup = BeautifulSoup(response.text, 'html.parser')

    #get div with class 'sp-qa-top-stories'
    news_list = soup.find('div', {'class': 'sp-qa-top-stories'})
    news = []

    for item in news_list.find_all('div', {'class': 'gs-c-promo'}):
        link = item.find('a')['href']
        image = item.find('img')['data-src'].replace("{width}", "800")
        title = item.find('h3').text
        description = item.find('a', {'class': 'gs-c-promo-heading'}).text

        news, created = News.objects.get_or_create(
            title=title,
            description=description,
            url=link,
            image=image,
            category='football',
            country='worldwide',
            language='en',

            author=bbc_sport
        )



def getTechCruchHeadlines():
    techcrunch = "https://techcrunch.com/"
    categories = ['artificial-intelligence', 'fintech', 'startups', 'security', 'cryptocurrency', 'apps', 'media-entertainment', 'hardware']

    for category in categories:
        response = requests.get(techcrunch + "category/" + category, headers={'Referer': 'https://techcrunch.com/'})
        soup = BeautifulSoup(response.text, 'html.parser')

        #get article elements
        news_list = soup.find('div', {'class': 'river'})

        for item in news_list.find_all('div', {'class': 'post-block'}):
            link = item.find('a')['href']
            image = item.find('img')['srcset'].split(' ')[4]    
            title = re.sub('\s+', " ", item.find('h2').text)
            description = re.sub('\s+', " ", item.find('div', {'class': 'post-block__content'}).text)
            time = item.find('time')['datetime']

            news, created = News.objects.get_or_create(
                title=title,
                description=description,
                url=link,
                image=image,
                category=category,
                country='worldwide',
                language='en',
                publishedAt=time,

                author=tech_crunch
            )