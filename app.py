import hmac
import sqlite3
from datetime import datetime, timedelta
import re
import rsaidnumber

from flask_cors import CORS
from flask_mail import Mail, Message
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_users():
    with sqlite3.connect('practice.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM register')
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[5], data[6]))
    return new_data


users = fetch_users()


def convertToBinaryData():
    filename = '...'# Convert digital data to binary format
    with open(filename, 'rb') as file:
        photo = file.read()
    return photo


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
    print("register table created")
    conn.close()


def product_table():
    conn = sqlite3.connect('practice2.db')
    conn.execute("CREATE TABLE IF NOT EXISTS product2(product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "product_name TEXT NOT NULL,"
                 "description TEXT NOT NULL,"
                 "price TEXT NOT NULL,"
                 "product_image TEXT NOT NULL)")
    print('Product table Created')
    conn.close()


user_table()
product_table()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
CORS(app)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config["JWT_EXPIRATION_DELTA"] = timedelta(hours=24)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'aslamdien90@gmail.com'
app.config['MAIL_PASSWORD'] = 'nitrocharge'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/register/', methods=['POST'])
def register():
    response = {}

    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        id_number = request.form['id_number']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        if re.search(regex, email):
            try:
                id_number = rsaidnumber.parse(id_number)
                age = str((datetime.today() - id_number.date_of_birth) // timedelta(365.25))

                if int(age) >= 18:
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

                        msg = Message('Welcome To My Point Of Sale', sender='aslamdien90@gmail.com', recipients=[email])
                        msg.subject = 'New User'
                        msg.body = "Thank You for registering with us " + name + "."
                        msg.body = "Don't forget your Username: " + username + " and Password: " + password + "."
                        mail.send(msg)
                        response['description'] = 'Registration Successful'
                        response['status_code'] = 201

                elif int(age) < 18:
                        year = str(int(age) - 18)
                        response['message']="Sorry", "Your Are Too Young to Play. Please Try Again In " + year + " Year(s)"
                else:
                    response['message'] = 'Email Invalid, Please Valid Email Address'
            except ValueError:
                if id_number != int:
                    response['message'] = "This Is Not An ID Number"
            return response


@app.route('/show-products/', methods=['GET'])
def get_blogs():
    response = {}

    with sqlite3.connect('practice.db') as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute('SELECT * FROM product')

        product = cursor.fetchall()
        data = []

        for i in product:
            data.append({u: i[u] for u in i.keys()})

    response['status_code'] = 200
    return jsonify(data, response)


@app.route('/add-product/', methods=['POST'])
def add_product():
    response = {}

    if request.method == 'POST':
        product_name = request.form['product_name']
        description = request.form['description']
        price = request.form['price']
        product_image = request.files['product_image']

        with sqlite3.connect('flask_EOMP.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO product2(product_name, description, price, product_image) VALUES(?,?,?,?)', (product_name, description, str('R') + price, product_image))
            conn.commit()
            response['status_code'] = 201
            response['description'] = 'New Product Has Been Added'
        return response


@app.route('/view-product/<int:product_id>', methods=['GET'])
def view_product(product_id):
    response = {}

    with sqlite3.connect('practice.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM product WHERE product_id=' + str(product_id))

        response['status_code'] = 200
        response['description'] = 'Product Successfully Retrieved'
        response['data'] = cursor.fetchone()

    return jsonify(response)


@app.route('/edit-product/<int:product_id>', methods=['PUT'])
def edit_product(product_id):
    response = {}

    if request.method == 'PUT':
        with sqlite3.connect('practice.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get('product_name') is not None:
                put_data['product_name'] = incoming_data.get('product_name')

                with sqlite3.connect('practice.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET product_name =? WHERE product_id=?',
                                   (put_data['product_name'], product_id))
                    conn.commit()
                    response['message'] = 'Product Name Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('description') is not None:
                put_data['description'] = incoming_data.get('description')

                with sqlite3.connect('practice.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET description =? WHERE product_id=?',
                                   (put_data['description'], product_id))
                    conn.commit()
                    response['message'] = 'Item Description Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('price') is not None:
                put_data['price'] = incoming_data.get('price')

                with sqlite3.connect('practice.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET price =? WHERE product_id=?', (put_data['price'], product_id))
                    conn.commit()
                    response['message'] = 'Product Price Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('product_image') is not None:
                put_data['product_image'] = incoming_data.get('product_image')

                with sqlite3.connect('practice.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET product_image =? WHERE product_id=?',
                                   (put_data['product_image'], product_id))
                    conn.commit()
                    response['message'] = 'Product Image Updated Successfully'
                    response['status_code'] = 200
    return response


@app.route('/delete-product/<int:product_id>')
def delete_product(product_id):
    response = {}

    with sqlite3.connect('practice.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM product WHERE product_id=' + str(product_id))
        conn.commit()
        response['status_code'] = 204
        response['message'] = 'Product Has Been Deleted'
    return response


if __name__ == '__main__':
    app.run()
