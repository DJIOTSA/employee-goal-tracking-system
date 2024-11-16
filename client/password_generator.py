
import string
import random

def generate_password():
    password_length = 8
    password_characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(password_characters) for i in range(password_length))
    print(password)
    return password

generate_password()