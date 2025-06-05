from django.urls import include, path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    

    
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

