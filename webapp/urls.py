from django.urls import path
from .views import cart_count_api
from . import views
urlpatterns = [
    #registration paths starts here:-
    path('school/<slug:slug>/register/', views.register_user, name='register'),
    path('school/<slug:slug>/login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),

    path('', views.home, name='home'),

    path('about/',views.about, name='about'),
    path('school/<slug:slug>/products/',views.school_detail, name='school_detail'),
    path('school/<slug:slug>/cart/', views.cart_summary, name='cart_summary'),
    path("school/<slug:slug>/checkout/", views.checkout, name="checkout"),
    path('update-cart/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/count/', cart_count_api, name='cart_count_api'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
]
