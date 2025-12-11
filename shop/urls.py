"""
# shop/urls.py
"""

from django.urls import path
from . import views


urlpatterns = [
    path('products/', views.ProductsView.as_view()),
    path('ingredients/', views.IngredientsView.as_view())
]