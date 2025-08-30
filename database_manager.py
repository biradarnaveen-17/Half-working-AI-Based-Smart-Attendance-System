# database_manager.py
import mysql.connector
from mysql.connector import Error
import datetime
import sqlite3

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
        
    def connect(self):
        """Create database connection with proper error handling"""
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="attendance_system"
            )
            if self.connection.is_connected():
                print("✅ Database connected successfully")
                self.initialize_tables()
                
        except Error as e:
            print(f"❌ Database connection failed: {e}")
            self.use_fallback_database()
    
    def use_fallback_database(self):
        """Fallback to SQLite if MySQL is not available"""
        try:
            self.connection = sqlite3.connect('attendance_fallback.db')
            print("✅ Using SQLite fallback database")
            self.initialize_tables()
        except Exception as e:
            print(f"❌ Fallback database also failed: {e}")
    
    def initialize_tables(self):
        """Ensure all required tables exist"""
        try:
            cursor = self.connection.cursor()
            
            # Create students table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create enhanced attendance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    student_name VARCHAR(100) NOT NULL,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    confidence FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_attendance (student_name, date)
                )
            """)
            
            self.connection.commit()
            print("✅ Database tables initialized")
            
        except Error as e:
            print(f"❌ Table creation failed: {e}")
            if hasattr(self.connection, 'rollback'):
                self.connection.rollback()