from rest_framework import serializers, validators
from .models import (
    Enterprise, 
    Category, 
    EmployeeProfile, 
    AdministratorProfile, 
    Employee,
  
)

from django.contrib.auth import get_user_model

User = get_user_model()


class AllowedImageFileTypeValidator:
    """ Image file validator"""
    def __call__(self, value):
        allowed_extensions = ['jpeg', 'jpg', 'png']
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"Invalid file type. Allowed extensions are: {', '.join(allowed_extensions)}")

class AllowedFileTypeValidator:
    """ File validator"""
    def __call__(self, value):
        allowed_extensions = ['pdf', 'docx',]
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"Invalid file type. Allowed extensions are: {', '.join(allowed_extensions)}")



"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    User, ENTERPRISE, CATEGORY, EMPLOYEE Registrations, EmployeeProfile, AdministratorProfile, sign_up, login,
    password reset, password verification, password change, email change, email change verification, 
"""
class UserDetailSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="myuser-detail", lookup_field='pk')
    class Meta:
        model = User
        fields = ["url", "pk", "first_name", "last_name", "picture", "cv", "role"]
class SignupSerializer(serializers.ModelSerializer):
    """
    Don't require email to be unique so visitor can signup multiple times,
    if misplace verification email.  Handle in view.
    """
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')


class SignupEmployeeSerializer(serializers.ModelSerializer):
    """
    Don't require email to be unique so visitor can signup multiple times,
    if misplace verification email.  Handle in view.
    """
    enterprise_name = serializers.CharField(write_only=True)
    user_email = serializers.EmailField(write_only=True)
    class Meta:
        model = User
        fields = ('user_email', 'first_name', 'last_name',  'enterprise_name')

    # override the create function to make sure that the field user_email and enterprise_name is not save in the database
    def create(self, validated_data):
        print(validated_data)
        enterprise_name = validated_data.pop('enterprise_name')
        user_email = validated_data.pop('user_email')
        # print(enterprise_name)
        # print(validated_data)
        # return Product.objects.create(**validated_data )
        obj = super().create(validated_data)
        return obj


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128)
    # class Meta:
    #     # model = User
    #     fields = ('email', 'password', )


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=255)


class PasswordResetVerifiedSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40)
    password = serializers.CharField(max_length=128)


class PasswordChangeSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128)


class EmailChangeSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)


class EmailChangeVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)


class DeactivateEmployeeSerializer(serializers.Serializer):
    employee_email = serializers.EmailField(max_length=255)
    enterprise_name = serializers.CharField(max_length=255)


class UserSerializer(serializers.ModelSerializer):
    picture = serializers.ImageField(allow_null=True , validators=[AllowedImageFileTypeValidator()])
    url = serializers.HyperlinkedIdentityField(view_name="myuser-detail", lookup_field='pk')
    class Meta:
        model = User
        fields = '__all__'



class UserUpdate2Serializer(serializers.ModelSerializer):
    enterprise_name = serializers.CharField(write_only=True)
    cv = serializers.FileField(allow_null=True, validators = [AllowedFileTypeValidator()])
    picture = serializers.ImageField(allow_null = True, validators = [AllowedImageFileTypeValidator()])
    url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = User
        fields = ["pk", "url", "enterprise_name", "first_name", "last_name", "cv", "recovery_email", 'picture']
    
    def get_url(self, obj):
        return f""
    
    def create(self, validated_data):
        enterprise_name = validated_data.pop("enterprise_name")
        return super().create(validated_data)

class EnterpriseSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="enterprise-detail", lookup_field="pk")
    class Meta:
        model = Enterprise
        fields = "__all__"


class EnterpriseCreateSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(allow_null=True ,validators= [AllowedImageFileTypeValidator()])
    class Meta:
        model  = Enterprise
        fields = ['name', 'country', 'city', 'location', 'logo',  'admin_salary', 'PDG',]




class UserUpdateSerializer(serializers.ModelSerializer):
    picture = serializers.ImageField(allow_null=True ,validators= [AllowedImageFileTypeValidator()])
    cv = serializers.FileField(allow_null=True, validators= [AllowedFileTypeValidator()])
    class Meta:
        model = get_user_model()
        fields = ['picture', 'first_name', "last_name", "cv"]



class EnterpriseSetEmployeeAdminSerializer(serializers.Serializer):
    """
        employees_list structure
        employees_list = {
            "employees": [<list of employee emails>]
        }

    """
    enterprise_name = serializers.CharField(max_length=255)
    employees_list = serializers.JSONField()



class EnterpriseUpdateSerializer(serializers.ModelSerializer):
    # do this if you don't want a field to be change during the update operation
    # code = serializers.CharField(max_length=255, read_only=True)
    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)

    #     # Check if the read_only_field is already set
    #     if instance.code:
    #         representation['code'] = instance.code

    #     return representation

    class Meta:
        model = Enterprise
        fields = ('name','city','country', 'location','logo',)


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="category-detail", lookup_field="pk")
    class Meta:
        model = Category
        fields = "__all__"

class CategoryEnterpriseSerializer(serializers.ModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name="category-detail", lookup_field="pk")
    class Meta:
        model = Category
        fields = "__all__"


class CategoriesPerEnterpriseSerializer(serializers.Serializer):
    enterprise_code = serializers.CharField(max_length=168)


class EmployeeProfileSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="update-employee-profile", lookup_field="pk")
    class Meta:
        model = EmployeeProfile
        fields =("__all__")
    
    


class AdministratorProfileSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="administrator-detail", lookup_field='user')
    class Meta:
        model = AdministratorProfile
        fields = '__all__'


class ChangePdgOrAdministratorSerializer(serializers.Serializer):
    new_administrator_email = serializers.EmailField(max_length=255)
    enterprise_name = serializers.CharField(max_length=255)


class EmployeeListSerializer(serializers.Serializer):
    enterprise_code = serializers.EmailField(max_length=255)
    full_name = serializers.CharField(max_length=300)
    dateOfRegistration = serializers.DateTimeField()
    status = serializers.IntegerField()
    category = serializers.CharField(max_length=255)
    salary = serializers.DecimalField(max_digits=10, decimal_places=3)


class EmployeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']
        

class EmployeeCategorySerializer(serializers.Serializer):
    employee_email = serializers.EmailField(max_length=255)
    category = serializers.CharField(max_length=200)
    enterprise_name = serializers.CharField(max_length=255)

class EmployeeProfileChangeSalarySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    enterprise_name = serializers.CharField(max_length=255)
    salary = serializers.DecimalField(max_digits=10, decimal_places=3)


class EnterpriseEmployeeListSerializer(serializers.Serializer):
    enterprise_name = serializers.CharField(max_length=255)