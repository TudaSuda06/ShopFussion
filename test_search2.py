import app
with app.app.app_context():
    for p in app.Product.query.limit(5).all():
        name_bytes = p.name.encode('utf-8')
        print(f'ID={p.id} name_bytes={name_bytes}')
        print(f'  contains науш: {p.name.__contains__("науш")}')
