from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    #path('about/', views.about, name='about'),
    #path('contact/', views.contact, name='contact'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('claims/new/', views.file_claim, name='file_claim'),
    path('policies/new/', views.add_policy, name='add_policy'),
    path('profile/', views.profile, name='profile'),
]