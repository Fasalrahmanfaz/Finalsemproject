from django.urls import path
from . import views

app_name = 'enquiries'

urlpatterns = [
    path('send/<int:band_id>/', views.submit_enquiry, name='submit_enquiry'),
    path('success/<int:pk>/', views.enquiry_success, name='enquiry_success'),
    path('my-enquiries/', views.my_enquiries, name='my_enquiries'),
    path('<int:pk>/', views.enquiry_detail, name='enquiry_detail'),
    path('<int:pk>/cancel/', views.cancel_enquiry, name='cancel_enquiry'),
    path('<int:pk>/message/', views.send_enquiry_message, name='send_message'),
    # Band Manager
    path('manage/', views.manager_enquiry_list, name='manager_enquiry_list'),
    path('manage/<int:pk>/accept/', views.accept_enquiry, name='accept_enquiry'),
    path('manage/<int:pk>/reject/', views.reject_enquiry, name='reject_enquiry'),
    # AJAX
    path('pricing-estimate/', views.pricing_estimator_ajax, name='pricing_estimator'),
]
