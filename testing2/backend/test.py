import pymysql

try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        database='complaint_system',
        port=3306
    )
    print("Connection successful!")
    connection.close()
except Exception as e:
    print(f"Connection failed: {e}")
