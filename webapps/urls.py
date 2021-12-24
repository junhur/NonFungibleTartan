"""webapps URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from non_fungible_tartan import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("login", views.login_action, name="login"),
    path("login-google", views.google_login_action, name="login_google"),
    path("logout", views.logout_action, name="logout"),
    path("register", views.register_action, name="register"),
    path("create-nft", views.create_nft_action, name="create_nft"),
    # path("get-auctions", views.get_auctions, name="get_auctions"),
    path("nft-details/<int:id>", views.nft_details_action, name="nft_details"),
    path("photo/<int:id>", views.get_photo, name="photo"),
    path("oauth/", include("social_django.urls", namespace="social")),
    path("profile/<int:user_id>", views.profile_action, name="profile"),
    path("profile/", views.profile_action, name="profile"),
    path("non_fungible_tartan/get-details", views.get_details_ajax, name="get-details"),
    path("add_power", views.add_buying_power_action, name="add_power"),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
