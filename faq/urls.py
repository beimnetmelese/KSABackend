# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FAQViewset

router = DefaultRouter()
router.register(r'faq', FAQViewset)

urlpatterns = [
    path('', include(router.urls)),
]