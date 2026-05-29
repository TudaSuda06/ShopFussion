import app
from sqlalchemy import text

with app.app.app_context():
    # Check SQLite version and LOWER behavior with Russian
    sql = "SELECT LOWER('Наушники'), UPPER('наушники')"
    rows = app.db.session.execute(text(sql)).fetchall()
    print('LOWER test:', rows[0][0], '/', rows[0][1])

    # Direct match test - find all products with name containing H (Н)
    sql2 = "SELECT id, name FROM product WHERE name LIKE '%Н%'"
    rows2 = app.db.session.execute(text(sql2)).fetchall()
    print('Russian letter Н match:', len(rows2))
