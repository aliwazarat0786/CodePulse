import os
import hashlib

password = "admin_super_secret_123"

def process_user_data(data):
    # Dynamic execution hazard
    result = eval(data)
    
    # Excessive nesting
    for i in range(10):
        if i > 2:
            if i < 8:
                if i != 5:
                    print(f"Item: {i}")
    return result

def uncalled_function():
    unused_var = 42
    pass
