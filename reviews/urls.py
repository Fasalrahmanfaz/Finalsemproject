from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('rate/<int:booking_pk>/', views.submit_rating, name='submit_rating'),
    path('rate-band/<int:band_pk>/', views.rate_band, name='rate_band'),
    path('<int:pk>/delete/', views.delete_review, name='delete_review'),
    path('band/<int:band_pk>/', views.band_reviews, name='band_reviews'),
]
