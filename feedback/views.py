from .models import Feedback
from .serializers import FeedbackSerializer,FeedbackStatsSerializer,WeeklyFeedbackSerializer
from rest_framework.viewsets import ModelViewSet,ViewSet
from rest_framework.response import Response

class FeedbackViewset(ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer

class FeedbackStatsViewSet(ModelViewSet):
    """
    ModelViewSet for feedback statistics using FeedbackStatsSerializer.
    Only supports list (GET) for aggregated stats.
    """
    serializer_class = FeedbackStatsSerializer
    queryset = Feedback.objects.none()  # Not actually used, since data comes from serializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['days'] = self.request.query_params.get('days')
        return context

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=Feedback())  # dummy instance
        return Response(serializer.data)

class FeedbackWeeklyStatsViewSet(ModelViewSet):
    queryset = Feedback.objects.none()
    serializer_class = WeeklyFeedbackSerializer
    authentication_classes = []
    permission_classes = []

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(None)
        return Response(serializer.data)