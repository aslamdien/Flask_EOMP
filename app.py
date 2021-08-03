import hmac
import sqlite3

from flask_cors import CORS
from flask import Flask, request, jsonify, render_template
from flask_jwt import JWT, jwt_required, current_identity


class User(object):
    def __init__(self,id, username, password):
        self.id = id
        self.username = username
        self.password = password

def fetch_users():
    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM register')
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[5], data[6]))
    return new_data


users = fetch_users()


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
    conn = sqlite3.connect('flask_EOMP.db')
    conn.execute("CREATE TABLE IF NOT EXISTS product(product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "product_name TEXT NOT NULL,"
                 "description TEXT NOT NULL,"
                 "price TEXT NOT NULL,"
                 "product_image BLOB NOT NULL)")


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

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


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
            response['description'] = 'Registration Successful'
            response['status_code'] = 201
        return response


@app.route('/show-products/', methods=['GET'])
def get_blogs():
    response = {}

    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM product')

        product = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = product
    return response


@app.route('/add-product/', methods=['POST'])
def add_product():
    response = {}

    if request.method == 'POST':
        product_name = request.form['product_name']
        description = request.form['description']
        price = request.form['price']
        product_image = request.form['product_image']

        with sqlite3.connect('flask_EOMP.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO product('
                           'product_name,'
                           'description,'
                           'price,'
                           'product_image,) VALUES(?,?,?,?)', (product_name, description, price, product_image))
            conn.commit()
            response['status_code'] = 201
            response['description'] = 'New Product Has Been Added'
        return response

@app.route('/view-product/<int:product_id>', methods=['GET'])
def view_product(product_id):
    response = {}

    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM product WHERE produt_id='+ str(product_id))

        response['status_code'] = 200
        response['description'] = 'Product Successfully Retrieved'
        response['data'] = cursor.fetchone()

    return jsonify(response)

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
                    cursor.execute('UPDATE product SET product_name =? WHERE product_id=?', (put_data['product_name'], product_id))
                    conn.commit()
                    response['message'] = 'Product Name Updated Successfully'
                    response['status_code'] = 200

            if incoming_data.get('description') is not None:
                put_data['description'] = incoming_data.get('description')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET description =? WHERE product_id=?', (put_data['description'], product_id))
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
                put_data['product_image'] = incoming_data.get('product_image')

                with sqlite3.connect('flask_EOMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET product_image =? WHERE product_id=?', (put_data['product_image'], product_id))
                    conn.commit()
                    response['message'] = 'Product Image Updated Successfully'
                    response['status_code'] = 200
    return response


@app.route('/delete-product/<int:product_id>')
def delete_product(product_id):
    response = {}

    with sqlite3.connect('flask_EOMP.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM product WHERE product_id=' + str(product_id))
        conn.commit()
        response['status_code'] = 204
        response['message'] = 'Product Has Been Deleted'
    return response
