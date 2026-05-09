import mysql.connector

try:
    # Connect directly to the MySQL engine (ignoring phpMyAdmin)
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    cursor = db.cursor()

    # Force create the database
    cursor.execute("CREATE DATABASE IF NOT EXISTS rigtracker_db")
    cursor.execute("USE rigtracker_db")

    # Force create the Builds table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS builds (
      Build_ID INT AUTO_INCREMENT PRIMARY KEY,
      Build_Name VARCHAR(255) NOT NULL,
      Date_Created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Force create the Components table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS components (
      ID INT AUTO_INCREMENT PRIMARY KEY,
      Model VARCHAR(255) NOT NULL,
      Category VARCHAR(100) NOT NULL,
      ItemCondition VARCHAR(50) NOT NULL,
      BasePrice DECIMAL(10, 2) NOT NULL,
      Build_ID INT,
      Date_Added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    print("✅ DATABASE COMPLETELY SETUP! YOU CAN NOW RUN RIGTRACKER!")
    db.close()

except Exception as e:
    print(f"❌ Error: {e}")