from flask import Flask, request, jsonify
import sqlite3
import time

app = Flask(__name__)

# --- Инициализация базы данных ---
def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    # Добавляем тестовые товары, если таблица пуста
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        products = [
            ('Ноутбук', 59999.99, 50),
            ('Смартфон', 29999.99, 100),
            ('Наушники', 4999.99, 200),
            ('Клавиатура', 2999.99, 150),
            ('Мышь', 1499.99, 300),
        ]
        cursor.executemany(
            'INSERT INTO products (name, price, stock) VALUES (?, ?, ?)',
            products
        )
    conn.commit()
    conn.close()

# --- Главная страница ---
@app.route('/')
def index():
    return '''
    <h1>Интернет-магазин "TechShop"</h1>
    <p>Добро пожаловать!</p>
    <ul>
        <li><a href="/products">Каталог товаров</a></li>
    </ul>
    '''

# --- Каталог товаров (GET — запрос к БД) ---
@app.route('/products')
def products():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, price, stock FROM products')
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            'id': row[0],
            'name': row[1],
            'price': row[2],
            'stock': row[3]
        })
    return jsonify(result)

# --- Регистрация пользователя (POST — запись в БД) ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '')
    email = data.get('email', '')
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'Все поля обязательны'}), 400

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, password)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500
    conn.close()
    return jsonify({'message': 'Пользователь зарегистрирован', 'user_id': user_id}), 201

# --- Добавление товара в корзину (POST — запись в БД) ---
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json() if request.is_json else request.form
    user_id = data.get('user_id', '')
    product_id = data.get('product_id', '')
    quantity = data.get('quantity', 1)

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # Проверяем наличие товара
    cursor.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    if not product:
        conn.close()
        return jsonify({'error': 'Товар не найден'}), 404

    # Добавляем в корзину
    try:
        cursor.execute(
            'INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)',
            (user_id, product_id, quantity)
        )
        # Уменьшаем остаток на складе
        cursor.execute(
            'UPDATE products SET stock = stock - ? WHERE id = ?',
            (quantity, product_id)
        )
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500
    conn.close()
    return jsonify({'message': 'Товар добавлен в корзину'}), 201

# --- Просмотр корзины (GET — запрос к БД) ---
@app.route('/cart/<int:user_id>')
def view_cart(user_id):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, p.name, p.price, c.quantity, (p.price * c.quantity) as total
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    items = []
    for row in rows:
        items.append({
            'cart_id': row[0],
            'product': row[1],
            'price': row[2],
            'quantity': row[3],
            'total': row[4]
        })
    return jsonify(items)


if __name__ == '__main__':
    init_db()
    # threaded=True чтобы обрабатывать несколько запросов
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)