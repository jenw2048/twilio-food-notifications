from flask import Flask, jsonify 
import os
import flask, sqlite3, uuid, hashlib, datetime
from twilio.rest import Client

app = Flask(__name__)
app.config.update(
    APPLICATION_ROOT = '/',
    DB_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'var', 'db.sqlite3'
    )
)


class InvalidUsage(Exception):
    """Invalid Usage."""

    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        """Initialize invalid usage."""
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert."""
        r_v = dict(self.payload or ())
        r_v['message'] = self.message
        return r_v



@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    """Handle invalid usage."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response



################
# DB FUNCTIONS #
################
def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_db():
    if 'sqlite_db' not in flask.g:
        db_filename = app.config['DB_PATH']
        flask.g.sqlite_db = sqlite3.connect(db_filename)
        flask.g.sqlite_db.row_factory = dict_factory

        # Foreign keys have to be enabled per-connection.  This is an sqlite3
        # backwards compatibility thing.
        flask.g.sqlite_db.execute("PRAGMA foreign_keys = ON")

    return flask.g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    assert error or not error  # Needed to avoid superfluous style error
    sqlite_db = flask.g.pop('sqlite_db', None)
    if sqlite_db is not None:
        sqlite_db.commit()
        sqlite_db.close()



######################
# PASSWORD FUNCTIONS #
######################
def generate_hashed_password(plain_text_password):
    """Generate hashed password."""
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + plain_text_password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def verify_password_match(plain_text_password, db_password):
    """Verify password."""
    algorithm, salt, password_hash = db_password.split("$")
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + plain_text_password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string == db_password


class UserDetails:
    def __init__(self, username):
        self.username = username
    
    def to_dict(self):
        return ({
            "username": self.username
        })

class OrderStatus:
    PENDING = "pending"
    COLLECTED = "collected"
    DONE = "done"

class ClickType:
    REOPEN = "reopen"
    DONE = "done"
    COLLECTED = "collected"

class CustomerResponseType:
    call = "Call"
    sms = "SMS"
    whatsapp = "WhatsApp"



def contact_twilio(customer_phone_number, message, response_type=CustomerResponseType.sms):
    # Download the helper library from https://www.twilio.com/docs/python/install
    # Your Account Sid and Auth Token from twilio.com/console
    # DANGER! This is insecure. See http://twil.io/secure
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    account_phone_number = os.environ['TWILIO_PHONE_NUMBER']
    client = Client(account_sid, auth_token)

    if (response_type == CustomerResponseType.call):
        call = client.calls.create(
                        twiml='<Response><Say>' + str(message) + '</Say></Response>',
                        from_=account_phone_number,
                        to=customer_phone_number
                    )
        print(call.sid)
    elif (response_type == CustomerResponseType.whatsapp):
        message = client.messages.create(
                              body=message,
                              from_='whatsapp:' + account_phone_number,
                              to='whatsapp:' + customer_phone_number
                          )
        print(message.sid)
    else:
        message = client.messages \
                        .create(
                            body=message,
                            from_=account_phone_number,
                            to=customer_phone_number
                        )
        print(message.sid)



@app.route("/api/v1/order/<string:username>/<int:orderid>/", methods=['GET', 'POST', 'DELETE'])
def order(username, orderid):
    """Handles order status."""   
    # Establish connection
    connection = get_db()
    matching_users = connection.execute("SELECT * FROM users WHERE username=?",(username,)).fetchall()
    if len(matching_users) == 0:
        raise InvalidUsage('User does not exist!', status_code=404)
    matching_orders = connection.execute("SELECT * FROM orders WHERE orderid=?",(orderid,)).fetchall()
    if len(matching_orders) == 0:
        raise InvalidUsage('Order does not exist!', status_code=404)
    order = matching_orders[0]
    if order['owner'] != username:
        raise InvalidUsage('User does not own order!', status_code=403)

    # Handle Deletes
    if flask.request.method == 'DELETE':
        connection.execute("DELETE FROM orders WHERE orderid=?", (orderid,)).fetchall()
        return flask.jsonify({}), 204

    # A series of actions the owner can choose to perform.
    # If order is complete, owner can click on done. 
    # A text message is then sent to the customer.
    # Once the customer has picked up the order,
    # owner can click on `collected` and the order is removed.
    if flask.request.method == 'POST':
        if 'click_type' not in flask.request.args:
            raise InvalidUsage('User does not own order!', status_code=402)
        click_type = flask.request.args['click_type']
        
        if click_type == ClickType.DONE and order['status'] != OrderStatus.DONE:
            order['status'] = OrderStatus.DONE
            message = "Your order from " + matching_users[0]['business'] + " is ready for pickup!"
            contact_twilio(order['phone'], message, order['response_type'])

        elif click_type == ClickType.REOPEN and order['status'] == OrderStatus.DONE:
            order['status'] = OrderStatus.PENDING

        elif click_type == ClickType.COLLECTED and order['status'] == OrderStatus.DONE:
            order['status'] = OrderStatus.COLLECTED

        connection.execute("UPDATE orders SET status=? WHERE orderid=?", (order['status'], orderid))

    return flask.jsonify(order), 200



@app.route("/api/v1/orders/<string:username>/", methods=['GET', 'POST'])
def orders(username):
    # more like a homepage for our app
    connection = get_db()
    matching_users = connection.execute("SELECT * FROM users WHERE username=?",(username,)).fetchall()
    if len(matching_users) == 0:
        raise InvalidUsage('User does not exist!', status_code=404)

    # GET
    # display all orders
    if flask.request.method == 'GET':       
        return flask.jsonify(connection.execute("SELECT * FROM orders WHERE owner=?  ORDER BY created DESC", (username,)).fetchall()), 200

    # POST
    # owner adds a new order
    else:
        new_order = flask.request.get_json(force=True)
        connection.execute("INSERT INTO orders (description,phone,status,response_type,owner) VALUES(?, ?, ?, ?, ?)", (new_order['description'], new_order['phone'], OrderStatus.PENDING, new_order['response_type'], username))
        new_orderid = connection.execute("""
            SELECT last_insert_rowid()
            AS last;
        """).fetchall()[0]['last']
        return flask.jsonify({
            'orderid': new_orderid,
            'description': new_order['description'],
            'phone': new_order['phone'],
            'status': OrderStatus.PENDING,
            'response_type': new_order['response_type'],
            'owner': username,
            'created': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200

    

@app.route("/api/v1/login/", methods=['POST'])
def login():
    login_details = flask.request.get_json(force=True)
    username = login_details['username']
    password = login_details['password']
    connection = get_db()
    
    matching_users = connection.execute("SELECT * FROM users WHERE username=?",(username,)).fetchall()
    if len(matching_users) == 0:
        raise InvalidUsage('User does not exist!', status_code=404)

    matching_user = matching_users[0]
    if verify_password_match(password, matching_user['password']):
        return flask.jsonify({"username": matching_user['username']}), 200
    else:
        raise InvalidUsage('Password incorrect!', status_code=403)



# val businessName: String, val username: String, val email: String, val password: String)
@app.route("/api/v1/signup/", methods=['POST'])
def signup(): 
    signup_details = flask.request.get_json(force=True)
    username = signup_details['username']
    password = signup_details['password']
    email = signup_details['email']
    business = signup_details['business']
    connection = get_db()
    
    matching_users = connection.execute("SELECT * FROM users WHERE username=?",(username,)).fetchall()
    if len(matching_users) != 0:
        raise InvalidUsage('Username already exists!', status_code=409)
    
    connection.execute("INSERT INTO users (username,business,email,password) VALUES(?, ?, ?, ?)", (username, business, email, generate_hashed_password(password)))

    return flask.jsonify({"username": username}), 200



if __name__ == "__main__":
    app.run(port=8000, debug=True)