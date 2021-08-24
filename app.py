import hmac
import sqlite3
from datetime import datetime, timedelta
import re
import rsaidnumber
import cloudinary
import cloudinary.uploader

from flask_cors import CORS
from flask_mail import Mail, Message
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.utils import redirect


# creating a class called users, part of the flask application configuration
class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


# creating a function to get all the users from the register table


# Creating Register Table for Users
def user_table():
    conn = sqlite3.connect('flask_EOMP.db')
    print("Database Opened")

    conn.execute("CREATE TABLE IF NOT EXISTS register("
                 "name TEXT NOT NULL,"
                 "surname TEXT NOT NULL,"
                 "id_number INTEGER NOT NULL,"
                 "email TEXT NOT NULL,"
                 "username TEXT NOT NULL PRIMARY KEY,"
                 "password TEXT NOT NULL)")
    print("User table created")
    conn.close()


# Creating Product Table
def product_table():
    conn = sqlite3.connect('flask_EOMP.db')
    conn.execute("CREATE TABLE IF NOT EXISTS product(product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "product_name TEXT NOT NULL,"
                 "description TEXT NOT NULL,"
                 "price TEXT NOT NULL,"
                 "product_image TEXT NOT NULL)")
    print('Product table Created')
    conn.close()


def fetch_users():
    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM register')
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[2], data[4], data[5])) # getting the id, username and password
    return new_data


users = fetch_users()

user_table()
product_table()


# function to take image uploads and convert them into urls
def upload_file():
    app.logger.info('in upload route')
    cloudinary.config(cloud_name = "dbcczql4w",
                      api_key = "138784466689969",
                      api_secret = "Nw8Wv4yVQaFk7I8gu1PHt2OcPxQ"
                      )
    upload_result = None
    if request.method == 'POST' or request.method == 'PUT':
        product_image = request.json['product_image']
        app.logger.info('%s file_to_upload', product_image)
        if product_image:
            upload_result = cloudinary.uploader.upload(product_image)
            app.logger.info(upload_result)
            return upload_result['url']


# Code For Authorization Token
def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


# Flask application
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})           # allows you to use api
app.debug = True                                         # when finds a bug, it continues to run
app.config['SECRET_KEY'] = 'super-secret'                # a random key used to encrypt your web app
app.config["JWT_EXPIRATION_DELTA"] = timedelta(days=1)   # allows token to last a day
app.config['MAIL_SERVER'] = 'smtp.gmail.com'             # Code For Sending Emails Through Flask
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = '081698work@gmail.com'
app.config['MAIL_PASSWORD'] = 'open@123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)                                         # Code For Sending Emails Ends
app.config['TESTING'] = True
app.config['CORS_HEADERS'] = ['Content-Type']

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


# A Route To Register A New User
@app.route('/register/', methods=['POST'])
def register():
    response = {}

    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        id_number = request.form['id_number']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        try:
            regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
            if re.search(regex, email) and rsaidnumber.parse(id_number):
                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO register('
                                   'name,'
                                   'surname,'
                                   'id_number,'
                                   'email,'
                                   'username,'
                                   'password) VALUES(?,?,?,?,?,?)', (name, surname, id_number, email, username, password))
                    conn.commit()

                    msg = Message('Welcome New User', sender='081698work@gmail.com', recipients=[email])
                    msg.subject = 'New User'
                    msg.body = "Thank You for registering with us " + name + "."
                    msg.body = "Don't forget your Username: " + username + " and Password: " + password + "."
                    mail.send(msg)
                    response['description'] = 'Registration Successful'
                    response['status_code'] = 201

            else:
                response['message'] = "Invalid Email Address"
        except ValueError:
            response['message'] = "ID Number Invalid"
        return response


# a route with a function to send the users their details
@app.route('/reset-password/', methods=["POST"])
def details():
    response = {}

    if request.method == "POST":
        email = request.form['email']

        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if re.search(regex, email):
            with sqlite3.connect("flask_EOMP.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM register WHERE email='" + str(email) + "'")
                details = cursor.fetchall()[0]

                msg = Message('Password Information', sender='081698work@gmail.com', recipients=[email])
                msg.body = "Here Is Your Information " + str(details[0]) + ". \nUsername: " + str(details[4]) + "\nPassword: " + str(details[5]) + '\n Don`t Lose It Again!!'

                mail.send(msg)

                response["message"] = "Success, Check Email"
                response["status_code"] = 201

        else:
            response['message'] = "Invalid Email Address"

    return response


# a route to view all the Registered users
@app.route('/show-users/', methods=["GET"])
def show_users():
    response = {}

    with sqlite3.connect("flask_EOMP.db") as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute("SELECT * FROM register")

        people = cursor.fetchall()
        data = []

        for i in people:
            data.append({u: i[u] for u in i.keys()})

    response['data'] = data
    return jsonify(response)


# a route to view a user
@app.route('/view-user/<int:user_id>', methods=["GET"])
#@jwt_required()
def view_user(user_id):
    response = {}
    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM register WHERE user_id='" + str(user_id) + "'")
        response["status_code"] = 200
        response["description"] = "User retrieved successfully"
        response["data"] = cursor.fetchone()
    return jsonify(response)


# A Route To View All Products
@app.route('/show-products/', methods=['GET'])
def view_products():
    response = {}

    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute('SELECT * FROM product')

        product = cursor.fetchall()
        data = []

        for i in product:
            data.append({u: i[u] for u in i.keys()})

    response['data'] = data
    return jsonify(response)


# A Route To Add A New Product
@app.route('/add-product/', methods=['POST'])
def add_product():
    response = {}

    if request.method == 'POST':
        product_name = request.json['product_name']
        description = request.json['description']
        price = request.json['price']
        product_image = upload_file()

        with sqlite3.connect('flask_EOMP.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO product(product_name,'
                           'description,'
                           'price,'
                           'product_image) VALUES(?,?,?,?)', (product_name, description, price, product_image))
            conn.commit()
            response['status_code'] = 201
            response['description'] = 'New Product Has Been Added'
    return response


# A Route to View A Specific Products
@app.route('/view-product/<int:product_id>', methods=['GET'])
def view_product(product_id):
    response = {}

    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM product WHERE product_id=' + str(product_id))

        response['status_code'] = 200
        response['description'] = 'Product Successfully Retrieved'
        response['data'] = cursor.fetchone()

    return jsonify(response)


# A Route To Edit A Specific Product
@app.route('/edit-product/<int:product_id>', methods=['PUT'])
def edit_product(product_id):
    response = {}

    if request.method == 'PUT':
        with sqlite3.connect('flask_EOMP.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get('product_name') is not None:
                put_data['product_name'] = incoming_data.get('product_name')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET product_name =? WHERE product_id=?',
                                   (put_data['product_name'], product_id))
                    conn.commit()
                    response['message'] = 'Product Name Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('description') is not None:
                put_data['description'] = incoming_data.get('description')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET description =? WHERE product_id=?',
                                   (put_data['description'], product_id))
                    conn.commit()
                    response['message'] = 'Item Description Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('price') is not None:
                put_data['price'] = incoming_data.get('price')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET price =? WHERE product_id=?', (put_data['price'], product_id))
                    conn.commit()
                    response['message'] = 'Product Price Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('product_image') is not None:
                put_data['product_image'] = upload_file()

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET product_image =? WHERE product_id=?',
                                   (put_data['product_image'], product_id))
                    conn.commit()
                    response['message'] = 'Product Image Updated Successfully'
                    response['status_code'] = 200
        return response


@app.route('/edit-user/<username>', methods=['PUT'])
def edit_user(username):
    response = {}

    if request.method == 'PUT':
        with sqlite3.connect('flask_EOMP.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get('name') is not None:
                put_data['name'] = incoming_data.get('name')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE register SET name =? WHERE username=?',
                                   (put_data['name'], username))
                    conn.commit()
                    response['message'] = 'Name Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('surname') is not None:
                put_data['surname'] = incoming_data.get('surname')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET surname =? WHERE username=?',
                                   (put_data['surname'], username))
                    conn.commit()
                    response['message'] = 'Surname Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('id_number') is not None:
                put_data['id_number'] = incoming_data.get('id_number')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE register SET id_number =? WHERE username=?', (put_data['id_number'], username))
                    conn.commit()
                    response['message'] = 'ID Number Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('email') is not None:
                put_data['email'] = incoming_data.get('email')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE register SET email =? WHERE username=?',
                                   (put_data['email'], username))
                    conn.commit()
                    response['message'] = 'Email Address Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('username') is not None:
                put_data['username'] = incoming_data.get('username')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE register SET username=? WHERE username=?',
                                   (put_data['username'], username))
                    conn.commit()
                    response['message'] = 'username Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('password') is not None:
                put_data['password'] = incoming_data.get('password')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE register SET password =? WHERE username=?',
                                   (put_data['password'], username))
                    conn.commit()
                    response['message'] = 'password Updated Successfully'
                    response['status_code'] = 200
        return response


# A Route to delete products
@app.route('/delete-product/<int:product_id>')
# @jwt_required()
def delete_product(product_id):
    response = {}

    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM product WHERE product_id=' + str(product_id))
        conn.commit()
        response['status_code'] = 204
        response['message'] = 'Product Has Been Deleted'
    return response


@app.route('/delete-user/<username>')
def delete_user(username):
    response = {}

    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM register WHERE username='" + str(username) + "'")
        conn.commit()
        response['status_code'] = 204
        response['message'] = 'User Has Been Deleted'
    return response


if __name__ == '__main__':
    app.run()
