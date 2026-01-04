import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pytz 

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uae-secret-key-123'
ADMIN_SECRET_CODE = 'A999A' 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cars.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# جدول السجلات
class CarLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    military_id = db.Column(db.String(50), nullable=False)
    car_type = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# جدول المناطق
class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

@app.template_filter('format_datetime_uae')
def format_datetime_uae(value):
    if value is None: return ""
    utc, uae = pytz.utc, pytz.timezone('Asia/Dubai')
    if value.tzinfo is None: value = utc.localize(value)
    return value.astimezone(uae).strftime('%Y-%m-%d %I:%M %p')

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    regions = Region.query.all()
    return render_template('home.html', regions=regions)

@app.route('/region_qr/<string:region_name>')
def region_qr(region_name):
    # هذا يقرأ رابط الموقع أوتوماتيك سواء كان أونلاين أو محلي
    base_url = request.host_url.rstrip('/')
    qr_link = f"{base_url}/register?region={region_name}"
    return render_template('qr_view.html', region=region_name, qr_link=qr_link)

@app.route('/register')
def index():
    region = request.args.get('region', 'الشارقة')
    return render_template('index.html', region=region)

@app.route('/submit', methods=['POST'])
def submit():
    username = request.form['username']
    military_id = request.form['military_id']
    car_type = request.form['car_type']
    region = request.form['region']
    new_log = CarLog(username=username, military_id=military_id, car_type=car_type, region=region)
    db.session.add(new_log)
    db.session.commit()
    return "تم التسجيل بنجاح!"

@app.route('/add_region', methods=['POST'])
def add_region():
    name = request.form.get('region_name')
    if name:
        try:
            new_reg = Region(name=name)
            db.session.add(new_reg)
            db.session.commit()
        except: db.session.rollback()
    return redirect(url_for('home'))

@app.route('/delete_region/<int:id>')
def delete_region(id):
    reg = Region.query.get(id)
    if reg:
        db.session.delete(reg)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    code = request.args.get('code')
    if code != ADMIN_SECRET_CODE: return redirect(url_for('home'))
    logs = CarLog.query.order_by(CarLog.timestamp.desc()).all()
    return render_template('admin.html', logs=logs)

if __name__ == '__main__':
    # مهم للرفع أونلاين
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)