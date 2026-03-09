from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/<int:pk>/toggle/', views.admin_toggle_user, name='admin_toggle_user'),
    path('admin-panel/bands/', views.admin_bands, name='admin_bands'),
    path('admin-panel/bands/<int:pk>/approve/', views.admin_approve_band, name='admin_approve_band'),
    path('admin-panel/bands/<int:pk>/toggle/', views.admin_toggle_band, name='admin_toggle_band'),
    path('admin-panel/enquiries/', views.admin_enquiries, name='admin_enquiries'),
    path('admin-panel/reviews/', views.admin_reviews, name='admin_reviews'),
]
