from rest_framework import serializers
from .models import Feedback
from datetime import date
from collections import defaultdict
from django.utils.timezone import now, timedelta


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('created_at',)



class FeedbackStatsSerializer(serializers.ModelSerializer):
    total_feedbacks = serializers.SerializerMethodField()
    total_positive = serializers.SerializerMethodField()
    total_negative = serializers.SerializerMethodField()
    sector_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = ['total_feedbacks', 'total_positive', 'total_negative', 'sector_breakdown']

    def get_filtered_queryset(self):
        request = self.context.get('request')
        days = self.context.get('days')

        queryset = Feedback.objects.all()
        if days:
            try:
                days = int(days)
                since = now() - timedelta(days=days)
                queryset = queryset.filter(feedback_time__gte=since)
            except (TypeError, ValueError):
                pass
        return queryset

    def get_total_feedbacks(self, obj):
        return self.get_filtered_queryset().count()

    def get_total_positive(self, obj):
        return self.get_filtered_queryset().filter(feedback_type__iexact='positive').count()

    def get_total_negative(self, obj):
        return self.get_filtered_queryset().filter(feedback_type__iexact='negative').count()

    def get_sector_breakdown(self, obj):
        sectors = ['Customer Service', 'Housekeeping', 'Food & Beverage', 'Maintenance', 'General']
        data = {}
        qs = self.get_filtered_queryset()
        for sector in sectors:
            sector_qs = qs.filter(sector=sector)
            data[sector] = {
                "total": sector_qs.count(),
                "positive": sector_qs.filter(feedback_type__iexact='positive').count(),
                "negative": sector_qs.filter(feedback_type__iexact='negative').count(),
            }
        return data


class WeeklyFeedbackSerializer(serializers.ModelSerializer):
    weekly_stats = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = ['weekly_stats']

    def get_weekly_stats(self, obj):
        today = date.today()
        seven_days_ago = today - timedelta(days=6)

        feedbacks = Feedback.objects.filter(date__range=[seven_days_ago, today])
        stats_by_day = defaultdict(lambda: {'positive': 0, 'negative': 0})

        for fb in feedbacks:
            day = fb.date.strftime('%Y-%m-%d')
            sentiment = fb.feedback_type.lower()
            if sentiment in stats_by_day[day]:
                stats_by_day[day][sentiment] += 1

        # Return list sorted by day
        return [
            {'date': day, 'positive': stats['positive'], 'negative': stats['negative']}
            for day, stats in sorted(stats_by_day.items())
        ]