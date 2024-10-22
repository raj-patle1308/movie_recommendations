from django.urls import path
from . import views
from .views import run_chatbot

urlpatterns = [
    path('run-chatbot/', run_chatbot, name='run_chatbot'),
    path('', views.index, name='index'),
    path('signup/', views.signUp, name='signup'),
    path('login/', views.Login, name='login'),
    path('logout/', views.Logout, name='logout'),
    path('<int:movie_id>/', views.detail, name='detail'),
    path('watch/', views.watch, name='watch'),
    path('romance/', views.romance, name='Romance'),
    path('action/', views.action, name='Action'),
    path('recommend/', views.recommend, name='recommend'),


]