import bcrypt
import csv

# 🔢 Step 1: Define your student list
# Format: [(username, name, plain_text_password)]
students = [
    ("student1", "aswin", "aswin123"),
    ("student2", "meera", "meera456"),
    ("student3", "rohan", "rohan789"),
    ("student4", "priya", "priya123")
]

# 📄 Step 2: Create and write to CSV
with open("student_credentials.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Username", "Name", "HashedPassword"])

    for username, name, password in students:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        writer.writerow([username, name, hashed])

print("✅ student_credentials.csv generated successfully.")
