from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeedbackViewset,FeedbackStatsViewSet,FeedbackWeeklyStatsViewSet

router = DefaultRouter()
router.register(r'feedback', FeedbackViewset)
router.register(r'feedbackstats', FeedbackStatsViewSet, basename='feedbackstats')
router.register(r'feedbackstats/weekly', FeedbackWeeklyStatsViewSet, basename='feedback-weekly-stats')

urlpatterns = [
    path('', include(router.urls)),
    
]
