
from rest_framework import serializers
from datetime import datetime


class DaySerializer(serializers.Serializer):
    enterprise_name  = serializers.CharField(max_length=255)

class PerformanceSerializer(serializers.Serializer):
    enterprise_name  = serializers.CharField(max_length=255)
    year = serializers.IntegerField(default=datetime.today().year)
    month_number = serializers.IntegerField()
    week_number = serializers.IntegerField()

class PerformanceGoalSerializer(serializers.Serializer):
    enterprise_name  = serializers.CharField(max_length=255)
    year = serializers.IntegerField(default=datetime.today().year)
    month_number = serializers.IntegerField()
    week_number = serializers.IntegerField()

class PerformanceMonthSerializer(serializers.Serializer):
    enterprise_name  = serializers.CharField(max_length=255)
    year = serializers.IntegerField()
    month_number = serializers.IntegerField()
    
class PerformanceYearSerializer(serializers.Serializer):
    enterprise_name  = serializers.CharField(max_length=255)
    year = serializers.IntegerField()
    
    

class DayActivitiesSerializer(serializers.Serializer):
    enterprise_name  = serializers.CharField(max_length=255)
    date = serializers.DateField(input_formats=['%Y-%m-%d', '%m/%d/%Y'])

class JsonSerializer(serializers.Serializer):
    statistic = serializers.JSONField()
    

class UserStatisticsSerializer(serializers.Serializer):
    enterprise_name  = serializers.CharField(max_length=255)
    user_id = serializers.IntegerField()


class UserWeekStatisticsSerializer(serializers.Serializer):
    enterprise_name  = serializers.CharField(max_length=255)
    user_id = serializers.IntegerField()
    year = serializers.IntegerField(default=datetime.today().year)
    month_number = serializers.IntegerField()
    week_number = serializers.IntegerField()


class UserMonthStatisticsSerializer(serializers.Serializer):
    enterprise_name  = serializers.CharField(max_length=255)
    user_id = serializers.IntegerField()
    year = serializers.IntegerField(default=datetime.today().year)
    month_number = serializers.IntegerField()


class UserYearStatisticsSerializer(serializers.Serializer):
    enterprise_name  = serializers.CharField(max_length=255)
    user_id = serializers.IntegerField()
    year = serializers.IntegerField()
    


