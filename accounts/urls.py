from django.urls import path
from . import views

urlpatterns = [
     path("register/", views.register, name="register"),
     path("login/", views.login, name="login"),
     path('logout/', views.logout, name='logout'),
     path("reset-password-verify-email/", views.reset_password_verify_email, name="verify_email"),
     path('reset-password-otp/', views.reset_password_verify_otp, name="verify_otp"),
]
