import bcrypt

emp_hash  = bcrypt.hashpw(b'employee123', bcrypt.gensalt()).decode()
cust_hash = bcrypt.hashpw(b'customer123', bcrypt.gensalt()).decode()
adm_hash  = bcrypt.hashpw(b'admin123',    bcrypt.gensalt()).decode()

print("Employee hash:", emp_hash)
print("Customer hash:", cust_hash)
print("Admin hash:   ", adm_hash)

