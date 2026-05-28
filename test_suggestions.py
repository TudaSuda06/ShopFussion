from app import app
import json
app.testing = True
with app.test_client() as c:
    r = c.get('/search/suggestions?q=тел')
    print(r.status_code)
    data = json.loads(r.data)
    for p in data:
        print(p['id'], p['name'], p['price'])
