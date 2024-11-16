import requests
# import json

login = 'http://127.0.0.1:8000/EGT/login/'

# get or create the token for authentication
auth_token = requests.post(login, json={'email': 'egt4startup@gmail.com', 'password': 'mhulo2029'})
# print(auth_token.json())

headers = {
    'Authorization': 'token '+ auth_token.json().get('token')
}

print(headers['Authorization'])
# headers = {
#     'Authorization': 'admin 020ee9e31696343364876eaff265b7906d09e658'
# }

url = "http://127.0.0.1:8000/performance/month/weeks/activities/performance/"


data = {
    'enterprise_name': 'employee goal tracker',
    'year': 2024,
    'month_number': 1
}



# goals_list = 'http://127.0.0.1:8000/tasks/Goal/list/'
users_me = 'http://127.0.0.1:8000/EGT/users/me'
# add_employee = 'http://127.0.0.1:8000/EGT/add/employee/'
# data = {
#     'enterprise_name': 'EL ENTERPRISE', 
#     'email': 'malabarmhulo2@gmail.com', 
#     'first_name': 'add_employee', 
#     'last_name': 'add_employee',
# }
# response = requests.post(url, headers=headers, json={'enterprise_name': 'employee goal tracker', 'year': 2024, 'month_number': 1})
response = requests.get(users_me, headers=headers)

print(response.json())