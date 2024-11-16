from rest_framework import serializers
from .models import  Goal, Activities, Report, ReportStatus
from rest_framework import validators, reverse
from django.contrib.auth import get_user_model

"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    FILE VALIDATOR
"""


class AllowedFileTypeValidator:
    def __call__(self, value):

        if not hasattr(value, 'name'):
            raise serializers.ValidationError("Invalid file provided.")

        allowed_extensions = [
            'pdf', 'txt', 'data', 'jpeg', 'jpg', 'svg', 'ai', 'eps', 'tiff', 
            'psd', "mov", "avi", "gif", 'zip', 'png', 'docx', 'exe', 'mp4', 
            'mp3', 'm4a', 'xls', 'xlsx', 'html', 'py', 'js',
        ]

        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"Invalid file type. Allowed extensions are: {', '.join(allowed_extensions)}")


"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    GOAL, ACTIVITIES, REPORT
"""

class GoalSerializer(serializers.ModelSerializer):
    # enterprise_name = serializers.CharField(max_length = 255, write_only=True)
    attached_file = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file1 = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file2 = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    employee_ids = serializers.CharField(write_only=True)
    class Meta:
        model = Goal
        fields = ("pk", "employee_ids",  "enterprise", "users_in_charge", "title", "description", "starting_date", "ending_date", "attached_file", "attached_file1", "attached_file2", "bonus", "repeat", "important")

    def create(self, validated_data):
        employee_ids = validated_data.pop("employee_ids")
        return super().create(validated_data)
    
class GoalUpdateSerializer(serializers.ModelSerializer):
    # enterprise_name = serializers.CharField(max_length = 255, write_only=True)
    attached_file = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file1 = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file2 = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    class Meta:
        model = Goal
        fields = ("pk",  "enterprise", "title", "description", "starting_date", "ending_date", "attached_file", "attached_file1", "attached_file2", "bonus", "repeat", "important")

    

class GoalSetUserInChargeOfGoalSerializer(serializers.Serializer):
    users = serializers.CharField(max_length=255)
    goal_id = serializers.IntegerField()


class GoalSetGoalManagerSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    goal_id = serializers.IntegerField()
 

class GoalSerializerList(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="goal-detail", lookup_field="pk")
    attached_file = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file1 = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file2 = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    
    class Meta:
        model = Goal
        fields = ("__all__")

class GoalListSerializer(serializers.Serializer):
    enterprise_name = serializers.CharField(max_length=255)
    

class ActivitiesSerializer(serializers.HyperlinkedModelSerializer):
    " Activity Serializer class"
    goal_id = serializers.IntegerField(write_only=True)
    employee_id = serializers.IntegerField(write_only=True)
    attached_file = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file1 = serializers.FileField(allow_null=True  ,validators = [AllowedFileTypeValidator()])
    attached_file2 = serializers.FileField(allow_null=True  ,validators = [AllowedFileTypeValidator()])
    class Meta:
        model = Activities
        fields = ("pk", "goal_id", "employee_id", "title", "description", "starting_date", "ending_date", "repeat", "attached_file", "attached_file1", "attached_file2", "bonus")

    def create(self, validated_data):
        goal_id = validated_data.pop('goal_id')
        employee_id = validated_data.pop('employee_id')
        obj = super().create(validated_data)
        return obj
    
class ActivitiesAddMulUsersSerializer(serializers.ModelSerializer):
    employees = serializers.JSONField(write_only=True)

    
class ActivitiesCreateMulSerializer(serializers.ModelSerializer):
    attached_file = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file1 = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file2 = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    employee_ids = serializers.CharField(write_only=True)
    class Meta:
        model = Activities
        fields = ( "employee_ids", "goal", "title", "description", "created_by", "repeat", "starting_date", "ending_date", "attached_file", "attached_file1", "attached_file2", "bonus")

    def create(self, validated_data):
        employee_ids = validated_data.pop("employee_ids")
        return super().create(validated_data)


class ActivitiesListSerializer(serializers.HyperlinkedModelSerializer):
    url= serializers.HyperlinkedIdentityField(view_name="activities-detail", lookup_field="pk")
    class Meta:
        model = Activities
        fields = ("__all__")


class  ActivitiesDeleteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Activities
        fields = ['status',]


class GoalActivitiesSerializer(serializers.Serializer):
    enterprise_name = serializers.CharField(max_length=255)
    goal_id = serializers.IntegerField()

class ActivityMulUpdateSerializer(serializers.HyperlinkedModelSerializer):
    attached_file = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file1 = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])
    attached_file2 = serializers.FileField(allow_null=True ,validators = [AllowedFileTypeValidator()])

    class Meta:
        model = Activities
        fields =[ "goal", "title",  "description", "starting_date", "ending_date", "attached_file", "attached_file1", "attached_file2", "bonus", "repeat"]


    
class ActivityAddUserInChargeSerializer(serializers.Serializer):
    activity_id = serializers.IntegerField()
    users = serializers.CharField(max_length=255)

class ReportSerializer(serializers.HyperlinkedModelSerializer):
    report = serializers.FileField(validators=[AllowedFileTypeValidator()])
    class Meta:
        model = Report
        fields = ("pk", "report",  "option", "goal", "activity" )

class ReportEmployeeUpdateSerializer(serializers.ModelSerializer):
    report = serializers.FileField(validators=[AllowedFileTypeValidator()])
    class Meta:
        model = Report
        fields = ("pk", "report", "submit_late")

class ReportDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["is_deleted"]

class ReportActivityCreateSerializer(serializers.ModelSerializer):
    report = serializers.FileField(validators=[AllowedFileTypeValidator()])
    # option = serializers.CharField(default="A")
    class Meta:
        model = Report
        fields = ["report", "activity"]


class ReportGoalCreateSerializer(serializers.HyperlinkedModelSerializer):
    report = serializers.FileField(validators=[AllowedFileTypeValidator()])
    # option = serializers.CharField(default="G")
    class Meta:
        model = Report
        fields = ["report",  "goal", "submit_by", "repeat_option", "repetition_num"]


class ReportListSerializer(serializers.HyperlinkedModelSerializer):
    report = serializers.FileField(validators=[AllowedFileTypeValidator()])
    url = serializers.HyperlinkedIdentityField(view_name="report-detail", lookup_field="pk")
    
    class Meta:
        model = Report
        fields = "__all__"
 

class TasksUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model= Report
        fields = ["pk", "rate", "comment" , "rated_by" , "report_status"]

class TasksListSerializer(serializers.Serializer):
    enterprise_name = serializers.CharField(max_length=255)


class GoalActivityReportListSerializer(serializers.Serializer):
    target_id = serializers.IntegerField()
    enterprise_name = serializers.CharField(max_length=255)


class TasksRateResetSerializer(serializers.ModelSerializer):
    report_id = serializers.IntegerField(write_only=True)
    retry = serializers.BooleanField(write_only=True)
    class Meta:
        model = Report
        fields = [ 'pk',"report_id", "rate", "comment" , "retry"]

    def create(self, validated_data):
        report_id = validated_data.pop('report_id')
        retry = validated_data.pop("retry")
        obj = self.super().create(validated_data)
        return obj
    

class TasksRateResetSerializer2(serializers.ModelSerializer):
    report_id = serializers.IntegerField(write_only=True)
    retry = serializers.BooleanField(write_only=True)
    class Meta:
        model = Report
        fields = [ 'pk',"report_id", "rate", "rated_by", "report_status", "comment" , "retry"]

    def create(self, validated_data):
        report_id = validated_data.pop('report_id')
        retry = validated_data.pop("retry")
        obj = self.super().create(validated_data)
        return obj
    
class TaskUpdate2Serializer(serializers.Serializer):
    pk = serializers.IntegerField()
    rate = serializers.IntegerField()
    comment = serializers.CharField(max_length=10000)


class ActivitySerializerLink(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="activity-detail", lookup_field="pk")
    class Meta:
        model=Activities
        fields =["url","title","description","starting_date", "ending_date", "bonus"]

class GoalSerializerLink(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="goal-detail", lookup_field="pk")
    class Meta:
        model=Goal
        fields =["url","title",  "description", "starting_date", "ending_date", "bonus", "important"]

