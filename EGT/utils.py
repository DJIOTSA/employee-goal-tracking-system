
from django.contrib.auth.models import Group
from django.db.models import Q
from django.contrib.auth import get_user_model

from django.conf import settings

from EGT.models import (
    AdministratorProfile, 
    EmployeeProfile, 
    Enterprise, 
    Category,
    MyUser,
    Status,
    UserRecords,
    ActionType,
    Employee,
    send_multi_format_email
    
)

import logging, datetime
import json
from EGT.exceptions import (
    AdministratorProfileDoesNotExistError,
    AdministratorProfileDoesNotExistError,
    EmployeeProfileDoesNotExistError,
    InvalidStatusError,
    InvalidUserRoleError,
    UserDoesNotExist,
)

# Create a logger object
logger = logging.getLogger(__name__)
# Set the logger's level to DEBUG or another appropriate level
logger.setLevel(logging.DEBUG)
# Create a formatter to specify the format of log messages
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Add the formatter to the logger
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# without function parameter type

def create_group(group_name):
    """
    Create a new group if it doesn't exist, otherwise return the existing group.
    """
    try:
        if not Group.objects.filter(name=group_name).exists():
            return Group.objects.create(name=group_name)
        else:
            return Group.objects.get(name=group_name)
    except Exception as e:
        logging.error(f"Error creating group: {e}")
        return False
        

def add_user_to_group(user, group_name):
    """
    Add a user to a specific group if both user and group exist.
    """
    try:
        user_instance = get_user_model().objects.get(email=user.email)
        group_instance = Group.objects.get(name=group_name)
        user_instance.groups.add(group_instance)
        user_instance.save()
        return user_instance
    except Group.DoesNotExist:
        logging.error(f"Group with name '{group_name}' does not exist.")
        return False
    except get_user_model().DoesNotExist:
        logging.error(f"User with email '{user.email}' does not exist.")
        return False
    except Exception as e:
        logging.error(f"Error adding user to group: {e}")
        return False


def remove_user_from_group(user, group_name):
    """
    Remove a user from a specific group if both user and group exist.
    """
    try:
        user_instance = get_user_model().objects.get(email=user.email)
        group_instance = Group.objects.get(name=group_name)
        user_instance.groups.objects.remove(group_instance)
        user_instance.save()
        return user_instance
    except Group.DoesNotExist:
        logging.error(f"Group with name '{group_name}' does not exist.")
        return False
    except get_user_model().DoesNotExist:
        logging.error(f"User with email '{user.email}' does not exist.")
        return False
    except Exception as e:
        logging.error(f"Error removing user from group: {e}")
        return False


def change_user_enterprise_status(user, enterprise_name, new_status):
    """
    This function changes the user's enterprises_status for both employees and administrators.
    """
    # Check if the user exists
    try:
        # Retrieve the user object using the provided email address of the user parameter
        user_object = get_user_model().objects.get(email=user.email)
    except get_user_model().DoesNotExist:
        # If the user doesn't exist, raise an appropriate exception
        # raise UserDoesNotExistError(f"User with email {user.email} does not exist.")
        raise UserDoesNotExist(f"User with email {user.email} does not exist.")

    # Check the user's role
    if user_object.role == 'ADMINISTRATOR':
        try:
            # Retrieve the administrator profile associated with the user
            admin_profile = AdministratorProfile.objects.get(user=user_object)
        except AdministratorProfile.DoesNotExist:
            # If the administrator profile doesn't exist, raise an appropriate exception
            raise AdministratorProfileDoesNotExistError(f"Administrator profile for user {user.email} does not exist.")

        # Set the enterprise status for the administrator
        item = set_user_enterprise_status_value(enterprise_name, new_status)
        admin_profile.enterprises_status.update(item)

    elif user_object.role == 'EMPLOYEE':
        try:
            # Retrieve the employee profile associated with the user
            employee_profile = EmployeeProfile.objects.get(user=user_object)
        except EmployeeProfile.DoesNotExist:
            # If the employee profile doesn't exist, raise an appropriate exception
            raise EmployeeProfileDoesNotExistError(f"Employee profile for user {user.email} does not exist.")

        # Set the enterprise status for the employee
        item = set_user_enterprise_status_value(enterprise_name, new_status)
        employee_profile.enterprises_status.update(item)
    else:
        # If the user's role is invalid, raise an appropriate exception
        raise InvalidUserRoleError(f"User with email {user.email} has an invalid role: {user_object.role}.")


def return_jsonfield_value(instance_name, value):
    """ set the status value of the user for the specified enterprise name """
    new = {
        instance_name: value,
    }
    return json.dumps(new)
   

def set_user_enterprise_status_value(enterprise_name, value):
    """ Set the status value of the user for the specified enterprise name. """

    try:
        if value not in [1, 2, 3]:
            raise InvalidStatusError(f"Invalid status value: {value}.")

        new = {
            str(enterprise_name): value,
        }

        return json.dumps(new)

    except Exception as e:
        # Catch and log any unexpected exceptions
        logger.error(f"Error setting user enterprise status: {e}")
        return False


def set_enterprise_code(name) -> str:
    """
    Generate a unique enterprise code using the provided enterprise name.

    Args:
        name (str): The enterprise's name.

    Returns:
        str: The generated enterprise code.
    """

    if not name:
        raise ValueError("Enterprise name cannot be empty.")

    name = name.upper().replace(" ", "")

    if len(name) <= 5:
        code = name
    else:
        start = name[0:2]
        middle = name[int(len(name) / 2)]
        end = name[-2:]
        code = start + middle + end

        if Enterprise.objects.filter(code=code).exists():
            number = len(Enterprise.objects.filter(Q(code=code))) + 1
            code = code + '-' + str(number) + "-"

    return code


def set_record(user, related_object, action_type, modification):
    """ set user records """
    if not get_user_model().objects.filter().exists():
        #check if the user exists
        raise ValueError(f'The user {user.email} does not exists.')
    
    UserRecords.objects.create(user=user, action_type=action_type, action=modification)


def set_employee_category(user_profile, enterprise_name, category_name):
    """
    Set the employee category for the specified enterprise.

    Args:
        user_profile (EmployeeProfile): The employee profile object.
        enterprise_name (str): The name of the enterprise.
        category_name (str): The name of the employee category.
    """

    if not user_belong_to_enterprise(user_profile.user, Enterprise.objects.get(name=enterprise_name)):
        raise ValueError(f"The user {user_profile.user.email} does not belong to {enterprise_name} enterprise.")

    try:
        if user_profile.category == None:
            user_profile.category = json.dumps({enterprise_name: category_name})
            user_profile.save()
            return json.loads(user_profile.category)

        existing_categories = json.loads(user_profile.category)
        existing_categories[enterprise_name] = category_name
        user_profile.category = json.dumps(existing_categories)
        user_profile.save()
        return json.loads(user_profile.category)

    except Exception as e:
        logging.error(f"Error setting employee category for {user_profile.user.email} in enterprise {enterprise_name}: {e}")
        return None


def _get_user_profile(user):
    if user.role == 'ADMINISTRATOR':
        return AdministratorProfile.objects.get(user=user)
    elif user.role == 'EMPLOYEE':
        return EmployeeProfile.objects.get(user=user)


def check_user_enterprise_status(user, enterprise):
    user_profile = _get_user_profile(user)
    if user_profile.enterprises_status == None:
        logging.warning("The user is not a member of any enterprise.")
        return None

    try:
        data = json.loads(user_profile.enterprises_status)
        status = data[enterprise.name]
        if status not in [1, 2, 3]:
            logging.error(f"Unknown user status: {status} for enterprise: {enterprise.name}")
            return None
        return status

    except Exception as e:
        logging.error(f"Error checking user status for enterprise: {enterprise.name}: {e}")
        return None


def get_total_salary(user, enterprise):

    if user_belong_to_enterprise(user, enterprise) == False:
        raise ValueError("user must belong to the enterprise")
    
    total_salary: float = 0.0

    if user.role ==  'ADMINISTRATOR':
        #check if the admin is an active user of the enterprise
        try:
            enterprises = enterprise.objects.filter(Q(PDG=user) | Q(admin=user))
            for company in enterprises:
                if check_user_enterprise_status(user, company) in [1]:
                    total_salary += float(company.admin_salary)
            return total_salary
        except:
            pass
    elif user.role ==  'EMPLOYEE':
        companies = user.groups.all()
        for group in companies:
            if Enterprise.objects.filter(name=str(group)).exists():
                total_salary += get_employee_enterprise_salary(EmployeeProfile.objects.get(user=user), Enterprise.objects.get(name=str(group)))


def get_employee_enterprise_salary(user_profile, enterprise):
    """ 
    Return the user salary of a specify enterprise if the user belong 
    to that enterprise and is currently active: Status.ACTIVE
    """

    if not user_belong_to_enterprise(user_profile.user, enterprise):
        # Check if the employee belongs to the enterprise
        raise ValueError(f"The user {user_profile.user.email} is not an employee of {enterprise.name} enterprise.")
    
    if check_user_enterprise_status(user_profile.user, enterprise) in [2, 3]:
        # check if the user is currently active in that enterprise
        logging.warning(f'This user "{user_profile.user.email}" is not active.')
        return 0.0
    else:
        try:
            # Handle the case where the user doesn't have a category
            if user_profile.category == None:
                logging.warning(f"Employee {user_profile.user.email} does not belong to any category of {enterprise.name}.")
                return 0.0
            
            categories = json.loads(user_profile.category)
            employee_category = Category.objects.get(name=categories[enterprise.name])
            employee_salary = float(employee_category.salary)
            return employee_salary

        except Exception as e:
            logging.error(f"Error retrieving employee salary for {user_profile.user.email} in enterprise {enterprise.name}: {e}")
            return 0.0


def deactivate_enterprise_pdg_admin_and_add_admin(administrator, enterprise, new_administrator):
    """
    Deactivate the PDG of the enterprise and add an administrator.

    Or we can deactivate the previous administrator and add a new one,
    since an enterprise can only have one active PDG or one active administrator
    """

    # Verify administrator and new administrator roles
    if administrator.role !=  'ADMINISTRATOR' or new_administrator.role !=  'ADMINISTRATOR':
        raise ValueError("Both administrator and new_administrator must have the ADMINISTRATOR role.")

    # Handle deactivation and addition for the PDG
    if enterprise.PDG is administrator:
        deactivate_user(administrator, enterprise)
        add_new_administrator(new_administrator, enterprise)

    # Handle deactivation and addition for the administrator
    elif enterprise.admin.last() is administrator:
        deactivate_user(administrator, enterprise)
        add_new_administrator(new_administrator, enterprise)


def deactivate_enterprise_employee(employee, enterprise):
    """ Deactivate an employee from an enterprise """
    if employee.role !=  'EMPLOYEE' or user_belong_to_enterprise(employee, enterprise) is False:
        raise ValueError("Employee must have the EMPLOYEE role and must belong to the enterprise.")
    
    try:
        deactivate_user(employee, enterprise)
    except Exception as e:
        logging.error(f"Error deactivating employee {employee.email} from enterprise {enterprise.name}: {e}")


def deactivate_pdg(administrator, enterprise):
    try:
        # Update PDG enterprise status
        pdg_profile = AdministratorProfile.objects.get(user=administrator)
        file = json.loads(pdg_profile.enterprises_status)
        file[enterprise.name] = 2
        pdg_profile.enterprises_status = json.dumps(file)
        pdg_profile.save()

        # Remove the PDG from the enterprise group
        administrator.groups.remove(name=enterprise.name)
        administrator.save()

        # Send deactivation confirmation email to the PDG
        ctxt = {
            'email': administrator.email,
            'first_name': administrator.first_name,
            'last_name': administrator.last_name,
            'enterprise_name': enterprise.name,
            'role': administrator.role,
            'password': administrator.password
        }
        send_multi_format_email('deactivation_admin', ctxt, target_email=administrator.email)

    except Exception as e:
        print(f"Error deactivating PDG: {e}")


def deactivate_user(user, enterprise):
    try:
        if user.role ==  'ADMINISTRATOR':
            user_profile = AdministratorProfile.objects.get(user=user)
        elif user.role ==  'EMPLOYEE':
            user_profile = EmployeeProfile.objects.get(user=user)
        else:
            raise ValueError(f"User role \'{user.role}\' is invalid.")

        file = json.loads(user_profile.enterprises_status)
        file[enterprise.name] = 2
        user_profile.enterprises_status = json.dumps(file)
        user_profile.save()

        # Remove the PDG from the enterprise group
        user.groups.remove(name=enterprise.name)
        user.save()

        # Send deactivation confirmation email to the PDG
        ctxt = {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'enterprise_name': enterprise.name,
            'role': user.role,
            'password': user.password
        }

        if user.role ==  'ADMINISTRATOR':
            send_multi_format_email('deactivation_admin', ctxt, target_email=user.email)
        elif user.role ==  'EMPLOYEE':
            send_multi_format_email('deactivation_employee', ctxt, target_email=user.email)

    except Exception as e:
        print(f"Error deactivating user: {e}")


def add_new_administrator(new_administrator, enterprise):
    try:
        # Add new administrator to enterprise admin field
        enterprise.admin.add(new_administrator)
        enterprise.save()

        # Add the new administrator to the enterprise group
        new_administrator.groups.add(name=enterprise.name)
        new_administrator.save()

        # Update enterprise status in new administrator's profile
        admin_profile = AdministratorProfile.objects.get(user=new_administrator)
        if admin_profile.enterprises_status is not None:
            file = json.loads(admin_profile.enterprises_status)
            file[enterprise.name] = 1
            admin_profile.enterprises_status = json.dumps(file)
            admin_profile.save()

            # Send email notification to new administrator
            ctxt = {
                'email': new_administrator.email,
                'first_name': new_administrator.first_name,
                'last_name': new_administrator.last_name,
                'enterprise_name': enterprise.name,
                'role': new_administrator.role,
                'password': new_administrator.password
            }
            send_multi_format_email('add_admin', ctxt, target_email=new_administrator.email)

        else:
            file = set_user_enterprise_status_value(enterprise.name, 1)
            admin_profile.enterprises_status = file
            admin_profile.save()

            # Send email notification to new administrator
            ctxt = {
                'email': new_administrator.email,
                'first_name': new_administrator.first_name,
                'last_name': new_administrator.last_name,
                'enterprise_name': enterprise.name,
                'role': new_administrator.role,
                'password': new_administrator.password
            }
            send_multi_format_email('add_admin', ctxt, target_email=new_administrator.email)

    except Exception as e:
        print(f"Error adding the new administrator: {e}")


def add_new_employee(employee, enterprise, employee_password):
    try:
        # check if employee has EMPLOYEE role
        if employee.role !=  'EMPLOYEE':
            raise ValueError("user must have the EMPLOYEE role.")

        # Add the new administrator to the enterprise group
        add_user_to_group(employee, enterprise.name )

        # Update enterprise status of the new employee's profile
        employee_profile = EmployeeProfile.objects.get(user=employee)

        if employee_profile.enterprises_status is not None:
            file = json.loads(employee_profile.enterprises_status)
            file[enterprise.name] = 1
            employee_profile.enterprises_status = json.dumps(file)
            employee_profile.save()

            #   set employee matriculation number
            set_employee_enterprise_code(employee, enterprise)

            # Send email notification to new administrator
            ctxt = {
                'email': employee.email,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'enterprise_name': enterprise.name,
                'role': employee.role,
                'password': employee_password
            }
            send_multi_format_email('add_employee', ctxt, target_email=employee.email)
        else:
            file = set_user_enterprise_status_value(enterprise.name, 1)
            employee_profile.enterprises_status = file
            employee_profile.save()

            # set employee enterprise code
            set_employee_enterprise_code(employee, enterprise)

            # Send email notification to new administrator
            ctxt = {
                'email': employee.email,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'enterprise_name': enterprise.name,
                'role': employee.role,
                'password': employee_password
            }
            send_multi_format_email('add_employee', ctxt, target_email=employee.email)
            
    except Exception as e:
        print(f"Error adding the new employee: {e}")


def user_belong_to_enterprise(user, enterprise) -> bool:
    if user.groups.filter(name=enterprise.name).exists():
        return True
    else:
        return False


def generate_employee_code(enterprise) -> str:
    """Generates employee's matriculation number based on the enterprise code."""
    code = enterprise.code
    current_date = datetime.datetime.now()
    year = current_date.year
    employee_number = str(len(Employee.objects.all()) + 1)
    enterprise_code = f"{code}{year}-{employee_number}"
    return enterprise_code.upper()


def set_employee_enterprise_code(user, enterprise):
    user_profile = EmployeeProfile.objects.get(user=user)

    if user_profile.user_enterprise_code == None:
        enterprise_code = generate_employee_code(enterprise)
        user_profile.user_enterprise_code = return_jsonfield_value(enterprise.name, enterprise_code)
        user_profile.save()

    data = json.loads(user_profile.user_enterprise_code)
    if enterprise.name not in data:
        data[enterprise.name] = generate_employee_code(enterprise)
        user_profile.user_enterprise_code = json.dumps(data)
        user_profile.save()


def employee_is_admin(user, enterprise, status):
    if user.role == 'EMPLOYEE':
        user_profile = EmployeeProfile.objects.get(user=user)
        if user_profile.is_admin == None:
            data = {enterprise.name: status}
            user_profile.is_admin = json.dumps(data)
            user_profile.save()
        data = json.loads(user_profile.is_admin)
        data[enterprise.name] = status
        user_profile.is_admin = json.dumps(data)
        user_profile.save()
    pass


def check_employee_is_admin(user, enterprise):
    if user.role == 'EMPLOYEE':
        user_profile = EmployeeProfile.objects.get(user=user)
        if user_profile.is_admin == None:
            return f"This user is not an admin."
        else:
            data = json.loads(user_profile.is_admin)
            if enterprise.name in data:
                return data[enterprise.name]


def get_employee_matriculation_number(user, enterprise): 
    if not user_belong_to_enterprise(user, enterprise):
        return None
    
    if check_user_enterprise_status(user, enterprise) in [2, 3]:
        return None

    user_profile = _get_user_profile(user)
    try:
        data = json.loads(user_profile.user_enterprise_code)
        if enterprise.name in data:
            return data[enterprise.name]
    except:
        pass

    return None



# with function parameter type 

# def create_group(group_name: str):
#     """
#     Create a new group if it doesn't exist, otherwise return the existing group.
#     """
#     try:
#         if not Group.objects.filter(name=group_name).exists():
#             return Group.objects.create(name=group_name)
#         else:
#             return Group.objects.get(name=group_name)
#     except Exception as e:
#         logging.error(f"Error creating group: {e}")
#         return False
        

# def add_user_to_group(user: get_user_model(), group_name: str):
#     """
#     Add a user to a specific group if both user and group exist.
#     """
#     try:
#         user_instance = get_user_model().objects.get(email=user.email)
#         group_instance = Group.objects.get(name=group_name)
#         user_instance.groups.add(group_instance)
#         user_instance.save()
#         return user_instance
#     except Group.DoesNotExist:
#         logging.error(f"Group with name '{group_name}' does not exist.")
#         return False
#     except get_user_model().DoesNotExist:
#         logging.error(f"User with email '{user.email}' does not exist.")
#         return False
#     except Exception as e:
#         logging.error(f"Error adding user to group: {e}")
#         return False


# def remove_user_from_group(user: get_user_model(), group_name: str):
#     """
#     Remove a user from a specific group if both user and group exist.
#     """
#     try:
#         user_instance = get_user_model().objects.get(email=user.email)
#         group_instance = Group.objects.get(name=group_name)
#         user_instance.groups.objects.remove(group_instance)
#         user_instance.save()
#         return user_instance
#     except Group.DoesNotExist:
#         logging.error(f"Group with name '{group_name}' does not exist.")
#         return False
#     except get_user_model().DoesNotExist:
#         logging.error(f"User with email '{user.email}' does not exist.")
#         return False
#     except Exception as e:
#         logging.error(f"Error removing user from group: {e}")
#         return False


# def change_user_enterprise_status(user: get_user_model(), enterprise_name: str, new_status: int):
#     """
#     This function changes the user's enterprises_status for both employees and administrators.
#     """
#     # Check if the user exists
#     try:
#         # Retrieve the user object using the provided email address of the user parameter
#         user_object = get_user_model().objects.get(email=user.email)
#     except get_user_model().DoesNotExist:
#         # If the user doesn't exist, raise an appropriate exception
#         # raise UserDoesNotExistError(f"User with email {user.email} does not exist.")
#         raise UserDoesNotExist(f"User with email {user.email} does not exist.")

#     # Check the user's role
#     if user_object.role ==  ADMINISTRATOR:
#         try:
#             # Retrieve the administrator profile associated with the user
#             admin_profile = AdministratorProfile.objects.get(user=user_object)
#         except AdministratorProfile.DoesNotExist:
#             # If the administrator profile doesn't exist, raise an appropriate exception
#             raise AdministratorProfileDoesNotExistError(f"Administrator profile for user {user.email} does not exist.")

#         # Set the enterprise status for the administrator
#         item = set_user_enterprise_status_value(enterprise_name, new_status)
#         admin_profile.enterprises_status.update(item)

#     elif user_object.role ==  EMPLOYEE:
#         try:
#             # Retrieve the employee profile associated with the user
#             employee_profile = EmployeeProfile.objects.get(user=user_object)
#         except EmployeeProfile.DoesNotExist:
#             # If the employee profile doesn't exist, raise an appropriate exception
#             raise EmployeeProfileDoesNotExistError(f"Employee profile for user {user.email} does not exist.")

#         # Set the enterprise status for the employee
#         item = set_user_enterprise_status_value(enterprise_name, new_status)
#         employee_profile.enterprises_status.update(item)
#     else:
#         # If the user's role is invalid, raise an appropriate exception
#         raise InvalidUserRoleError(f"User with email {user.email} has an invalid role: {user_object.role}.")


# def return_jsonfield_value(instance_name: str, value: str):
#     """ set the status value of the user for the specified enterprise name """
#     new = {
#         instance_name: value,
#     }
#     return json.dumps(new)
   

# def set_user_enterprise_status_value(enterprise_name: str, value: int):
#     """ Set the status value of the user for the specified enterprise name. """

#     try:
#         if value not in [Status.ACTIVE, Status.DEACTIVATED, Status.SUSPENDED]:
#             raise InvalidStatusError(f"Invalid status value: {value}.")

#         new = {
#             str(enterprise_name): value,
#         }

#         return json.dumps(new)

#     except Exception as e:
#         # Catch and log any unexpected exceptions
#         logger.error(f"Error setting user enterprise status: {e}")
#         return False


# def set_enterprise_code(name: str) -> str:
#     """
#     Generate a unique enterprise code using the provided enterprise name.

#     Args:
#         name (str): The enterprise's name.

#     Returns:
#         str: The generated enterprise code.
#     """

#     if not name:
#         raise ValueError("Enterprise name cannot be empty.")

#     name = name.upper().replace(" ", "")

#     if len(name) <= 5:
#         code = name
#     else:
#         start = name[0:2]
#         middle = name[int(len(name) / 2)]
#         end = name[-2:]
#         code = start + middle + end

#         if Enterprise.objects.filter(code=code).exists():
#             number = len(Enterprise.objects.filter(Q(code=code))) + 1
#             code = code + '-' + str(number) + "-"

#     return code


# def set_record(user: get_user_model(), related_object: str, action_type: ActionType, modification: str):
#     """ set user records """
#     if not get_user_model().objects.filter().exists():
#         #check if the user exists
#         raise ValueError(f'The user {user.email} does not exists.')
    
#     UserRecords.objects.create(user=user, action_type=action_type, action=modification)


# def set_employee_category(user_profile: EmployeeProfile, enterprise_name: str, category_name: str):
#     """
#     Set the employee category for the specified enterprise.

#     Args:
#         user_profile (EmployeeProfile): The employee profile object.
#         enterprise_name (str): The name of the enterprise.
#         category_name (str): The name of the employee category.
#     """

#     if not user_belong_to_enterprise(user_profile.user, Enterprise.objects.get(name=enterprise_name)):
#         raise ValueError(f"The user {user_profile.user.email} does not belong to {enterprise_name} enterprise.")

#     try:
#         if user_profile.category == None:
#             user_profile.category = json.dumps({enterprise_name: category_name})
#             user_profile.save()
#             return json.loads(user_profile.category)

#         existing_categories = json.loads(user_profile.category)
#         existing_categories[enterprise_name] = category_name
#         user_profile.category = json.dumps(existing_categories)
#         user_profile.save()
#         return json.loads(user_profile.category)

#     except Exception as e:
#         logging.error(f"Error setting employee category for {user_profile.user.email} in enterprise {enterprise_name}: {e}")
#         return None


# def _get_user_profile(user: get_user_model()):
#     if user.role ==  ADMINISTRATOR:
#         return AdministratorProfile.objects.get(user=user)
#     elif user.role ==  EMPLOYEE:
#         return EmployeeProfile.objects.get(user=user)


# def check_user_enterprise_status(user: get_user_model(), enterprise: Enterprise):
#     user_profile = _get_user_profile(user)
#     if user_profile.enterprises_status == None:
#         logging.warning("The user is not a member of any enterprise.")
#         return None

#     try:
#         data = json.loads(user_profile.enterprises_status)
#         status = data[enterprise.name]
#         if status not in [Status.ACTIVE, Status.DEACTIVATED, Status.SUSPENDED]:
#             logging.error(f"Unknown user status: {status} for enterprise: {enterprise.name}")
#             return None
#         return status

#     except Exception as e:
#         logging.error(f"Error checking user status for enterprise: {enterprise.name}: {e}")
#         return None


# def get_total_salary(user: get_user_model(), enterprise: Enterprise):

#     if user_belong_to_enterprise(user, enterprise) == False:
#         raise ValueError("user must belong to the enterprise")
    
#     total_salary: float = 0.0

#     if user.role ==  ADMINISTRATOR:
#         #check if the admin is an active user of the enterprise
#         try:
#             enterprises = enterprise.objects.filter(Q(PDG=user) | Q(admin=user))
#             for company in enterprises:
#                 if check_user_enterprise_status(user, company) in [Status.ACTIVE]:
#                     total_salary += float(company.admin_salary)
#             return total_salary
#         except:
#             pass
#     elif user.role ==  EMPLOYEE:
#         companies = user.groups.all()
#         for group in companies:
#             if Enterprise.objects.filter(name=str(group)).exists():
#                 total_salary += get_employee_enterprise_salary(EmployeeProfile.objects.get(user=user), Enterprise.objects.get(name=str(group)))


# def get_employee_enterprise_salary(user_profile: EmployeeProfile, enterprise: Enterprise):
#     """ 
#     Return the user salary of a specify enterprise if the user belong 
#     to that enterprise and is currently active: Status.ACTIVE
#     """

#     if not user_belong_to_enterprise(user_profile.user, enterprise):
#         # Check if the employee belongs to the enterprise
#         raise ValueError(f"The user {user_profile.user.email} is not an employee of {enterprise.name} enterprise.")
    
#     if check_user_enterprise_status(user_profile.user, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED]:
#         # check if the user is currently active in that enterprise
#         logging.warning(f'This user "{user_profile.user.email}" is not active.')
#         return 0.0
#     else:
#         try:
#             # Handle the case where the user doesn't have a category
#             if user_profile.category == None:
#                 logging.warning(f"Employee {user_profile.user.email} does not belong to any category of {enterprise.name}.")
#                 return 0.0
            
#             categories = json.loads(user_profile.category)
#             employee_category = Category.objects.get(name=categories[enterprise.name])
#             employee_salary = float(employee_category.salary)
#             return employee_salary

#         except Exception as e:
#             logging.error(f"Error retrieving employee salary for {user_profile.user.email} in enterprise {enterprise.name}: {e}")
#             return 0.0


# def deactivate_enterprise_pdg_admin_and_add_admin(administrator: get_user_model(), enterprise: Enterprise, new_administrator: get_user_model()):
#     """
#     Deactivate the PDG of the enterprise and add an administrator.

#     Or we can deactivate the previous administrator and add a new one,
#     since an enterprise can only have one active PDG or one active administrator
#     """

#     # Verify administrator and new administrator roles
#     if administrator.role !=  ADMINISTRATOR or new_administrator.role !=  ADMINISTRATOR:
#         raise ValueError("Both administrator and new_administrator must have the ADMINISTRATOR role.")

#     # Handle deactivation and addition for the PDG
#     if enterprise.PDG is administrator:
#         deactivate_user(administrator, enterprise)
#         add_new_administrator(new_administrator, enterprise)

#     # Handle deactivation and addition for the administrator
#     elif enterprise.admin.last() is administrator:
#         deactivate_user(administrator, enterprise)
#         add_new_administrator(new_administrator, enterprise)


# def deactivate_enterprise_employee(employee: get_user_model(), enterprise: Enterprise):
#     """ Deactivate an employee from an enterprise """
#     if employee.role !=  EMPLOYEE or user_belong_to_enterprise(employee, enterprise) is False:
#         raise ValueError("Employee must have the EMPLOYEE role and must belong to the enterprise.")
    
#     try:
#         deactivate_user(employee, enterprise)
#     except Exception as e:
#         logging.error(f"Error deactivating employee {employee.email} from enterprise {enterprise.name}: {e}")


# def deactivate_pdg(administrator: get_user_model(), enterprise: Enterprise):
#     try:
#         # Update PDG enterprise status
#         pdg_profile = AdministratorProfile.objects.get(user=administrator)
#         file = json.loads(pdg_profile.enterprises_status)
#         file[enterprise.name] = Status.DEACTIVATED
#         pdg_profile.enterprises_status = json.dumps(file)
#         pdg_profile.save()

#         # Remove the PDG from the enterprise group
#         administrator.groups.remove(name=enterprise.name)
#         administrator.save()

#         # Send deactivation confirmation email to the PDG
#         ctxt = {
#             'email': administrator.email,
#             'first_name': administrator.first_name,
#             'last_name': administrator.last_name,
#             'enterprise_name': enterprise.name,
#             'role': administrator.role,
#             'password': administrator.password
#         }
#         send_multi_format_email('deactivation_admin', ctxt, target_email=administrator.email)

#     except Exception as e:
#         print(f"Error deactivating PDG: {e}")


# def deactivate_user(user: get_user_model(), enterprise: Enterprise):
#     try:
#         if user.role ==  ADMINISTRATOR:
#             user_profile = AdministratorProfile.objects.get(user=user)
#         elif user.role ==  EMPLOYEE:
#             user_profile = EmployeeProfile.objects.get(user=user)
#         else:
#             raise ValueError(f"User role \'{user.role}\' is invalid.")

#         file = json.loads(user_profile.enterprises_status)
#         file[enterprise.name] = Status.DEACTIVATED
#         user_profile.enterprises_status = json.dumps(file)
#         user_profile.save()

#         # Remove the PDG from the enterprise group
#         user.groups.remove(name=enterprise.name)
#         user.save()

#         # Send deactivation confirmation email to the PDG
#         ctxt = {
#             'email': user.email,
#             'first_name': user.first_name,
#             'last_name': user.last_name,
#             'enterprise_name': enterprise.name,
#             'role': user.role,
#             'password': user.password
#         }

#         if user.role ==  ADMINISTRATOR:
#             send_multi_format_email('deactivation_admin', ctxt, target_email=user.email)
#         elif user.role ==  EMPLOYEE:
#             send_multi_format_email('deactivation_employee', ctxt, target_email=user.email)

#     except Exception as e:
#         print(f"Error deactivating user: {e}")


# def add_new_administrator(new_administrator: get_user_model(), enterprise: Enterprise):
#     try:
#         # Add new administrator to enterprise admin field
#         enterprise.admin.add(new_administrator)
#         enterprise.save()

#         # Add the new administrator to the enterprise group
#         new_administrator.groups.add(name=enterprise.name)
#         new_administrator.save()

#         # Update enterprise status in new administrator's profile
#         admin_profile = AdministratorProfile.objects.get(user=new_administrator)
#         if admin_profile.enterprises_status is not None:
#             file = json.loads(admin_profile.enterprises_status)
#             file[enterprise.name] = Status.ACTIVE
#             admin_profile.enterprises_status = json.dumps(file)
#             admin_profile.save()

#             # Send email notification to new administrator
#             ctxt = {
#                 'email': new_administrator.email,
#                 'first_name': new_administrator.first_name,
#                 'last_name': new_administrator.last_name,
#                 'enterprise_name': enterprise.name,
#                 'role': new_administrator.role,
#                 'password': new_administrator.password
#             }
#             send_multi_format_email('add_admin', ctxt, target_email=new_administrator.email)

#         else:
#             file = set_user_enterprise_status_value(enterprise.name, Status.ACTIVE)
#             admin_profile.enterprises_status = file
#             admin_profile.save()

#             # Send email notification to new administrator
#             ctxt = {
#                 'email': new_administrator.email,
#                 'first_name': new_administrator.first_name,
#                 'last_name': new_administrator.last_name,
#                 'enterprise_name': enterprise.name,
#                 'role': new_administrator.role,
#                 'password': new_administrator.password
#             }
#             send_multi_format_email('add_admin', ctxt, target_email=new_administrator.email)

#     except Exception as e:
#         print(f"Error adding the new administrator: {e}")


# def add_new_employee(employee: get_user_model(), enterprise: Enterprise, employee_password: str):
#     try:
#         # check if employee has EMPLOYEE role
#         if employee.role !=  EMPLOYEE:
#             raise ValueError("user must have the EMPLOYEE role.")

#         # Add the new administrator to the enterprise group
#         add_user_to_group(employee, enterprise.name )

#         # Update enterprise status of the new employee's profile
#         employee_profile = EmployeeProfile.objects.get(user=employee)

#         if employee_profile.enterprises_status is not None:
#             file = json.loads(employee_profile.enterprises_status)
#             file[enterprise.name] = Status.ACTIVE
#             employee_profile.enterprises_status = json.dumps(file)
#             employee_profile.save()

#             #   set employee matriculation number
#             set_employee_enterprise_code(employee, enterprise)

#             # Send email notification to new administrator
#             ctxt = {
#                 'email': employee.email,
#                 'first_name': employee.first_name,
#                 'last_name': employee.last_name,
#                 'enterprise_name': enterprise.name,
#                 'role': employee.role,
#                 'password': employee_password
#             }
#             send_multi_format_email('add_employee', ctxt, target_email=employee.email)
#         else:
#             file = set_user_enterprise_status_value(enterprise.name, Status.ACTIVE)
#             employee_profile.enterprises_status = file
#             employee_profile.save()

#             # set employee enterprise code
#             set_employee_enterprise_code(employee, enterprise)

#             # Send email notification to new administrator
#             ctxt = {
#                 'email': employee.email,
#                 'first_name': employee.first_name,
#                 'last_name': employee.last_name,
#                 'enterprise_name': enterprise.name,
#                 'role': employee.role,
#                 'password': employee_password
#             }
#             send_multi_format_email('add_employee', ctxt, target_email=employee.email)
            
#     except Exception as e:
#         print(f"Error adding the new employee: {e}")


# def user_belong_to_enterprise(user: get_user_model(), enterprise: Enterprise) -> bool:
#     if user.groups.filter(name=enterprise.name).exists():
#         return True
#     else:
#         return False


# def generate_employee_code(enterprise: Enterprise) -> str:
#     """Generates employee's matriculation number based on the enterprise code."""
#     code = enterprise.code
#     current_date = datetime.datetime.now()
#     year = current_date.year
#     employee_number = str(len(Employee.objects.all()) + 1)
#     enterprise_code = f"{code}{year}-{employee_number}"
#     return enterprise_code.upper()


# def set_employee_enterprise_code(user: get_user_model(), enterprise: Enterprise):
#     user_profile = EmployeeProfile.objects.get(user=user)

#     if user_profile.user_enterprise_code == None:
#         enterprise_code = generate_employee_code(enterprise)
#         user_profile.user_enterprise_code = return_jsonfield_value(enterprise.name, enterprise_code)
#         user_profile.save()

#     data = json.loads(user_profile.user_enterprise_code)
#     if enterprise.name not in data:
#         data[enterprise.name] = generate_employee_code(enterprise)
#         user_profile.user_enterprise_code = json.dumps(data)
#         user_profile.save()


# def employee_is_admin(user: get_user_model(), enterprise: Enterprise, status: bool):
#     if user.role == 'EMPLOYEE':
#         user_profile = EmployeeProfile.objects.get(user=user)
#         if user_profile.is_admin == None:
#             data = {enterprise.name: status}
#             user_profile.is_admin = json.dumps(data)
#             user_profile.save()
#         data = json.loads(user_profile.is_admin)
#         data[enterprise.name] = status
#         user_profile.is_admin = json.dumps(data)
#         user_profile.save()
#     pass


# def check_employee_is_admin(user: get_user_model(), enterprise: Enterprise):
#     if user.role == 'EMPLOYEE':
#         user_profile = EmployeeProfile.objects.get(user=user)
#         if user_profile.is_admin == None:
#             return f"This user is not an admin."
#         else:
#             data = json.loads(user_profile.is_admin)
#             if enterprise.name in data:
#                 return data[enterprise.name]


# def get_employee_matriculation_number(user: get_user_model(), enterprise: Enterprise): 
#     if not user_belong_to_enterprise(user, enterprise):
#         return None
    
#     if check_user_enterprise_status(user, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED]:
#         return None

#     user_profile = _get_user_profile(user)
#     try:
#         data = json.loads(user_profile.user_enterprise_code)
#         if enterprise.name in data:
#             return data[enterprise.name]
#     except:
#         pass

#     return None

