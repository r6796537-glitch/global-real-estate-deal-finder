from flask import Flask, render_template, request, redirect, url_for, Response
import sqlite3, os, csv, io
from datetime import datetime

app = Flask(__name__)
DB = os.environ.get('DATABASE_PATH', 'deals.db')

COUNTRIES = ['India','United States','United Kingdom','Canada','United Arab Emirates','Australia','Other']
CURRENCIES = ['INR','USD','GBP','CAD','AED','AUD','EUR','Other']

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, country TEXT NOT NULL, city TEXT NOT NULL,
            address TEXT DEFAULT '', property_type TEXT DEFAULT 'Residential',
            price REAL DEFAULT 0, currency TEXT DEFAULT 'USD', repair_cost REAL DEFAULT 0,
            target_price REAL DEFAULT 0, source_url TEXT DEFAULT '', seller_name TEXT DEFAULT '',
            seller_contact TEXT DEFAULT '', buyer_budget REAL DEFAULT 0, notes TEXT DEFAULT '',
            created_at TEXT NOT NULL)''')
init_db()

@app.route('/')
def index():
    with db() as con:
        deals = con.execute('SELECT * FROM deals ORDER BY id DESC').fetchall()
    totals = {'count': len(deals), 'spread': sum((d['target_price'] or 0) - (d['price'] or 0) - (d['repair_cost'] or 0) for d in deals)}
    return render_template('index.html', deals=deals, totals=totals, countries=COUNTRIES, currencies=CURRENCIES)

@app.post('/add')
def add():
    f = request.form
    def num(key):
        try: return max(0, float(f.get(key, 0) or 0))
        except ValueError: return 0
    with db() as con:
        con.execute('''INSERT INTO deals(country,city,address,property_type,price,currency,repair_cost,target_price,source_url,seller_name,seller_contact,buyer_budget,notes,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (f.get('country','India'), f.get('city','').strip(), f.get('address','').strip(), f.get('property_type','Residential'), num('price'), f.get('currency','USD'), num('repair_cost'), num('target_price'), f.get('source_url','').strip(), f.get('seller_name','').strip(), f.get('seller_contact','').strip(), num('buyer_budget'), f.get('notes','').strip(), datetime.utcnow().isoformat(timespec='seconds')+'Z'))
    return redirect(url_for('index'))

@app.post('/delete/<int:deal_id>')
def delete(deal_id):
    with db() as con: con.execute('DELETE FROM deals WHERE id=?', (deal_id,))
    return redirect(url_for('index'))

@app.get('/export.csv')
def export_csv():
    with db() as con: rows = con.execute('SELECT * FROM deals ORDER BY id DESC').fetchall()
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(rows[0].keys() if rows else ['id','country','city','address','property_type','price','currency','repair_cost','target_price','source_url','seller_name','seller_contact','buyer_budget','notes','created_at'])
    for row in rows: writer.writerow(list(row))
    return Response('\ufeff'+output.getvalue(), mimetype='text/csv; charset=utf-8', headers={'Content-Disposition':'attachment; filename=global-property-leads.csv'})

@app.get('/health')
def health(): return {'status':'ok'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
