from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from reservations.views import court_reserve_view

urlpatterns = [
    path('', views.home, name='home'),
    path('courts/', views.court_list, name='court_list'),
    path('courts/<int:court_id>/', views.court_detail, name='court_detail'),
    path('courts/<int:court_id>/reserve/', court_reserve_view, name='reservation_create'),
    path('reservations/<int:reservation_id>/cancel/', views.cancel_reservation, name='reservation_cancel'),
    path('payments/', include('payments.urls', namespace='web_payments')),  # Web routes for payments
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_edit'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('terms/', views.terms, name='terms'),
    
    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]
