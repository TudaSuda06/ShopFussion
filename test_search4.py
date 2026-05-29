import app
from sqlalchemy import text
from sqlalchemy import func

with app.app.app_context():
    q = 'науш'

    # Try LOWER in SQL
    sql = "SELECT id, name FROM product WHERE LOWER(name) LIKE '%{}%'".format(q)
    rows = app.db.session.execute(text(sql)).fetchall()
    print('SQL LOWER LIKE:', len(rows))
    for r in rows:
        print(' ', r[0], r[1])

    # Try using func.lower in SQLAlchemy
    results = app.Product.query.filter(func.lower(app.Product.name).contains(q)).all()
    print('func.lower contains:', len(results))
    for r in results:
        print(' ', r.id, r.name)

    # Try ilike again on the lowercased query
    results2 = app.Product.query.filter(app.Product.name.ilike('%' + q + '%')).all()
    print('ilike:', len(results2))
