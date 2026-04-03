from django.urls import include, path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('bookmarks/toggle/', views.toggle_bookmark, name='toggle_bookmark'),
    path('bookmarks/<int:bookmark_id>/update/', views.update_bookmark, name='update_bookmark'),
    path('refresh-news/', views.refresh_news, name='refresh_news'),
    path('send-digest/', views.send_digest_now, name='send_digest_now'),
    path('national/', views.national, name='national'),
    path('international/', views.international, name='international'),
    path('sports/', views.sports, name='sports'),
    path('science/', views.science, name='science'),
    path('health/', views.health, name='health'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.user_signup, name='signup'),
    path('', views.home, name='home'),
]

