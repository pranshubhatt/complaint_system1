import pymysql

try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='$ujay#Edge24',  # Replace with your actual password
        database='complaint_system'
    )
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
