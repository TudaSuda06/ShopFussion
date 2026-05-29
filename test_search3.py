import app
from sqlalchemy import text

with app.app.app_context():
    q = 'науш'
    sql = "SELECT id, name FROM product WHERE name LIKE '%{}%'".format(q)
    rows = app.db.session.execute(text(sql)).fetchall()
    print('SQL LIKE:', len(rows))
    for r in rows:
        print(' ', r[0], r[1])

    all_p = app.Product.query.all()
    filtered = [p for p in all_p if q in p.name.lower()]
    print('Python filter:', len(filtered))
    for p in filtered:
        print(' ', p.id, p.name)
