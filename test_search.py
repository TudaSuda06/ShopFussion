import app

q = 'наушники'
with app.app.app_context():
    results = app.Product.query.filter(app.Product.name.ilike('%' + q + '%')).all()
    print('ilike:', len(results))
    for r in results:
        print(' ', r.name)
    p = app.Product.query.get(3)
    print('Name:', repr(p.name))
    results2 = app.Product.query.filter(app.Product.name.contains(q)).all()
    print('contains:', len(results2))
