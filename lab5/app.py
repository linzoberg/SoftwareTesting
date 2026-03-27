from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import sqlite3
import hashlib
import random
import string
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_testing_2025'


# ==================== БАЗА ДАННЫХ ====================

def get_db():
    """Получить соединение с БД (каждый раз новое — имитация реальной нагрузки)."""
    conn = sqlite3.connect('shop.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализация базы данных с таблицами и тестовыми данными."""
    conn = get_db()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица категорий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT ''
        )
    ''')

    # Таблица товаров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            price REAL NOT NULL,
            old_price REAL DEFAULT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            category_id INTEGER,
            rating REAL DEFAULT 0.0,
            reviews_count INTEGER DEFAULT 0,
            image_url TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')

    # Таблица корзины
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Таблица заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'new',
            delivery_address TEXT DEFAULT '',
            payment_method TEXT DEFAULT 'card',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Таблица позиций заказа
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Таблица отзывов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            text TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # ===== Заполняем тестовыми данными =====
    cursor.execute('SELECT COUNT(*) FROM categories')
    if cursor.fetchone()[0] == 0:
        categories = [
            ('Ноутбуки', 'Ноутбуки для работы, учёбы и игр'),
            ('Смартфоны', 'Мобильные телефоны и аксессуары'),
            ('Наушники', 'Проводные и беспроводные наушники'),
            ('Периферия', 'Клавиатуры, мыши и коврики'),
            ('Мониторы', 'Мониторы для работы и гейминга'),
            ('Планшеты', 'Планшеты и электронные книги'),
            ('Комплектующие', 'Процессоры, видеокарты, память'),
            ('Сетевое оборудование', 'Роутеры, свитчи, кабели'),
        ]
        cursor.executemany(
            'INSERT INTO categories (name, description) VALUES (?, ?)',
            categories
        )

    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        products = [
            # Ноутбуки (category_id = 1)
            ('ASUS VivoBook 15', 'Intel Core i5, 8GB RAM, 512GB SSD, 15.6" FHD', 54999.99, 62999.99, 25, 1, 4.5, 128),
            ('Lenovo IdeaPad 3', 'AMD Ryzen 5, 8GB RAM, 256GB SSD, 15.6" FHD', 42999.99, None, 40, 1, 4.2, 95),
            ('HP Pavilion 14', 'Intel Core i7, 16GB RAM, 512GB SSD, 14" FHD', 69999.99, 74999.99, 15, 1, 4.7, 203),
            ('Acer Aspire 5', 'Intel Core i5, 8GB RAM, 512GB SSD, 15.6" FHD', 47999.99, None, 35, 1, 4.3, 156),
            ('MacBook Air M2', 'Apple M2, 8GB RAM, 256GB SSD, 13.6" Retina', 109999.99, 119999.99, 10, 1, 4.9, 312),

            # Смартфоны (category_id = 2)
            ('Samsung Galaxy S24', '6.2" AMOLED, Snapdragon 8 Gen 3, 128GB', 79999.99, 89999.99, 50, 2, 4.6, 245),
            ('iPhone 15', '6.1" OLED, A16 Bionic, 128GB', 84999.99, None, 30, 2, 4.8, 567),
            ('Xiaomi 14', '6.36" AMOLED, Snapdragon 8 Gen 3, 256GB', 59999.99, 64999.99, 60, 2, 4.4, 189),
            ('Google Pixel 8', '6.2" OLED, Tensor G3, 128GB', 54999.99, None, 20, 2, 4.5, 134),
            ('OnePlus 12', '6.82" AMOLED, Snapdragon 8 Gen 3, 256GB', 64999.99, 69999.99, 45, 2, 4.3, 98),
            ('Realme GT 5 Pro', '6.78" AMOLED, Snapdragon 8 Gen 3, 256GB', 44999.99, None, 70, 2, 4.1, 67),

            # Наушники (category_id = 3)
            ('Sony WH-1000XM5', 'Беспроводные, шумоподавление, 30 часов', 29999.99, 34999.99, 80, 3, 4.8, 432),
            ('Apple AirPods Pro 2', 'TWS, шумоподавление, MagSafe', 24999.99, None, 100, 3, 4.7, 389),
            ('JBL Tune 520BT', 'Беспроводные накладные, 57 часов', 3999.99, 4999.99, 200, 3, 4.2, 156),
            ('Sennheiser HD 560S', 'Открытые проводные, аудиофильские', 14999.99, None, 30, 3, 4.6, 87),
            ('Marshall Major IV', 'Беспроводные накладные, 80 часов', 8999.99, 10999.99, 60, 3, 4.4, 201),

            # Периферия (category_id = 4)
            ('Logitech MX Keys', 'Беспроводная клавиатура, подсветка', 9999.99, 11999.99, 90, 4, 4.5, 178),
            ('Razer DeathAdder V3', 'Игровая мышь, 30000 DPI', 7999.99, None, 120, 4, 4.6, 234),
            ('SteelSeries Apex Pro', 'Механическая клавиатура, OmniPoint', 19999.99, 22999.99, 40, 4, 4.7, 145),
            ('Logitech G502 X', 'Игровая мышь, LIGHTFORCE', 6499.99, 7999.99, 150, 4, 4.4, 312),
            ('HyperX Pulsefire Haste 2', 'Игровая мышь, 53г, 26000 DPI', 4999.99, None, 100, 4, 4.3, 89),

            # Мониторы (category_id = 5)
            ('Samsung Odyssey G5', '27" QHD, 165Hz, VA, 1ms', 24999.99, 29999.99, 20, 5, 4.4, 167),
            ('LG UltraGear 27GP850', '27" QHD, 180Hz, IPS, 1ms', 32999.99, None, 15, 5, 4.6, 198),
            ('Dell S2722QC', '27" 4K, 60Hz, IPS, USB-C', 29999.99, 34999.99, 25, 5, 4.5, 134),
            ('ASUS TUF Gaming VG249Q', '24" FHD, 144Hz, IPS, 1ms', 16999.99, None, 50, 5, 4.3, 267),

            # Планшеты (category_id = 6)
            ('iPad Air M1', '10.9" Liquid Retina, M1, 64GB', 54999.99, 59999.99, 30, 6, 4.7, 289),
            ('Samsung Galaxy Tab S9', '11" AMOLED, Snapdragon 8 Gen 2, 128GB', 62999.99, None, 20, 6, 4.5, 145),
            ('Xiaomi Pad 6', '11" IPS, Snapdragon 870, 128GB', 29999.99, 34999.99, 55, 6, 4.3, 178),

            # Комплектующие (category_id = 7)
            ('AMD Ryzen 7 7800X3D', 'Процессор, AM5, 8 ядер, 4.2-5.0 GHz', 34999.99, 39999.99, 40, 7, 4.9, 456),
            ('NVIDIA RTX 4070', 'Видеокарта, 12GB GDDR6X', 54999.99, 59999.99, 15, 7, 4.7, 334),
            ('Kingston Fury Beast 32GB', 'DDR5-5600, 2x16GB, CL36', 8999.99, None, 100, 7, 4.5, 212),
            ('Samsung 990 Pro 1TB', 'NVMe SSD, 7450/6900 MB/s', 9999.99, 12999.99, 75, 7, 4.8, 378),

            # Сетевое (category_id = 8)
            ('TP-Link Archer AX73', 'Wi-Fi 6, AX5400, 6 антенн', 7999.99, 9999.99, 60, 8, 4.4, 189),
            ('ASUS RT-AX86U', 'Wi-Fi 6, AX5700, Gaming', 14999.99, None, 25, 8, 4.6, 134),
            ('Keenetic Giga KN-1012', 'Wi-Fi 6, AX1800, Mesh', 9999.99, 11999.99, 45, 8, 4.5, 223),
        ]
        cursor.executemany(
            '''INSERT INTO products 
               (name, description, price, old_price, stock, category_id, rating, reviews_count) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            products
        )

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ==================== МАРШРУТЫ: СТРАНИЦЫ ====================

@app.route('/')
def index():
    """Главная страница с популярными товарами."""
    conn = get_db()
    # Популярные товары (по рейтингу)
    popular = conn.execute(
        '''SELECT p.*, c.name as category_name 
           FROM products p 
           JOIN categories c ON p.category_id = c.id 
           ORDER BY p.rating DESC LIMIT 8'''
    ).fetchall()
    # Товары со скидкой
    sales = conn.execute(
        '''SELECT p.*, c.name as category_name 
           FROM products p 
           JOIN categories c ON p.category_id = c.id 
           WHERE p.old_price IS NOT NULL 
           ORDER BY (p.old_price - p.price) DESC LIMIT 4'''
    ).fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    return render_template('index.html', popular=popular, sales=sales, categories=categories)


@app.route('/catalog')
@app.route('/catalog/<int:category_id>')
def catalog(category_id=None):
    """Каталог товаров с фильтрацией и сортировкой."""
    conn = get_db()
    sort = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    page = request.args.get('page', 1, type=int)
    per_page = 12

    sort_options = {
        'name': 'p.name', 'price': 'p.price',
        'rating': 'p.rating', 'date': 'p.created_at'
    }
    sort_col = sort_options.get(sort, 'p.name')
    order_dir = 'DESC' if order == 'desc' else 'ASC'

    query = '''SELECT p.*, c.name as category_name 
               FROM products p 
               JOIN categories c ON p.category_id = c.id WHERE 1=1'''
    params = []

    if category_id:
        query += ' AND p.category_id = ?'
        params.append(category_id)
    if min_price is not None:
        query += ' AND p.price >= ?'
        params.append(min_price)
    if max_price is not None:
        query += ' AND p.price <= ?'
        params.append(max_price)

    # Считаем общее количество
    count_query = query.replace(
        'SELECT p.*, c.name as category_name',
        'SELECT COUNT(*)'
    )
    total = conn.execute(count_query, params).fetchone()[0]
    total_pages = max(1, (total + per_page - 1) // per_page)

    query += f' ORDER BY {sort_col} {order_dir} LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])

    products = conn.execute(query, params).fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()

    current_category = None
    if category_id:
        current_category = conn.execute(
            'SELECT * FROM categories WHERE id = ?', (category_id,)
        ).fetchone()

    conn.close()
    return render_template('catalog.html',
                           products=products, categories=categories,
                           current_category=current_category,
                           page=page, total_pages=total_pages,
                           sort=sort, order=order)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Страница товара с отзывами."""
    conn = get_db()
    product = conn.execute(
        '''SELECT p.*, c.name as category_name 
           FROM products p 
           JOIN categories c ON p.category_id = c.id 
           WHERE p.id = ?''', (product_id,)
    ).fetchone()

    if not product:
        conn.close()
        return 'Товар не найден', 404

    reviews = conn.execute(
        '''SELECT r.*, u.username 
           FROM reviews r 
           JOIN users u ON r.user_id = u.id 
           WHERE r.product_id = ? 
           ORDER BY r.created_at DESC LIMIT 10''', (product_id,)
    ).fetchall()

    # Похожие товары
    similar = conn.execute(
        '''SELECT * FROM products 
           WHERE category_id = ? AND id != ? 
           ORDER BY rating DESC LIMIT 4''',
        (product['category_id'], product_id)
    ).fetchall()

    conn.close()
    return render_template('product.html',
                           product=product, reviews=reviews, similar=similar)


@app.route('/search')
def search():
    """Поиск товаров."""
    q = request.args.get('q', '').strip()
    conn = get_db()
    products = []
    if q:
        products = conn.execute(
            '''SELECT p.*, c.name as category_name 
               FROM products p 
               JOIN categories c ON p.category_id = c.id 
               WHERE p.name LIKE ? OR p.description LIKE ? 
               ORDER BY p.rating DESC''',
            (f'%{q}%', f'%{q}%')
        ).fetchall()
    conn.close()
    return render_template('search.html', products=products, query=q)


# ==================== МАРШРУТЫ: РЕГИСТРАЦИЯ / ВХОД ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    # POST — может быть JSON (от JMeter) или форма
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()

    if not username or not email or not password:
        if request.is_json:
            return jsonify({'error': 'Все обязательные поля должны быть заполнены'}), 400
        flash('Все обязательные поля должны быть заполнены', 'error')
        return render_template('register.html')

    conn = get_db()
    try:
        conn.execute(
            '''INSERT INTO users (username, email, password_hash, first_name, last_name) 
               VALUES (?, ?, ?, ?, ?)''',
            (username, email, hash_password(password), first_name, last_name)
        )
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()

        if request.is_json:
            return jsonify({'message': 'Регистрация успешна', 'user_id': user_id}), 201
        session['user_id'] = user_id
        session['username'] = username
        return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        conn.close()
        if request.is_json:
            return jsonify({'error': 'Пользователь с таким именем или email уже существует'}), 409
        flash('Пользователь с таким именем или email уже существует', 'error')
        return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    username = data.get('username', '')
    password = data.get('password', '')

    conn = get_db()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password_hash = ?',
        (username, hash_password(password))
    ).fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        if request.is_json:
            return jsonify({'message': 'Вход выполнен', 'user_id': user['id']}), 200
        return redirect(url_for('index'))

    if request.is_json:
        return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401
    flash('Неверное имя пользователя или пароль', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ==================== МАРШРУТЫ: КОРЗИНА ====================

@app.route('/cart')
def cart():
    user_id = session.get('user_id')
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return redirect(url_for('login'))

    conn = get_db()
    items = conn.execute(
        '''SELECT c.id as cart_id, c.quantity, p.id as product_id, 
                  p.name, p.price, (p.price * c.quantity) as subtotal
           FROM cart c 
           JOIN products p ON c.product_id = p.id 
           WHERE c.user_id = ?''', (user_id,)
    ).fetchall()

    total = sum(item['subtotal'] for item in items)
    conn.close()
    return render_template('cart.html', items=items, total=total)


@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if request.is_json:
        data = request.get_json()
        user_id = data.get('user_id') or session.get('user_id')
    else:
        data = request.form
        user_id = session.get('user_id')

    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return redirect(url_for('login'))

    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    conn = get_db()

    # Проверяем товар и остаток
    product = conn.execute(
        'SELECT * FROM products WHERE id = ?', (product_id,)
    ).fetchone()

    if not product:
        conn.close()
        if request.is_json:
            return jsonify({'error': 'Товар не найден'}), 404
        flash('Товар не найден', 'error')
        return redirect(url_for('catalog'))

    if product['stock'] < quantity:
        conn.close()
        if request.is_json:
            return jsonify({'error': 'Недостаточно товара на складе'}), 400
        flash('Недостаточно товара на складе', 'error')
        return redirect(url_for('product_detail', product_id=product_id))

    # Проверяем, есть ли уже в корзине
    existing = conn.execute(
        'SELECT * FROM cart WHERE user_id = ? AND product_id = ?',
        (user_id, product_id)
    ).fetchone()

    if existing:
        conn.execute(
            'UPDATE cart SET quantity = quantity + ? WHERE id = ?',
            (quantity, existing['id'])
        )
    else:
        conn.execute(
            'INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)',
            (user_id, product_id, quantity)
        )

    conn.commit()
    conn.close()

    if request.is_json:
        return jsonify({'message': 'Товар добавлен в корзину'}), 201
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db()
    conn.execute('DELETE FROM cart WHERE id = ? AND user_id = ?', (cart_id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('cart'))


# ==================== МАРШРУТЫ: ЗАКАЗ ====================

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.is_json:
        data = request.get_json()
        user_id = data.get('user_id') or session.get('user_id')
    else:
        user_id = session.get('user_id')

    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return redirect(url_for('login'))

    conn = get_db()
    items = conn.execute(
        '''SELECT c.*, p.name, p.price, p.stock,
                  (p.price * c.quantity) as subtotal
           FROM cart c 
           JOIN products p ON c.product_id = p.id 
           WHERE c.user_id = ?''', (user_id,)
    ).fetchall()

    if not items:
        conn.close()
        if request.is_json:
            return jsonify({'error': 'Корзина пуста'}), 400
        flash('Корзина пуста', 'error')
        return redirect(url_for('cart'))

    total = sum(item['subtotal'] for item in items)

    if request.method == 'GET' and not request.is_json:
        conn.close()
        return render_template('checkout.html', items=items, total=total)

    # Оформление заказа (POST)
    if request.is_json:
        address = data.get('address', 'Тестовый адрес')
        payment = data.get('payment_method', 'card')
    else:
        address = request.form.get('address', '')
        payment = request.form.get('payment_method', 'card')

    try:
        # Создаём заказ
        conn.execute(
            '''INSERT INTO orders (user_id, total_amount, delivery_address, payment_method) 
               VALUES (?, ?, ?, ?)''',
            (user_id, total, address, payment)
        )
        order_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Переносим товары из корзины в заказ и обновляем остатки
        for item in items:
            conn.execute(
                'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                (order_id, item['product_id'], item['quantity'], item['price'])
            )
            conn.execute(
                'UPDATE products SET stock = stock - ? WHERE id = ?',
                (item['quantity'], item['product_id'])
            )

        # Очищаем корзину
        conn.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

        if request.is_json:
            return jsonify({
                'message': 'Заказ оформлен',
                'order_id': order_id,
                'total': total
            }), 201
        return render_template('order_success.html', order_id=order_id, total=total)

    except Exception as e:
        conn.close()
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Ошибка при оформлении заказа: {e}', 'error')
        return redirect(url_for('cart'))


# ==================== МАРШРУТЫ: ОТЗЫВЫ ====================

@app.route('/review/add', methods=['POST'])
def add_review():
    if request.is_json:
        data = request.get_json()
        user_id = data.get('user_id') or session.get('user_id')
    else:
        data = request.form
        user_id = session.get('user_id')

    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return redirect(url_for('login'))

    product_id = data.get('product_id')
    rating = int(data.get('rating', 5))
    text = data.get('text', '')

    conn = get_db()
    conn.execute(
        'INSERT INTO reviews (product_id, user_id, rating, text) VALUES (?, ?, ?, ?)',
        (product_id, user_id, rating, text)
    )
    # Обновляем средний рейтинг
    avg = conn.execute(
        'SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?',
        (product_id,)
    ).fetchone()
    conn.execute(
        'UPDATE products SET rating = ?, reviews_count = ? WHERE id = ?',
        (round(avg[0], 1), avg[1], product_id)
    )
    conn.commit()
    conn.close()

    if request.is_json:
        return jsonify({'message': 'Отзыв добавлен'}), 201
    return redirect(url_for('product_detail', product_id=product_id))


# ==================== API (для JMeter JSON-запросов) ====================

@app.route('/api/products')
def api_products():
    conn = get_db()
    products = conn.execute(
        '''SELECT p.*, c.name as category_name 
           FROM products p 
           JOIN categories c ON p.category_id = c.id'''
    ).fetchall()
    conn.close()
    return jsonify([dict(p) for p in products])


@app.route('/api/product/<int:product_id>')
def api_product(product_id):
    conn = get_db()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product:
        return jsonify(dict(product))
    return jsonify({'error': 'Не найден'}), 404


@app.route('/api/cart/<int:user_id>')
def api_cart(user_id):
    conn = get_db()
    items = conn.execute(
        '''SELECT c.id, p.name, p.price, c.quantity, (p.price * c.quantity) as total
           FROM cart c JOIN products p ON c.product_id = p.id
           WHERE c.user_id = ?''', (user_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])


# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("Интернет-магазин TechShop запущен!")
    print("http://127.0.0.1:5000")
    print("=" * 50)
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)