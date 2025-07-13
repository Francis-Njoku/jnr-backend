from django.urls import path
from .views import RegisterIssuerView, ResendVerificationEmailView, VerifiedUserAPIView, ApproveUserAPIView, UserDetailAPIView, UserListAPIView, LoginViewSet, RefreshViewSet, RegisterReferralView, Invite, RegisterView, LoginView2, LogoutAPIView, LoadUserView, SetNewPasswordAPIView, VerifyEmail, LoginAPIView, PasswordTokenCheckAPI, RequestPasswordResetEmail
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from . import views


urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    #path('investor/', views.UserInvestorDetailAPIView.as_view(), name="user-investor"),
    #path('initial-interest/', views.InitialInvestmentView.as_view(), name="initial-interest"),
    #path('initial-interest/update/<int:id>', views.UpdateInitialInvestmentView.as_view(), name="update-initial-interest"),
    #path('register/referral/', RegisterReferralView.as_view(),
    #     name="register-referral"),
    #path('register/issuer/', RegisterIssuerView.as_view(), name="register-issuer"),
    #path('login2/', LoginViewSet, name='auth-login'),
    #path('refresh/', RefreshViewSet, name='auth-refresh'),
    path('login/', LoginAPIView.as_view(), name="login"),
    path('invite/', Invite.as_view(), name="get-referral"),
    path('sign-in/', LoginView2.as_view(), name="sign-in"),
    path('logout/', LogoutAPIView.as_view(), name="logout"),
    path('loaduser/', LoadUserView.as_view(), name="load-user"),
    path('email-verify/', VerifyEmail.as_view(), name="email-verify"),
    #path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('request-reset-email/', RequestPasswordResetEmail.as_view(),
         name="request-reset-email"),
    path('resend-email-verification/', ResendVerificationEmailView.as_view(), name='resend-email-verification'),
    path('password-reset/<uidb64>/<token>/',
         PasswordTokenCheckAPI.as_view(), name='password-reset-confirm'),
    path('password-reset-complete', SetNewPasswordAPIView.as_view(),
         name='password-reset-complete'),
    path('list-users/', UserListAPIView.as_view(), name="user-details"),
    path('user/<int:id>', UserDetailAPIView.as_view(), name="user-data"),
    path('approve/<int:id>', ApproveUserAPIView.as_view(), name="approve-data"),
    path('verify/<int:id>', VerifiedUserAPIView.as_view(), name="verify-user"),
    path('export/users/', views.ExportUserAPIView.as_view(),
         name="export-user-data"),
    path('export/users/pdf/', views.ExportUsersPDFAPIView.as_view(),
         name="export-user-data"),




]
