from django.urls import path
from . import views

app_name = 'bands'

urlpatterns = [
    path('explore/', views.explore, name='explore'),
    path('<int:pk>/', views.band_profile_detail, name='profile_detail'),
    path('dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('create/', views.create_band_profile, name='create_profile'),
    path('edit/', views.edit_band_profile, name='edit_profile'),
    # Packages
    path('packages/', views.manage_packages, name='manage_packages'),
    path('packages/add/', views.add_package, name='add_package'),
    path('packages/<int:pk>/edit/', views.edit_package, name='edit_package'),
    path('packages/<int:pk>/delete/', views.delete_package, name='delete_package'),
    # Gallery
    path('gallery/', views.manage_gallery, name='manage_gallery'),
    path('gallery/upload/', views.upload_gallery_image, name='upload_gallery'),
    path('gallery/<int:pk>/delete/', views.delete_gallery_image, name='delete_gallery'),
    path('gallery/reorder/', views.reorder_gallery, name='reorder_gallery'),
    # Availability
    path('availability/', views.manage_availability, name='manage_availability'),
    path('availability/calendar/<int:band_id>/', views.get_availability_calendar_ajax, name='availability_calendar'),
    # AJAX
    path('check-availability/', views.check_availability_ajax, name='check_availability'),
    # Delete
    path('delete/', views.delete_band, name='delete_band'),
]
