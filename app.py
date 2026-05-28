import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from urllib.parse import urlparse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shopfussion_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shopfussion.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='buyer')
    avatar = db.Column(db.String(200), default='default_avatar.png')
    avatar_data = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='seller', lazy=True)
    orders = db.relationship('Order', backref='buyer', lazy=True)
    wishlist_items = db.relationship('WishlistItem', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class ProductCharacteristic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(200), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image = db.Column(db.String(200), default='default_product.png')
    image_data = db.Column(db.LargeBinary, nullable=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    characteristics = db.relationship('ProductCharacteristic', backref='product', lazy=True, cascade='all, delete-orphan')

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OrderTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    description = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True)
    tracking = db.relationship('OrderTracking', backref='order', lazy=True, order_by='OrderTracking.created_at.desc()')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='wishlist_items', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)
    text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='reviews', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['seller', 'admin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

MONTHS_RU = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
             'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

@app.template_filter('rusdate')
def rusdate_filter(dt, fmt='%d %B %Y'):
    if dt is None:
        return ''
    result = dt.strftime(fmt)
    ru_month = MONTHS_RU[dt.month - 1]
    result = result.replace(dt.strftime('%B'), ru_month)
    return result

@app.template_filter('status_icon')
def status_icon_filter(status):
    icons = {
        'pending': 'fa-clock',
        'processing': 'fa-cog',
        'shipped': 'fa-truck',
        'completed': 'fa-check-circle',
        'cancelled': 'fa-times-circle',
    }
    return icons.get(status, 'fa-circle')

@app.template_filter('status_color')
def status_color_filter(status):
    colors = {
        'pending': 'warning',
        'processing': 'info',
        'shipped': 'primary',
        'completed': 'success',
        'cancelled': 'danger',
    }
    return colors.get(status, 'secondary')

@app.template_filter('status_ru')
def status_ru_filter(status):
    names = {
        'pending': 'Ожидание',
        'processing': 'Обработка',
        'shipped': 'В пути',
        'completed': 'Завершён',
        'cancelled': 'Отменён',
    }
    return names.get(status, status)

@app.template_filter('product_img')
def product_img_filter(image):
    if not image or image == 'default_product.png':
        return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><rect fill="%23eeeeee" width="200" height="200"/><text x="100" y="105" text-anchor="middle" fill="%23999" font-family="Inter,Arial,sans-serif" font-size="14" font-weight="600">Нет фото</text></svg>'
    if image.startswith(('http://', 'https://')):
        return image
    if image.startswith('db_'):
        return url_for('db_image', type='product', filename=image)
    return url_for('static', filename='uploads/' + image)

@app.template_filter('avatar_img')
def avatar_img_filter(avatar):
    if avatar and avatar.startswith(('http://', 'https://')):
        return avatar
    if avatar and avatar.startswith('db_'):
        return url_for('db_image', type='avatar', filename=avatar)
    return url_for('static', filename='uploads/' + (avatar or 'default_avatar.png'))

@app.context_processor
def inject_categories():
    categories = Category.query.all()
    cart_count = 0
    if current_user.is_authenticated:
        cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
    return dict(categories=categories, cart_count=cart_count)

@app.route('/')
def index():
    products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    categories = Category.query.all()
    cat_products = {}
    for cat in categories:
        cat_products[cat.id] = Product.query.filter_by(category_id=cat.id, is_active=True).count()
    stats = {
        'users': User.query.count(),
        'products': Product.query.filter_by(is_active=True).count(),
        'orders': Order.query.count(),
    }
    wishlist_ids = []
    if current_user.is_authenticated:
        wishlist_ids = [item.product_id for item in WishlistItem.query.filter_by(user_id=current_user.id).all()]
    return render_template('index.html', products=products, categories=categories, cat_products=cat_products, stats=stats, wishlist_ids=wishlist_ids)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'buyer')

        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято!', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Эта почта уже зарегистрирована!', 'danger')
            return render_template('register.html')

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash(f'Добро пожаловать в ShopFussion, {username}! Войдите в аккаунт.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'С возвращением, {user.username}!', 'success')

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'seller':
                return redirect(url_for('seller_dashboard'))
            else:
                return redirect(url_for('buyer_dashboard'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.email = request.form.get('email')
        avatar = request.files.get('avatar')
        avatar_url = request.form.get('avatar_url', '').strip()
        if avatar and allowed_file(avatar.filename):
            filename = secure_filename(f"avatar_{current_user.id}_{datetime.utcnow().timestamp()}_{avatar.filename}")
            current_user.avatar_data = avatar.read()
            current_user.avatar = f"db_{filename}"
        elif avatar_url:
            current_user.avatar = avatar_url
            current_user.avatar_data = None
        db.session.commit()
        flash('Профиль обновлён!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html')

@app.route('/profile/delete-avatar', methods=['POST'])
@login_required
def delete_avatar():
    current_user.avatar = 'default_avatar.png'
    current_user.avatar_data = None
    db.session.commit()
    flash('Аватар удалён.', 'info')
    return redirect(url_for('profile'))

@app.route('/products')
def products():
    category_id = request.args.get('category')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = 8

    query = Product.query.filter_by(is_active=True)

    if category_id:
        query = query.filter_by(category_id=int(category_id))

    if search:
        query = query.filter(Product.name.contains(search) | Product.description.contains(search))

    products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.all()
    wishlist_ids = []
    if current_user.is_authenticated:
        wishlist_ids = [item.product_id for item in WishlistItem.query.filter_by(user_id=current_user.id).all()]
    return render_template('products.html', products=products, categories=categories, wishlist_ids=wishlist_ids)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    related = Product.query.filter_by(category_id=product.category_id, is_active=True).filter(Product.id != product_id).limit(4).all()
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(product_id=product_id).scalar() or 0
    is_wishlisted = False
    if current_user.is_authenticated:
        is_wishlisted = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first() is not None
    return render_template('product_detail.html', product=product, related=related, reviews=reviews, avg_rating=round(avg_rating, 1), is_wishlisted=is_wishlisted)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)
    if not product or not product.is_active:
        flash('Товар не найден!', 'danger')
        return redirect(url_for('products'))

    existing = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        existing.quantity += 1
    else:
        item = CartItem(user_id=current_user.id, product_id=product_id)
        db.session.add(item)

    db.session.commit()
    flash(f'"{product.name}" добавлен в корзину!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in items if item.product)
    return render_template('cart.html', items=items, total=total)

@app.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    item = db.session.get(CartItem, item_id)
    if item and item.user_id == current_user.id:
        quantity = int(request.form.get('quantity', 1))
        if quantity > 0:
            item.quantity = min(quantity, item.product.stock)
        else:
            db.session.delete(item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    item = db.session.get(CartItem, item_id)
    if item and item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Ваша корзина пуста!', 'warning')
        return redirect(url_for('cart'))

    total = sum(item.product.price * item.quantity for item in items if item.product)

    if request.method == 'POST':
        address = request.form.get('address')
        if not address:
            flash('Укажите адрес доставки.', 'danger')
            return render_template('checkout.html', items=items, total=total)

        order = Order(buyer_id=current_user.id, total=total, address=address)
        db.session.add(order)
        db.session.flush()

        tracking = OrderTracking(order_id=order.id, status='pending',
                                 location='Склад продавца',
                                 description='Заказ принят и передан в обработку')
        db.session.add(tracking)

        for item in items:
            if item.product.stock < item.quantity:
                flash(f'Недостаточно товара "{item.product.name}" на складе!', 'danger')
                return redirect(url_for('cart'))

            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)
            item.product.stock -= item.quantity
            db.session.delete(item)

        db.session.commit()
        flash('Заказ оформлен успешно!', 'success')
        return redirect(url_for('buyer_orders'))

    return render_template('checkout.html', items=items, total=total)

@app.route('/order/tracking/<int:order_id>')
@login_required
def order_tracking(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    if order.buyer_id != current_user.id and current_user.role not in ['seller', 'admin']:
        abort(403)
    return render_template('order_tracking.html', order=order)

@app.route('/order/tracking/<int:order_id>/add', methods=['POST'])
@login_required
def add_tracking(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    if current_user.role not in ['admin']:
        if current_user.role == 'seller':
            product_ids = [p.id for p in Product.query.filter_by(seller_id=current_user.id).all()]
            order_product_ids = [oi.product_id for oi in OrderItem.query.filter_by(order_id=order_id).all()]
            if not any(pid in product_ids for pid in order_product_ids):
                abort(403)
        else:
            abort(403)

    status = request.form.get('status', order.status)
    location = request.form.get('location', '')
    description = request.form.get('description', '')

    order.status = status
    tracking = OrderTracking(order_id=order.id, status=status,
                             location=location, description=description)
    db.session.add(tracking)
    db.session.commit()
    flash('Трек-событие добавлено!', 'success')
    return redirect(request.referrer or url_for('admin_orders'))

@app.route('/buyer/dashboard')
@login_required
def buyer_dashboard():
    recent_orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    return render_template('buyer/dashboard.html', recent_orders=recent_orders, cart_items=cart_items)

@app.route('/buyer/orders')
@login_required
def buyer_orders():
    orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('buyer/orders.html', orders=orders)

@app.route('/seller/dashboard')
@login_required
@seller_required
def seller_dashboard():
    products = Product.query.filter_by(seller_id=current_user.id).all()
    total_products = len(products)
    total_stock = sum(p.stock for p in products)
    total_revenue = sum(p.price * sum(oi.quantity for oi in OrderItem.query.filter_by(product_id=p.id).all()) for p in products)
    orders_count = sum(1 for p in products for oi in OrderItem.query.filter_by(product_id=p.id).all())
    return render_template('seller/dashboard.html', products=products, total_products=total_products, total_stock=total_stock, total_revenue=total_revenue, orders_count=orders_count)

@app.route('/seller/products')
@login_required
@seller_required
def seller_products():
    if current_user.role == 'admin':
        products = Product.query.order_by(Product.created_at.desc()).all()
    else:
        products = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template('seller/products.html', products=products)

def handle_product_form(product=None):
    name = request.form.get('name')
    description = request.form.get('description')
    price = float(request.form.get('price', 0))
    stock = int(request.form.get('stock', 0))
    category_id = int(request.form.get('category_id', 0))
    image = request.files.get('image')
    image_url = request.form.get('image_url', '').strip()
    delete_image = request.form.get('delete_image') == '1'
    brand = request.form.get('brand', '').strip()
    color = request.form.get('color', '').strip()
    size = request.form.get('size', '').strip()
    weight = request.form.get('weight', '').strip()
    material = request.form.get('material', '').strip()

    if product is not None and delete_image:
        product.image = 'default_product.png'
        product.image_data = None

    if image and allowed_file(image.filename):
        filename = secure_filename(f"{datetime.utcnow().timestamp()}_{image.filename}")
        product.image_data = image.read()
        current_img = f"db_{filename}"
    elif image_url:
        current_img = image_url
        if product:
            product.image_data = None
    elif product is None:
        current_img = 'default_product.png'
    else:
        current_img = product.image

    extra_chars = {}
    for key in request.form:
        if key.startswith('char_name_'):
            idx = key.replace('char_name_', '')
            char_val = request.form.get(f'char_value_{idx}', '').strip()
            char_name = request.form.get(key, '').strip()
            if char_name and char_val:
                extra_chars[char_name] = char_val

    chars = {}
    if brand: chars['Бренд'] = brand
    if color: chars['Цвет'] = color
    if size: chars['Размер'] = size
    if weight: chars['Вес'] = weight
    if material: chars['Материал'] = material
    chars.update(extra_chars)

    if product is None:
        product = Product(
            name=name, description=description, price=price,
            stock=stock, image=current_img, seller_id=current_user.id,
            category_id=category_id
        )
        db.session.add(product)
    else:
        product.name = name
        product.description = description
        product.price = price
        product.stock = stock
        product.category_id = category_id
        product.is_active = 'is_active' in request.form
        if image and allowed_file(image.filename):
            product.image = current_img
        elif image_url:
            product.image = current_img
            product.image_data = None
        ProductCharacteristic.query.filter_by(product_id=product.id).delete()

    db.session.flush()

    for char_name, char_value in chars.items():
        db.session.add(ProductCharacteristic(product_id=product.id, name=char_name, value=char_value))

    db.session.commit()
    return product

@app.route('/seller/products/add', methods=['GET', 'POST'])
@login_required
@seller_required
def add_product():
    if request.method == 'POST':
        try:
            handle_product_form()
            flash('Товар успешно добавлен!', 'success')
            return redirect(url_for('seller_products'))
        except Exception as e:
            flash(f'Ошибка: {str(e)}', 'danger')

    categories = Category.query.all()
    return render_template('seller/add_product.html', categories=categories)

@app.route('/seller/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@seller_required
def edit_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    if current_user.role != 'admin' and product.seller_id != current_user.id:
        abort(404)

    if request.method == 'POST':
        try:
            handle_product_form(product=product)
            flash('Товар обновлён!', 'success')
            return redirect(url_for('seller_products'))
        except Exception as e:
            flash(f'Ошибка: {str(e)}', 'danger')

    categories = Category.query.all()
    return render_template('seller/edit_product.html', product=product, categories=categories)

@app.route('/seller/products/delete/<int:product_id>', methods=['POST'])
@login_required
@seller_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product and (product.seller_id == current_user.id or current_user.role == 'admin'):
        product.is_active = False
        db.session.commit()
        flash('Товар деактивирован.', 'info')
    return redirect(url_for('seller_products'))

@app.route('/seller/orders')
@login_required
@seller_required
def seller_orders():
    product_ids = [p.id for p in Product.query.filter_by(seller_id=current_user.id).all()]
    order_items = OrderItem.query.filter(OrderItem.product_id.in_(product_ids)).all() if product_ids else []
    order_ids = list(set(oi.order_id for oi in order_items))
    orders = Order.query.filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc()).all() if order_ids else []
    return render_template('seller/orders.html', orders=orders, order_items=order_items)

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total)).scalar() or 0
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', total_users=total_users, total_products=total_products, total_orders=total_orders, total_revenue=total_revenue, recent_users=recent_users, recent_orders=recent_orders)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user and user.id != current_user.id:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь удалён.', 'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def admin_categories():
    if current_user.role not in ['admin', 'seller']:
        abort(403)
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            cat = Category(name=name)
            db.session.add(cat)
            db.session.commit()
            flash('Категория добавлена!', 'success')
        return redirect(url_for('admin_categories'))

    categories = Category.query.all()
    cat_products = {}
    for cat in categories:
        cat_products[cat.id] = Product.query.filter_by(category_id=cat.id).count()
    return render_template('admin/categories.html', categories=categories, cat_products=cat_products)

@app.route('/admin/categories/delete/<int:cat_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if cat:
        db.session.delete(cat)
        db.session.commit()
        flash('Категория удалена.', 'info')
    return redirect(url_for('admin_categories'))

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/update/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if order:
        new_status = request.form.get('status', 'pending')
        if order.status != new_status:
            order.status = new_status
            tracking = OrderTracking(
                order_id=order.id,
                status=new_status,
                location=request.form.get('location', ''),
                description=request.form.get('description', '')
            )
            db.session.add(tracking)
            flash('Статус заказа обновлён! Событие добавлено в историю.', 'success')
        else:
            flash('Статус не изменился.', 'info')
        db.session.commit()
    return redirect(url_for('admin_orders'))

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('seller/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_product():
    if request.method == 'POST':
        try:
            handle_product_form()
            flash('Товар успешно добавлен!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash(f'Ошибка: {str(e)}', 'danger')
    categories = Category.query.all()
    return render_template('seller/add_product.html', categories=categories)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    if request.method == 'POST':
        try:
            handle_product_form(product=product)
            flash('Товар обновлён!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash(f'Ошибка: {str(e)}', 'danger')
    categories = Category.query.all()
    return render_template('seller/edit_product.html', product=product, categories=categories)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product:
        product.is_active = False
        db.session.commit()
        flash('Товар деактивирован.', 'info')
    return redirect(url_for('admin_products'))

@app.route('/product/<int:product_id>/delete-image', methods=['POST'])
@login_required
def delete_product_image(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    if current_user.role != 'admin' and product.seller_id != current_user.id:
        abort(403)
    product.image_data = None
    product.image = 'default_product.png'
    db.session.commit()
    flash('Изображение удалено.', 'info')
    return redirect(url_for('edit_product', product_id=product_id) if current_user.role != 'admin' else url_for('admin_edit_product', product_id=product_id))

@app.route('/wishlist')
@login_required
def wishlist():
    items = WishlistItem.query.filter_by(user_id=current_user.id).order_by(WishlistItem.created_at.desc()).all()
    return render_template('wishlist.html', items=items)

@app.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def wishlist_add(product_id):
    existing = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not existing:
        item = WishlistItem(user_id=current_user.id, product_id=product_id)
        db.session.add(item)
        db.session.commit()
    return redirect(request.referrer or url_for('products'))

@app.route('/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def wishlist_remove(product_id):
    item = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(request.referrer or url_for('wishlist'))

@app.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    if current_user.role != 'buyer':
        flash('Только покупатели могут оставлять отзывы.', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    has_ordered = Order.query.join(OrderItem).filter(Order.buyer_id == current_user.id, OrderItem.product_id == product_id, Order.status == 'delivered').first()
    if not has_ordered:
        flash('Вы можете оставить отзыв только на оплаченные и доставленные товары.', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    rating = request.form.get('rating', 5, type=int)
    text = request.form.get('text', '').strip()
    if rating < 1 or rating > 5:
        rating = 5
    existing = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        existing.rating = rating
        existing.text = text
        existing.created_at = datetime.utcnow()
        flash('Отзыв обновлён.', 'info')
    else:
        review = Review(user_id=current_user.id, product_id=product_id, rating=rating, text=text)
        db.session.add(review)
        flash('Отзыв добавлен. Спасибо!', 'success')
    db.session.commit()
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/search/suggestions')
def search_suggestions():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    products = Product.query.filter(Product.is_active == True, Product.name.contains(q)).limit(10).all()
    def img_url(p):
        if p.image and p.image.startswith(('http://', 'https://')):
            return p.image
        if p.image and p.image.startswith('db_'):
            return url_for('db_image', type='product', filename=p.image)
        return url_for('static', filename='uploads/' + (p.image or 'default_product.png'))
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price, 'image': img_url(p)} for p in products])

from flask import Response as FlaskResponse
@app.route('/db-image/<type>/<filename>')
def db_image(type, filename):
    data = None
    if type == 'product':
        product = Product.query.filter_by(image=filename).first()
        if product and product.image_data:
            data = product.image_data
    elif type == 'avatar':
        user = User.query.filter_by(avatar=filename).first()
        if user and user.avatar_data:
            data = user.avatar_data
    if data is None:
        return '', 404
    return FlaskResponse(data, mimetype='image/png')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@shopfussion.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

            if not Category.query.first():
                categories = ['Электроника', 'Одежда', 'Дом и сад', 'Книги', 'Спорт', 'Красота и здоровье', 'Игрушки', 'Еда и напитки']
                for name in categories:
                    db.session.add(Category(name=name))

            if not User.query.filter_by(username='seller').first():
                seller = User(username='seller', email='seller@shopfussion.com', role='seller')
                seller.set_password('seller123')
                db.session.add(seller)

            if not User.query.filter_by(username='buyer').first():
                buyer = User(username='buyer', email='buyer@shopfussion.com', role='buyer')
                buyer.set_password('buyer123')
                db.session.add(buyer)

            db.session.commit()
            print('База данных инициализирована с тестовыми данными.')
    app.run(debug=True, host='0.0.0.0', port=5000)
