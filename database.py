import os
import sqlite3
import re
from datetime import datetime

# Database connection configuration
MYSQL_HOST = os.environ.get("DB_HOST", "localhost")
MYSQL_USER = os.environ.get("DB_USER", "root")
MYSQL_PASSWORD = os.environ.get("DB_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("DB_NAME", "maidbooking")
SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "maidbooking.db")

# Detect database backend (MySQL vs SQLite fallback)
_USE_SQLITE = False
_MYSQL_DRIVER = None

try:
    import pymysql
    _MYSQL_DRIVER = "pymysql"
except ImportError:
    try:
        import mysql.connector
        _MYSQL_DRIVER = "mysql.connector"
    except ImportError:
        _USE_SQLITE = True

def _test_mysql():
    global _USE_SQLITE
    if _USE_SQLITE or _MYSQL_DRIVER is None:
        return False
    try:
        if _MYSQL_DRIVER == "pymysql":
            conn = pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                connect_timeout=2
            )
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}`")
            conn.close()
            # Test connecting directly to the database
            conn = pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                connect_timeout=2
            )
            conn.close()
            return True
        elif _MYSQL_DRIVER == "mysql.connector":
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                connection_timeout=2
            )
            cur = conn.cursor()
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}`")
            cur.close()
            conn.close()
            return True
    except Exception as e:
        # MySQL not running or credentials invalid -> fallback to SQLite
        return False
    return False

# Initialize backend detection
if not _USE_SQLITE:
    if not _test_mysql():
        _USE_SQLITE = True

print(f"[*] MaidBooking Database Engine: {'SQLite (' + SQLITE_PATH + ')' if _USE_SQLITE else 'MySQL (' + MYSQL_DATABASE + ')'}")

def get_connection():
    if _USE_SQLITE:
        os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        if _MYSQL_DRIVER == "pymysql":
            return pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        else:
            return mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )

def _translate_for_sqlite(query):
    # Convert %s to ?
    # Be careful not to replace % inside LIKE strings or date formats if any, but standard SQL %s is safe
    q = re.sub(r'(?<!%)(%s)', '?', query)
    # Translate NOW() and CURDATE()
    q = re.sub(r'\bNOW\(\)', "datetime('now', 'localtime')", q, flags=re.IGNORECASE)
    q = re.sub(r'\bCURDATE\(\)', "date('now', 'localtime')", q, flags=re.IGNORECASE)
    return q

def init_db():
    """Initializes tables and seeds default data if not already present."""
    conn = get_connection()
    if _USE_SQLITE:
        cur = conn.cursor()
        cur.executescript('''
        CREATE TABLE IF NOT EXISTS login (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS customer (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            c_fname TEXT NOT NULL,
            c_lname TEXT NOT NULL,
            c_housename TEXT DEFAULT '',
            c_street TEXT DEFAULT '',
            c_city TEXT DEFAULT '',
            c_state TEXT DEFAULT 'Kerala',
            c_pincode TEXT DEFAULT '',
            c_phone TEXT DEFAULT '',
            c_email TEXT DEFAULT '',
            c_gender TEXT DEFAULT 'Male',
            c_dob TEXT DEFAULT '',
            c_status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS maid (
            maid_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            maid_fname TEXT NOT NULL,
            maid_lname TEXT NOT NULL,
            maid_housename TEXT DEFAULT '',
            maid_street TEXT DEFAULT '',
            maid_city TEXT DEFAULT '',
            maid_dist TEXT DEFAULT 'Ernakulam',
            maid_pincode TEXT DEFAULT '',
            maid_phone TEXT DEFAULT '',
            maid_email TEXT DEFAULT '',
            maid_gender TEXT DEFAULT 'Female',
            maid_dob TEXT DEFAULT '',
            experience TEXT DEFAULT '3 Years',
            hourly_rate REAL DEFAULT 350.00,
            maid_status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS service (
            service_id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            details TEXT,
            rate REAL DEFAULT 350.00,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS slot (
            slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER DEFAULT 0,
            slot TEXT NOT NULL,
            fromtime TEXT NOT NULL,
            totime TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS booking (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            maid_id INTEGER NOT NULL DEFAULT 0,
            service_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            booking_address TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            notes TEXT,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Confirmed',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS payment (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            transaction_id TEXT NOT NULL,
            payment_status TEXT DEFAULT 'Paid',
            payment_date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS review (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            maid_id INTEGER NOT NULL,
            rating INTEGER NOT NULL DEFAULT 5,
            review_text TEXT,
            review_date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS complaint (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            booking_id INTEGER DEFAULT 0,
            complaint TEXT NOT NULL,
            reply TEXT DEFAULT 'pending',
            complaint_date TEXT NOT NULL
        );
        ''')
        conn.commit()

        # Seed data if empty
        cur.execute("SELECT COUNT(*) FROM login")
        if cur.fetchone()[0] == 0:
            cur.executescript('''
            INSERT INTO login (username, password, type, status) VALUES
            ('admin', 'admin', 'admin', 'active'),
            ('staff', 'staff', 'maid', 'active'),
            ('mary@maid.com', 'mary123', 'maid', 'active'),
            ('anita@maid.com', 'anita123', 'maid', 'active'),
            ('arun@gmail.com', 'arun', 'customer', 'active');

            INSERT INTO customer (customer_id, username, c_fname, c_lname, c_housename, c_street, c_city, c_state, c_pincode, c_phone, c_email, c_gender, c_dob, c_status) VALUES
            (1, 'arun@gmail.com', 'Arun', 'Kumar', 'Arun Nivas', '2nd Street, Kakkanad', 'Kochi', 'Kerala', '682030', '9876543210', 'arun@gmail.com', 'male', '1998-05-12', 'active');

            INSERT INTO maid (maid_id, username, maid_fname, maid_lname, maid_housename, maid_street, maid_city, maid_dist, maid_pincode, maid_phone, maid_email, maid_gender, maid_dob, experience, hourly_rate, maid_status) VALUES
            (1, 'staff', 'Amal', 'Raj', 'Amal Bhavan', '32nd Cross, Edappally', 'Kochi', 'Ernakulam', '682024', '9847123456', 'amal@maid.com', 'male', '1995-02-14', '4 Years', 300.00, 'active'),
            (2, 'mary@maid.com', 'Mary', 'Joseph', 'St. Marys Villa', 'MG Road', 'Ernakulam', 'Ernakulam', '682016', '9847654321', 'mary@maid.com', 'female', '1992-08-20', '5 Years', 400.00, 'active'),
            (3, 'anita@maid.com', 'Anita', 'Nair', 'Nair Cottage', 'Kaloor Kadavanthra', 'Kochi', 'Ernakulam', '682017', '9745123987', 'anita@maid.com', 'female', '1996-11-05', '2 Years', 350.00, 'active');

            INSERT INTO service (service_id, service, details, rate, status) VALUES
            (1, 'Deep Home Cleaning', 'Complete sanitization, floor scrubbing, kitchen deep degreasing, and dusting.', 500.00, 'active'),
            (2, 'Daily Cooking & Meal Prep', 'Traditional home-cooked breakfast, lunch, or dinner preparation with dietary preferences.', 400.00, 'active'),
            (3, 'Babysitting & Child Care', 'Attentive childcare, homework supervision, meal feeding, and playtime engagement.', 350.00, 'active'),
            (4, 'Elderly Assistance', 'Companionship, medicine reminders, light mobility assistance, and meal serving.', 350.00, 'active'),
            (5, 'Laundry & Ironing', 'Washing, gentle garment handling, pressing, and organized folding.', 250.00, 'active');

            INSERT INTO slot (slot_id, service_id, slot, fromtime, totime, status) VALUES
            (1, 1, 'Morning Shift 1', '08:00 AM', '11:00 AM', 'active'),
            (2, 1, 'Afternoon Shift', '12:00 PM', '03:00 PM', 'active'),
            (3, 2, 'Evening Shift', '04:00 PM', '07:00 PM', 'active'),
            (4, 0, 'Full Day Support', '09:00 AM', '05:00 PM', 'active');

            INSERT INTO booking (booking_id, customer_id, maid_id, service_id, slot_id, booking_date, booking_address, contact_phone, notes, total_amount, status, created_at) VALUES
            (1, 1, 1, 1, 1, '2026-11-20', 'Arun Nivas, Kakkanad, Kochi', '9876543210', 'Focus especially on kitchen and bathroom deep cleaning', 500.00, 'Confirmed', '2026-11-17 10:00:00'),
            (2, 1, 2, 2, 3, '2026-11-21', 'Arun Nivas, Kakkanad, Kochi', '9876543210', 'Dinner prep for family of 4, south Indian dishes', 400.00, 'Completed', '2026-11-15 09:30:00');

            INSERT INTO payment (payment_id, booking_id, customer_id, amount, payment_method, transaction_id, payment_status, payment_date) VALUES
            (1, 1, 1, 500.00, 'UPI', 'TXN-MB-9823412', 'Paid', '2026-11-17 10:05:00'),
            (2, 2, 1, 400.00, 'Card', 'TXN-MB-1234567', 'Paid', '2026-11-15 09:35:00');

            INSERT INTO review (review_id, booking_id, customer_id, maid_id, rating, review_text, review_date) VALUES
            (1, 2, 1, 2, 5, 'Mary prepared very delicious food, very polite and on time. Highly recommended!', '2026-11-21 20:00:00');

            INSERT INTO complaint (complaint_id, customer_id, booking_id, complaint, reply, complaint_date) VALUES
            (1, 1, 1, 'Maid arrived 15 minutes later than requested.', 'We apologize for the delay. The maid encountered unexpected traffic, and we have updated her schedule accordingly.', '2026-11-17 11:00:00');
            ''')
            conn.commit()
        cur.close()
    conn.close()

# Initialize DB on module import
init_db()

def select(q, params=None):
    conn = get_connection()
    try:
        if _USE_SQLITE:
            sql = _translate_for_sqlite(q)
            cur = conn.cursor()
            if params:
                cur.execute(sql, tuple(params))
            else:
                cur.execute(sql)
            rows = cur.fetchall()
            result = [dict(row) for row in rows]
            cur.close()
            return result
        else:
            if _MYSQL_DRIVER == "pymysql":
                cur = conn.cursor(pymysql.cursors.DictCursor)
            else:
                cur = conn.cursor(dictionary=True)
            if params:
                cur.execute(q, tuple(params))
            else:
                cur.execute(q)
            result = cur.fetchall()
            cur.close()
            return result
    finally:
        conn.close()

def update(q, params=None):
    conn = get_connection()
    try:
        if _USE_SQLITE:
            sql = _translate_for_sqlite(q)
            cur = conn.cursor()
            if params:
                cur.execute(sql, tuple(params))
            else:
                cur.execute(sql)
            conn.commit()
            rowcount = cur.rowcount
            cur.close()
            return rowcount
        else:
            cur = conn.cursor()
            if params:
                cur.execute(q, tuple(params))
            else:
                cur.execute(q)
            conn.commit()
            rowcount = cur.rowcount
            cur.close()
            return rowcount
    finally:
        conn.close()

def delete(q, params=None):
    conn = get_connection()
    try:
        if _USE_SQLITE:
            sql = _translate_for_sqlite(q)
            cur = conn.cursor()
            if params:
                cur.execute(sql, tuple(params))
            else:
                cur.execute(sql)
            conn.commit()
            rowcount = cur.rowcount
            cur.close()
            return rowcount
        else:
            cur = conn.cursor()
            if params:
                cur.execute(q, tuple(params))
            else:
                cur.execute(q)
            conn.commit()
            rowcount = cur.rowcount
            cur.close()
            return rowcount
    finally:
        conn.close()

def insert(q, params=None):
    conn = get_connection()
    try:
        if _USE_SQLITE:
            sql = _translate_for_sqlite(q)
            cur = conn.cursor()
            if params:
                cur.execute(sql, tuple(params))
            else:
                cur.execute(sql)
            conn.commit()
            lastid = cur.lastrowid
            cur.close()
            return lastid
        else:
            cur = conn.cursor()
            if params:
                cur.execute(q, tuple(params))
            else:
                cur.execute(q)
            conn.commit()
            lastid = cur.lastrowid
            cur.close()
            return lastid
    finally:
        conn.close()
