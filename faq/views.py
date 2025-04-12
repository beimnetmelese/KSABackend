# views.py
from .models import FAQ
from .serializers import FQASerializer
from rest_framework.viewsets import ModelViewSet

class FAQViewset(ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FQASerializer

