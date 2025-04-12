from rest_framework import serializers
from .models import FAQ
from django.utils.timezone import now, timedelta


class FQASerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
        read_only_fields = ('created_at',)