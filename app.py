import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pytz 

# إعدادات المسارات
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uae-secret-key-123')
ADMIN_SECRET_CODE = os.environ.get('ADMIN_CODE', 'A999A') 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cars.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# جدول قاعدة البيانات
class CarLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    military_id = db.Column(db.String(50), nullable=False)
    car_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# فلتر تعديل الوقت للإماراتي
@app.template_filter('format_datetime_uae')
def format_datetime_uae(value):
    if value is None: return ""
    utc, uae = pytz.utc, pytz.timezone('Asia/Dubai')
    if value.tzinfo is None: value = utc.localize(value)
    return value.astimezone(uae).strftime('%Y-%m-%d %I:%M %p')

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    car_name = request.args.get('car', 'سيارة غير محددة') 
    # هني تأكدي إن الملف في مجلد templates اسمه index.html
    return render_template('index.html', car_name=car_name)

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        username = request.form['username']
        military_id = request.form['military_id']
        car_type = request.form['car_type']
        new_log = CarLog(username=username, military_id=military_id, car_type=car_type)
        try:
            db.session.add(new_log)
            db.session.commit()
            flash('تم تسجيل بياناتك بنجاح!', 'success')
            return redirect(url_for('index', car=car_type)) 
        except:
            flash('خطأ في التسجيل!', 'danger')
            return redirect(url_for('index', car=car_type))

@app.route('/admin')
def admin():
    code = request.args.get('code') 
    if code != ADMIN_SECRET_CODE:
        flash('🚫 وصول غير مصرح به!', 'danger')
        return redirect(url_for('index')) 
    all_logs = CarLog.query.order_by(CarLog.timestamp.desc()).all()
    return render_template('admin.html', logs=all_logs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)