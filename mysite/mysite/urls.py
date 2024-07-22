"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from charts.views import publish_topic, get_filenames, get_file_data, test_redis_connection, test_ros_bridge_publish

urlpatterns = [
    path('test-redis/', test_redis_connection),
    path('test-ros-brdige/', test_ros_bridge_publish),
    path('get_filenames/', get_filenames, name='get_filenames'),
    path('get_file_data/<str:filename>/', get_file_data, name='get_file_data'), 
    # path('admin/', admin.site.urls),
    path('publish/', publish_topic, name='publish_topic'),
]
