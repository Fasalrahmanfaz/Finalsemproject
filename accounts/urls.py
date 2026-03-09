from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/customer/', views.register_customer, name='register_customer'),
    path('register/band-manager/', views.register_band_manager, name='register_band_manager'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('set-new-password/', views.set_new_password, name='set_new_password'),
    path('profile/', views.profile_view, name='profile'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('delete-account/', views.delete_account, name='delete_account'),
]
