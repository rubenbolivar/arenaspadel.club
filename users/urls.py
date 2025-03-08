from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'users'

router = DefaultRouter()
router.register(r'api/', views.UserViewSet)

urlpatterns = [
    # Template URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    
    # API URLs
    path('api/register/', views.UserRegistrationView.as_view(), name='api_register'),
    path('api/login/', views.UserLoginView.as_view(), name='api_login'),
    path('api/logout/', views.UserLogoutView.as_view(), name='api_logout'),
    path('api/profile/', views.UserProfileView.as_view(), name='api_profile'),
    path('api/profile/update/', views.UserProfileUpdateView.as_view(), name='api_profile_update'),
]

urlpatterns += router.urls
