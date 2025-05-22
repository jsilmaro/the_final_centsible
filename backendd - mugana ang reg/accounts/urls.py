from django.urls import path
from .views import RegisterView, LoginView, get_user, update_profile

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("user/", get_user, name="user"),  # Endpoint for fetching user details
    path("profile/update/", update_profile, name="update_profile"),

]
