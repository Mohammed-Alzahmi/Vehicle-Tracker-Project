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

# جدول المناطق الجديد
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
    # إضافة مناطق افتراضية إذا كان الجدول فاضي
    if not Region.query.first():
        default_regions = [Region(name="خورفكان"), Region(name="الذيد"), Region(name="كلباء")]
        db.session.bulk_save_objects(default_regions)
        db.session.commit()

@app.route('/')
def home():
    regions = Region.query.all()
    return render_template('home.html', regions=regions)

@app.route('/add_region', methods=['POST'])
def add_region():
    new_name = request.form.get('region_name')
    if new_name:
        try:
            new_reg = Region(name=new_name)
            db.session.add(new_reg)
            db.session.commit()
            flash('تمت إضافة المنطقة بنجاح', 'success')
        except:
            flash('المنطقة موجودة مسبقاً', 'danger')
    return redirect(url_for('home'))

@app.route('/delete_region/<int:id>')
def delete_region(id):
    reg = Region.query.get(id)
    if reg:
        db.session.delete(reg)
        db.session.commit()
        flash('تم حذف المنطقة', 'success')
    return redirect(url_for('home'))

@app.route('/register')
def index():
    car_name = request.args.get('car', 'سيارة غير محددة')
    region = request.args.get('region', 'غير محدد')
    return render_template('index.html', car_name=car_name, region=region)

@app.route('/submit', methods=['POST'])
def submit():
    username = request.form['username']
    military_id = request.form['military_id']
    car_type = request.form['car_type']
    region = request.form['region']
    new_log = CarLog(username=username, military_id=military_id, car_type=car_type, region=region)
    db.session.add(new_log)
    db.session.commit()
    flash('تم تسجيل البيانات بنجاح!', 'success')
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    code = request.args.get('code')
    if code != ADMIN_SECRET_CODE: return redirect(url_for('home'))
    region_filter = request.args.get('region')
    if region_filter:
        logs = CarLog.query.filter_by(region=region_filter).order_by(CarLog.timestamp.desc()).all()
    else:
        logs = CarLog.query.order_by(CarLog.timestamp.desc()).all()
    return render_template('admin.html', logs=logs, current_region=region_filter)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)