from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = [
    path('users/', views.UsersList.as_view(), name="users-list"),
    path("user/<int:pk>/update/", views.UserUpdate.as_view(), name="user-update"),
    path("user/<int:pk>/detail/", views.UserDetail.as_view(), name="myuser-detail"),    
    path("user/<str:pk>/detail/", views.UserDetail.as_view(), name="myuser-detail"),


    # user sign up
    path('signup/admin/', views.SignupAdministrator.as_view(), name='signup-admin'),
    path('signup/verify/', views.SignupVerify.as_view(), name='signup-verify'), # for admin
    path('signup/verify2/', views.SignupVerifyEmployee.as_view(), name='signup-verify2'), # for employee
    path('signup/not_verified/', views.SignupNotVerifiedFrontEnd.as_view(),name='signup-not-verified'),
    path('signup/verified/', views.SignupVerifiedFrontEnd.as_view(),name='signup-verified'),
    path('check/employee/registration/verified', views.AddEmployeeVerified.as_view(), name='add-employee-verified'),
    path('check/employee/registration/not_verified', views.AddEmployeeNotVerified.as_view(), name='add-employee-not-verified'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    # password reset
    path('password/reset/', views.PasswordReset.as_view(), name='password-reset'),
    path('password/reset/verify/', views.PasswordResetVerify.as_view(), name='password-reset-verify'),
    path('password/reset/verified/', views.PasswordResetVerifiedFrontEnd.as_view(), name='password-reset-verified'),
    path('password/reset/not_verified/', views.PasswordResetNotVerifiedFrontEnd.as_view(), name='password-reset-not-verified'),
    # Change user Email
    path('email/change/', views.EmailChange.as_view(), name='email-change'),
    path('email/change/verify/', views.EmailChangeVerify.as_view(), name='email-change-verify'),
    path('email/change/verified/', views.EmailChangeVerifiedFrontEnd.as_view(), name='email-change-verified'),
    path('email/change/not_verified/', views.EmailChangeNotVerifiedFrontEnd.as_view(), name='email-change-not-verified'),
    # administrator
    path("admin/list/", views.AdministratorList.as_view(), name="list of all administrator"),
    path("admin/<int:pk>/detail/", views.AdministratorDetails.as_view(), name="administrator details"),
    path("admin/<int:pk>/update/", views.AdministratorUpdate.as_view(),name="update administrator"),
    path("admin/<int:pk>/delete/", views.AdministratorDelete.as_view(),name="delete administrator"),
    # Enterprise
    path("enterprise/create/", views.EnterpriseCreateView.as_view(),name="create Enterprise"),
    path("enterprise/list/", views.EnterpriseList.as_view(),name="list of all Enterprise"),
    path("enterprise/<int:pk>/detail/", views.EnterpriseDetails.as_view(), name="enterprise-detail"),
    path("enterprise/<int:pk>/update/", views.EnterpriseUpdate.as_view(), name="update Enterprise"),
    path("enterprise/<int:pk>/delete/", views.EnterpriseDelete.as_view(), name="delete Enterprise"),
    path('enterprise/employee/list/', views.EnterpriseEmployeeList.as_view(), name='employee-list'),
    path('enterprise/employee/create/', views.SignupEmployee.as_view(), name='signup-employee'),
    path('enterprise/category/list/', views.EnterpriseCategoryList.as_view(), name='enterprise_categories'),
    path('enterprise/change/administrator/', views.ChangePdgOrAdmin.as_view(), name='change-enterprise-administrator'),
    path('enterprise/employee/deactivate/', views.DeactivateEmployee.as_view(), name='deactivate_employee'),
    path('enterprise/employee/activate/', views.ActivateEmployee.as_view(), name='deactivate_employee'),
    path('enterprise/set/employee_category/', views.EnterpriseEmployeeCategory.as_view(), name="set-employee-enterprise-category"),
    path('enterprise/set/employee_admins/', views.EnterpriseSetEmployeeAdmin.as_view(), name="enterprise-set-employee-admins"),
    path('enterprise/remove/employee_admins/', views.EnterpriseRemoveEmployeeAdmin.as_view(), name="enterprise-remove-employee-admins"),
    path('enterprise/change/employee/salary/', views.EmployeeProfileChangeSalary.as_view(), name="change-employee-salary"),
    # Category
    path("enterprise/category/create/", views.CategoryCreateView.as_view(),name="create Category"),
    path("category/list/", views.CategoryList.as_view(), name="list-of-all-Category"),
    path("enterprise/category/<int:pk>/detail/", views.CategoryDetails.as_view(), name="category-detail"),
    path("enterprise/category/<int:pk>/update/",  views.CategoryUpdate.as_view(), name="update-Category"),
    path("enterprise/category/<int:pk>/delete/", views.CategoryDelete.as_view(), name="delete-Category"),
    # Employee
    path("employee/list/", views.EmployeeList.as_view(), name="list of all employee"),
    path("employee/<int:pk>/detail/", views.EmployeeDetails.as_view(), name="employee-detail"),
    path("employee/<int:pk>/update/", views.EmployeeUpdate.as_view(), name="update employee"),
    path("employee/<int:pk>/delete/", views.EmployeeDelete.as_view(), name="delete employee"),
    # employee profile
    path("employee_profile/list/", views.EmployeeProfileList.as_view(), name="employee-profile-list"),
    path("employee_profile/<int:pk>/detail/",views.EmployeeProfileRetrieveUpdate.as_view(), name="update-employee-profile"),
    # administrator profile
    path("administrator_profile/list/", views.AdministratorProfileList.as_view(),  name="administrator-profile-list"),
    # path("administrator_profile/<int:pk>/update/", views.AdministratorProfileUpdate.as_view(), name="update administrator profile"),
    path("administrator_profile/<str:user>/detail/", views.AdministratorProfileRetrieve.as_view(), name="administrator-detail"),
]

# urlpatterns = format_suffix_patterns(urlpatterns)
