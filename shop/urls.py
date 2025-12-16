"""
# shop/urls.py
"""

from django.urls import path
from . import views


urlpatterns = [
    path('home/', views.HomeView.as_view()),

    path('products/', views.ProductsView.as_view()),
    path('product/<int:pk>/', views.ProductView.as_view()),

    path('ingredients/', views.IngredientsView.as_view())
]