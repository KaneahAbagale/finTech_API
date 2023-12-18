from flask import Flask, request, jsonify
import re
import random
from database import init_db, create_bank_account, create_phone_number, \
    transfer_to_own_momo, transfer_to_third_party_momo, request_statements, \
    check_user_data_privacy, save_charge_profit, admin_get_statements, get_all_accounts

app = Flask(__name__)

# Move this line outside of the create_bank_account_api function
def get_request_data():
    return request.get_json() or {}

# Extract relevant data
def extract_data(keys, data):
    return {key: data[key] for key in keys if key in data}

@app.route('/create_bank_account', methods=['POST'])
def create_bank_account_api():
    data = get_request_data()

    # Extract relevant data
    keys = ['username', 'password', 'email', 'phone_number']
    user_data = extract_data(keys, data)

    # Validate email format
    if not is_valid_email(user_data.get('email', '')):
        return jsonify(error='Invalid email format.'), 400

    # Ensure phone_number is present and is an integer
    if 'phone_number' not in data or not data['phone_number']:
        return jsonify(error='Phone number is required.'), 400
    
    phone_number = str(data['phone_number'])
    # Validate and format phone number
    if not phone_number.isdigit() or len(phone_number) != 10:
        return jsonify(error='Invalid phone_number. It should be an integer and 10 characters long.'), 400

    # Generate a unique account number
    account_number = generate_account_number()

    # Set the initial balance to 1000
    balance = 1000.0

    create_bank_account(**user_data, account_number=account_number, initial_balance=balance)

    return jsonify(message='Bank account created successfully')

@app.route('/get_all_accounts', methods=['GET'])
def get_all_accounts_api():
    accounts = get_all_accounts()
    return jsonify(accounts=accounts)


@app.route('/add_phone_number', methods=['POST'])
def add_phone_number():
    data = get_request_data()
    user_id = data['user_id']
    phone_number = str(data['phone_number'])
    balance = 1000.0

    # Validate and format phone number
    if not phone_number.isdigit() or len(phone_number) != 10:
        return jsonify(error='Invalid phone_number. It should be an integer and 10 characters long.'), 400

    create_phone_number(user_id, phone_number, balance)

    return jsonify(message='Phone number added successfully')

@app.route('/transfer_to_own_momo', methods=['POST'])
def transfer_to_own_momo_api():
    data = get_request_data()
    user_id = data['user_id']
    amount = data['amount']

    success, response = transfer_to_own_momo(user_id, amount)

    if success:
        return response
    else:
        return response


@app.route('/transfer_to_third_party_momo', methods=['POST'])
def transfer_to_third_party_momo_api():
    data = get_request_data()
    sender_id = data['sender_id']
    receiver_phone_number = data['receiver_phone_number']
    amount = data['amount']

    transfer_to_third_party_momo(sender_id, receiver_phone_number, amount)

    return jsonify(message='Money transferred to third-party momo successfully')

@app.route('/request_statements', methods=['POST'])
def request_statements_api():
    data = get_request_data()
    user_id = data['user_id']

    statements = request_statements(user_id)

    return jsonify(statements=statements)

@app.route('/check_user_data_privacy', methods=['POST'])
def check_user_data_privacy_api():
    data = get_request_data()
    user_id = data['user_id']
    requested_user_id = data['requested_user_id']

    is_allowed = check_user_data_privacy(user_id, requested_user_id)

    return jsonify(allowed=is_allowed)

@app.route('/save_charge_profit', methods=['POST'])
def save_charge_profit_api():
    data = get_request_data()
    user_id = data['user_id']
    amount = data['amount']

    save_charge_profit(user_id, amount)

    return jsonify(message='Charge profit saved successfully')

@app.route('/admin_get_statements', methods=['POST'])
def admin_get_statements_api():
    data = get_request_data()
    admin_id = data['admin_id']

    statements = admin_get_statements(admin_id)

    return jsonify(statements=statements)

def is_valid_email(email):
    email_regex = r'^\S+@\S+\.\S+$'
    return re.match(email_regex, email) is not None

def generate_account_number():
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

if __name__ == '__main__':
    app.run(debug=True)
