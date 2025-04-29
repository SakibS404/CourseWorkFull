#import relevant extensions
from django.contrib import admin
from django.urls import path, include
from register1 import views as v1

#creates the url path to each webpage
urlpatterns = [
    path('database/', admin.site.urls),
    path('', include('register1.urls')),  # Include register1 URLs
]

