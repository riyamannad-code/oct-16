import bcrypt

password = "ldc12345"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hashed.decode())


