#db
import psycopg2
from psycopg2 import sql
import bcrypt
from flask import jsonify
from datetime import datetime

# Function to initialize the database
def init_db():
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname="kaneah",
        user="kaneah",
        password="",  # Assuming there's no password
        host="localhost"
    )

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone_number VARCHAR(15)
        );
    """)

    # Create Bank Accounts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank_accounts (
            account_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            account_number VARCHAR(20) UNIQUE NOT NULL,
            balance DECIMAL(10, 2) DEFAULT 0.0
        );
    """)

    # Create Momo Accounts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS momo_accounts (
            momo_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            phone_number VARCHAR(15) UNIQUE NOT NULL,
            balance DECIMAL(10, 2) DEFAULT 0.0
        );
    """)

    # Create Transactions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id SERIAL PRIMARY KEY,
            sender_id INTEGER REFERENCES users(user_id),
            receiver_id INTEGER REFERENCES users(user_id),
            amount DECIMAL(10, 2) NOT NULL,
            transaction_type VARCHAR(50) NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create Statements Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS statements (
            statement_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            transaction_id INTEGER REFERENCES transactions(transaction_id),
            statement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create Charges Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS charges (
            charge_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            amount DECIMAL(10, 2) NOT NULL,
            charge_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create Admins Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    """)

    # Commit the changes and close the cursor and connection
    conn.commit()
    cursor.close()
    conn.close()

# Call the init_db function to initialize the database
init_db()

# Create a cursor object to execute SQL queries
conn = psycopg2.connect(
    dbname="kaneah",
    user="kaneah",
    password="",  # Assuming there's no password
    host="localhost"
)
cursor = conn.cursor()

# Function to create a bank account
def create_bank_account(username, password, email, phone_number, account_number=None, initial_balance=1000.0):
    try:
        # Insert user data into the 'users' table
        cursor.execute("""
            INSERT INTO users (username, password, email, phone_number)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id;
        """, (username, password, email, phone_number))
        user_id = cursor.fetchone()[0]

        # If account_number is not provided, generate a unique account number
        if account_number is None:
            account_number = generate_account_number()

        # Insert bank account data into the 'bank_accounts' table
        cursor.execute("""
            INSERT INTO bank_accounts (user_id, account_number, balance)
            VALUES (%s, %s, %s)
            RETURNING account_id;
        """, (user_id, account_number, initial_balance))
        
        account_result = cursor.fetchone()
        
        if account_result:
            account_id = account_result[0]
            conn.commit()
            return account_id
        else:
            # Handle the case where the account result is None
            conn.rollback()
            return None
    except Exception as e:
        # Handle any other exceptions and rollback the transaction
        print(f"Error: {e}")
        conn.rollback()
        return None

    
# Function to get all accounts
def get_all_accounts():
    cursor.execute("""
        SELECT
            u.user_id,
            u.username,
            u.email,
            u.phone_number,
            b.account_number,
            b.balance
        FROM users u
        JOIN bank_accounts b ON u.user_id = b.user_id;
    """)
    accounts = cursor.fetchall()
    return accounts

# Function to create a phone number
def create_phone_number(user_id, phone_number, initial_balance=1000.0):
    cursor.execute("""
        INSERT INTO momo_accounts (user_id, phone_number, balance)
        VALUES (%s, %s, %s)
        RETURNING momo_id;
    """, (user_id, phone_number, initial_balance))
    momo_id = cursor.fetchone()[0]
    conn.commit()
    return momo_id

# Function to transfer money to own momo
def transfer_to_own_momo(user_id, amount):
    if amount > 0:
        # Update momo_account balance
        cursor.execute("""
            UPDATE momo_accounts
            SET balance = balance + %s
            WHERE user_id = %s;
        """, (amount, user_id))

        # Insert the transaction record
        cursor.execute("""
            INSERT INTO transactions (sender_id, receiver_id, amount, transaction_type)
            VALUES (%s, %s, %s, %s);
        """, (user_id, user_id, amount, 'Bank to Momo'))

        conn.commit()
        return True, jsonify(message='Money transferred to own momo successfully')  # Return a tuple with success flag
    else:
        return False, jsonify(error='Invalid amount. Amount must be greater than 0.'), 400


# Function to transfer money to third-party momo
def transfer_to_third_party_momo(sender_id, receiver_phone_number, amount):
    cursor.execute("""
        SELECT user_id FROM momo_accounts WHERE phone_number = %s;
    """, (receiver_phone_number,))
    receiver_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO transactions (sender_id, receiver_id, amount, transaction_type)
        VALUES (%s, %s, %s, %s);
    """, (sender_id, receiver_id, amount, 'Bank to Third-Party Momo'))
    conn.commit()

# Function to request statements
def request_statements(user_id):
    cursor.execute("""
        SELECT transaction_id, statement_date
        FROM statements
        WHERE user_id = %s;
    """, (user_id,))
    statements = cursor.fetchall()
    return statements

# Function to check user data privacy
def check_user_data_privacy(user_id, requested_user_id):
    return user_id == requested_user_id  # Replace with your logic

# Function to save charge profit
def save_charge_profit(user_id, amount):
    cursor.execute("""
        INSERT INTO charges (user_id, amount, charge_date)
        VALUES (%s, %s, %s);
    """, (user_id, amount, datetime.now()))
    conn.commit()

# Function for admin to get statements
def admin_get_statements(admin_id):
    # Implement logic for admin access (if needed)
    return []

# Close the cursor and connection
def close_db():
    cursor.close()
    conn.close()
