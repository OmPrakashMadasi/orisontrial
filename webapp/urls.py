from django.urls import path
from . import views
urlpatterns = [
    #registration paths starts here:-
    path('school/<slug:slug>/register/', views.register_user, name='register'),
    path('school/<slug:slug>/login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),

    path('', views.home, name='home'),

    path('about/',views.about, name='about'),
    path('school/<slug:slug>/products/',views.school_detail, name='school_detail'),
    path('school/<slug:slug>/search', views.search, name='search'),
    path('cart/', views.cart_summary, name='cart'),
]
