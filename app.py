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


# creating a class called users, part of the flask application configuration
class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


# creating a function to get all the users from the register table
def fetch_users():
    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM register')
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[5], data[6])) # getting the id, username and password
    return new_data


users = fetch_users()


# Creating Register Table for Users
def user_table():
    conn = sqlite3.connect('flask_EOMP.db')
    print("Database Opened")

    conn.execute("CREATE TABLE IF NOT EXISTS register(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "name TEXT NOT NULL,"
                 "surname TEXT NOT NULL,"
                 "id_number INTEGER NOT NULL,"
                 "email TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
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
        product_image = request.files['product_image']
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
CORS(app)                                                # allows you to use api
app.debug = True                                         # when finds a bug, it continues to run
app.config['SECRET_KEY'] = 'super-secret'                # a random key used to encrypt your web app
app.config["JWT_EXPIRATION_DELTA"] = timedelta(days=1)   # allows token to last a day

app.config['MAIL_SERVER'] = 'smtp.gmail.com'             # Code For Sending Emails Through Flask
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'aslamdien90@gmail.com'
app.config['MAIL_PASSWORD'] = 'nitrocharge'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)                                         # Code For Sending Emails Ends

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
        name = request.json['name']
        surname = request.json['surname']
        id_number = request.json['id_number']
        email = request.json['email']
        username = request.json['username']
        password = request.json['password']

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

                    msg = Message('Welcome New User', sender='aslamdien90@gmail.com', recipients=[email])
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
@jwt_required()
def add_product():
    response = {}

    if request.method == 'POST':
        product_name = request.form['product_name']
        description = request.form['description']
        price = request.form['price']

        with sqlite3.connect('flask_EOMP.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO product(product_name,'
                           'description,'
                           'price,'
                           'product_image) VALUES(?,?,?,?)', (product_name, description, price, upload_file()))
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
@jwt_required()
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


# a route to delete products
@app.route('/delete-product/<int:product_id>')
@jwt_required()
def delete_product(product_id):
    response = {}

    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM product WHERE product_id=' + str(product_id))
        conn.commit()
        response['status_code'] = 204
        response['message'] = 'Product Has Been Deleted'
    return response


if __name__ == '__main__':
    app.run()
