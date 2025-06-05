from bs4 import BeautifulSoup
from django.conf import settings
import requests
from urllib.parse import urljoin  
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db import IntegrityError
from .forms import CustomUserCreationForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError




def scrape_ndtv():
    base_url = "https://www.ndtv.com/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html5lib')
        news_items = soup.find_all('div', class_='LstWg1_tx mb-0 pip_fix')
        news_data = []

        for item in news_items:
            headline_tag = item.find('h3')
            if headline_tag is not None:
                headline = headline_tag.text
                link = item.find('a')['href']
                full_link = urljoin(base_url, link) 
                image_tag = item.find('img')
                image_url = image_tag['data-src'] if image_tag and image_tag.has_attr('data-src') else image_tag['src'] if image_tag else None
                news_data.append({'headline': headline, 'image_url': image_url, 'url': full_link})
        
        
        return news_data
    
    except Exception as e:
        print(f"Error scraping NDTV: {e}")
        return []
    
def scrape_the_hindu():
    base_url = "https://www.thehindu.com/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html5lib')
        news_items = soup.find_all('div', class_='row mt-3')
        news_data = []

        for item in news_items:
            headline_tag = item.find('h3')
            if headline_tag is not None:
                headline = headline_tag.text
                link = item.find('a')['href']
                full_link = link 
                image_tag = item.find('img')
                image_url = image_tag['data-src'] if image_tag and image_tag.has_attr('data-src') else image_tag['src'] if image_tag else None
                news_data.append({'headline': headline, 'image_url': image_url, 'url': full_link})
        
        
        return news_data
    
    except Exception as e:
        print(f"Error scraping The Hindu: {e}")
        return []

def scrape_times_of_india():
    base_url = "https://timesofindia.indiatimes.com/"
    url = "https://timesofindia.indiatimes.com/briefs"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html5lib')
        news_items = soup.find_all('div', class_='brief_box')
        news_data = []

        for item in news_items:
            headline_tag = item.find('h2')
            if headline_tag is not None:
                headline = headline_tag.text
                link = item.find('a')['href']
                full_link = link if link.startswith('http') else base_url.rstrip('/') + link  
                image_tag = item.find('img')
                image_url = image_tag['data-src'] if image_tag and image_tag.has_attr('data-src') else image_tag['src'] if image_tag else None
                news_data.append({'headline': headline, 'image_url': image_url, 'url': full_link})
        
        return news_data
    
    except Exception as e:
        print(f"Error scraping Times of India: {e}")
        return []


def scrape_news_categories(url, headers, item_selector, headline_selector, link_selector, image_selector, image_attr='data-src'):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        news_items = soup.select(item_selector)
        news_data = []

        for item in news_items:
            headline_tag = item.select_one(headline_selector)
            link_tag = item.select_one(link_selector)
            image_tag = item.select_one(image_selector)
            
            if headline_tag and link_tag:
                headline = headline_tag.get_text(strip=True)
                link = link_tag['href']
                full_link = urljoin(url,link)
                if image_tag: 
                    image_url = image_tag.get(image_attr) or image_tag.get('src') or image_tag.get('placeholdersrc')
                else:
                    image_url='/static/img/depositphotos_132158888-stock-photo-science-concept-science-on-newspaper.jpg'
                news_data.append({'headline': headline, 'image_url': image_url, 'url': full_link})

        
        return news_data

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def scrape_ndtv_national():
    return scrape_news_categories(
        url="https://www.ndtv.com/india#pfrom=home-ndtv_mainnavigation",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='div.newsHdng',
        headline_selector='h2',
        link_selector='a',
        image_selector='img'
    )
print(scrape_ndtv_national)
def scrape_the_hindu_national():
    return scrape_news_categories(
        url="https://www.thehindu.com/news/national/",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='div.title.big',
        headline_selector='h3',
        link_selector='a',
        image_selector='img'
    )

def scrape_times_of_india_national():
    return scrape_news_categories(
        url="https://timesofindia.indiatimes.com/briefs/india",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='div.brief_box',
        headline_selector='h2',
        link_selector='a',
        image_selector='img'
    )

def scrape_india_today_international():
    return scrape_news_categories(
        url="https://www.indiatoday.in/world",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='article.B1S3_story__card__A_fhi',
        headline_selector='h2',
        link_selector='a',
        image_selector='img',
        image_attr='src'
    ) 
def scrape_news18_international():
        return scrape_news_categories(
        url="https://www.news18.com/world/",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='div.jsx-50600299959a4159 blog_list_row',
        headline_selector='h3',
        link_selector='a',
        image_selector='img'
    )

def scrape_times_of_india_international():
    return scrape_news_categories(
        url="https://timesofindia.indiatimes.com/briefs/world",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='div.brief_box',
        headline_selector='h2',
        link_selector='a',
        image_selector='img'
    )


def scrape_india_today_sports():
    return scrape_news_categories(
        url="https://www.indiatoday.in/sports",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='article.B1S3_story__card__A_fhi',
        headline_selector='h3',
        link_selector='a',
        image_selector='img'
    )

def scrape_the_hindu_sports():
    return scrape_news_categories(
        url="https://www.thehindu.com/sport/",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='div.title',
        headline_selector='h3',
        link_selector='a',
        image_selector='img'
    )

def scrape_times_of_india_sports():
    return scrape_news_categories(
        url="https://timesofindia.indiatimes.com/briefs/sports",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='div.brief_box',
        headline_selector='h2',
        link_selector='a',
        image_selector='img'
    )

def scrape_india_today_science():
    return scrape_news_categories(
        url="https://www.indiatoday.in/science",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='article.B1S3_story__card__A_fhi  B1S3_Bcard__L7ikx',
        headline_selector='h3',
        link_selector='a',
        image_selector='img'
    )

def scrape_the_hindu_science():
    return scrape_news_categories(
        url="https://www.thehindu.com/sci-tech/science/",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='div.title',
        headline_selector='h3',
        link_selector='a',
        image_selector='img'
    )

def scrape_times_of_india_science():
    return scrape_news_categories(
        url="https://timesofindia.indiatimes.com/articlelist/msid--2128672765,curpg-3.cms",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='span.w_tle',
        headline_selector='a',
        link_selector='a',
        image_selector='img',
        image_attr='data-src'
    )

def scrape_india_today_health():
    return scrape_news_categories(
        url="https://www.indiatoday.in/health",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='article.B1S3_story__card__A_fhi',
        headline_selector='h2',
        link_selector='a',
        image_selector='img'
    )

def scrape_times_of_india_health():
    return scrape_news_categories(
        url="https://timesofindia.indiatimes.com/briefs/lifestyle",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        item_selector='div.brief_box',
        headline_selector='h2',
        link_selector='a',
        image_selector='img'
    )

def home(request):
    query = request.GET.get('q')
    times_of_india_news = scrape_times_of_india()
    ndtv_news = scrape_ndtv()
    the_hindu_news = scrape_the_hindu()

    combined_news_data = ndtv_news + times_of_india_news + the_hindu_news
    for news in combined_news_data:
        news['full_url'] = request.build_absolute_uri(news['url'])
    if query:
        combined_news_data = [news for news in combined_news_data if query.lower() in news['headline'].lower()]

    return render(request, 'hello.html', {'news_data': combined_news_data})

def national(request):
    query = request.GET.get('q')
    times_of_india_national = scrape_times_of_india_national()
    ndtv_news_national = scrape_ndtv_national()
    the_hindu_news_national = scrape_the_hindu_national()

    combined_news_data_national = ndtv_news_national + times_of_india_national + the_hindu_news_national
    for news in combined_news_data_national:
        news['full_url'] = request.build_absolute_uri(news['url'])
    if query:
        combined_news_data_national = [news for news in combined_news_data_national if query.lower() in news['headline'].lower()]

    return render(request, 'national.html', {'news_data': combined_news_data_national})


def international(request):
    query = request.GET.get('q')
    times_of_india_international = scrape_times_of_india_international()
    india_today_international = scrape_india_today_international()
    news18_international = scrape_news18_international()
    
    combined_news_data_international = times_of_india_international+india_today_international+news18_international
    for news in combined_news_data_international:
        news['full_url'] = request.build_absolute_uri(news['url'])
    

    if query:
        combined_news_data_international = [news for news in combined_news_data_international if query.lower() in news['headline'].lower()]

    return render(request, 'international.html', {'news_data': combined_news_data_international})

def sports(request):
    query = request.GET.get('q')
    times_of_india_sports = scrape_times_of_india_sports()
    india_today_sports = scrape_india_today_sports()
    the_hindu_news_sports = scrape_the_hindu_sports()

    combined_news_data_sports = times_of_india_sports + the_hindu_news_sports+india_today_sports
    for news in combined_news_data_sports:
        news['full_url'] = request.build_absolute_uri(news['url'])
    if query:
        combined_news_data_sports = [news for news in combined_news_data_sports if query.lower() in news['headline'].lower()]

    return render(request, 'sports.html', {'news_data': combined_news_data_sports})

def science(request):
    query = request.GET.get('q')
    india_today_science = scrape_india_today_science()
    the_hindu_news_science = scrape_the_hindu_science()
    times_of_india_science=scrape_times_of_india_science()
    combined_news_data_science = times_of_india_science+ the_hindu_news_science+ times_of_india_science
    for news in combined_news_data_science:
        news['full_url'] = request.build_absolute_uri(news['url'])
    if query:
        combined_news_data_science = [news for news in combined_news_data_science if query.lower() in news['headline'].lower()]
    
    return render(request, 'science.html', {'news_data': combined_news_data_science})


def health(request):
    query = request.GET.get('q')
    times_of_india_health = scrape_times_of_india_health()
    india_today_health = scrape_india_today_health()
    

    combined_news_data_health = times_of_india_health + india_today_health
    for news in combined_news_data_health:
        news['full_url'] = request.build_absolute_uri(news['url'])
    if query:
        combined_news_data_health = [news for news in combined_news_data_health if query.lower() in news['headline'].lower()]

    return render(request, 'health.html', {'news_data': combined_news_data_health}) 

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    send_mail(
        'Test Email',
        'Hello! This is a test email from Django.',
        settings.DEFAULT_FROM_EMAIL,
        ['akshitamonikachadha@gmail.com'],
        fail_silently=False,
    )

from django.conf import settings
from django.core.mail import send_mail
from app.utils import send_welcome_email




def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('signup')

        user = User.objects.create_user(username=username, password=password, email=email)

        # 💌 Send welcome email
        send_welcome_email(user.email, user.username)

        login(request, user)
        return redirect('home')

    return render(request, 'signup.html')
def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html')
    
    return render(request, 'login.html')
from django.contrib.auth import logout

def user_logout(request):
    logout(request)
    return redirect('home')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')
        
       
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email address.")
            return render(request, 'signup.html')
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.save()
            messages.success(request, "Signup successful! Please log in.")
            login(request, user)
            return redirect('login') 
        except IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                messages.error(request, 'Username or email already exists. Please choose a different one.')
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
        
    return render(request, 'signup.html')

from django.http import JsonResponse



class CustomLoginView(LoginView):
    def get_success_url(self):
        return self.request.GET.get('next', 'home')
    


@login_required
def profile(request):
    
    
    return render(request, 'profile.html')
    
