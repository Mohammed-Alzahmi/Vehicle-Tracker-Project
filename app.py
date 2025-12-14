import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
# مهم: لازم نثبت pytz عشان يضبط التوقيت الإماراتي
import pytz 

# --- إعدادات التطبيق والداتا بيس ---
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# !! غيري هذا المفتاح السري عقب !!
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# 🚀 1. إضافة رمز الأمان للأدمن
ADMIN_SECRET_CODE = os.environ.get('ADMIN_CODE', 'A999A') 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cars.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- تعريف شكل الداتا بيس (CarLog) ---
class CarLog(db.Model):
    id = db.Column(db.Integer, primary_key=True) # رقم تسلسلي
    username = db.Column(db.String(100), nullable=False) # اسم الشخص
    military_id = db.Column(db.String(50), nullable=False) # الرقم العسكري
    car_type = db.Column(db.String(50), nullable=False) # نوع السيارة
    # 🚀 2. تعديل التوقيت: نخليه فاضي عشان نحسب الوقت لحظة الإرسال
    timestamp = db.Column(db.DateTime) 

    def __repr__(self):
        return f"Log('{self.username}', '{self.car_type}', '{self.timestamp}')"

# --- دالة مساعدة لتحويل التوقيت من UTC إلى توقيت الإمارات (Asia/Dubai) ---
def format_datetime_uae(value):
    # نحدد التوقيت الأصلي (UTC)
    utc_timezone = pytz.utc
    if value.tzinfo is None:
        # لو ما كان مسجل كتوقيت بمعلومات التوقيت (tz-aware)، نسوي له localization
        utc_datetime = utc_timezone.localize(value)
    else:
        # لو كان فيه معلومات التوقيت، نحوله لـ UTC
        utc_datetime = value.astimezone(utc_timezone)

    # نحدد توقيت دبي (Asia/Dubai)
    dubai_timezone = pytz.timezone('Asia/Dubai')

    # نحول من UTC إلى توقيت دبي
    dubai_datetime = utc_datetime.astimezone(dubai_timezone)

    # نسوي فورمات عربي مناسب (سنة-شهر-يوم ساعة:دقيقة صباحاً/مساءً)
    return dubai_datetime.strftime('%Y-%m-%d %I:%M %p')

# نسجل الدالة عشان نقدر نستخدمها في ملفات HTML (Jinja2)
app.jinja_env.filters['format_datetime_uae'] = format_datetime_uae

# --- التأكد من إنشاء قاعدة البيانات والجداول عند تشغيل التطبيق (مهم لـ Gunicorn) ---
# هذا الجزء يضمن إنشاء ملف قاعدة البيانات والجداول عند تشغيل التطبيق لأول مرة.
with app.app_context():
    db.create_all()

# --- الصفحة الرئيسية (اللي بيفتحها الموظف) ---
@app.route('/')
def index():
    # هذا يزيل لينك الأدمن من الأسفل إذا كان الموقع محمي
    car_name = request.args.get('car', 'سيارة غير محددة') 
    return render_template('form.html', car_name=car_name)

# --- صفحة استلام البيانات (لما الموظف يضغط 'إرسال') ---
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        username = request.form['username']
        military_id = request.form['military_id']
        car_type = request.form['car_type']

        # 🚀 3. نحسب الوقت الفعلي لتوقيت دبي لحظة الضغط على زر الإرسال
        uae_tz = pytz.timezone('Asia/Dubai')
        current_uae_time = datetime.datetime.now(uae_tz) 

        # 🚀 4. نمرر الوقت الجديد لـ new_log
        new_log = CarLog(username=username, military_id=military_id, car_type=car_type, timestamp=current_uae_time)

        try:
            db.session.add(new_log)
            db.session.commit()
            flash('تم تسجيل بياناتك بنجاح! شكراً.', 'success')
            return redirect(url_for('index', car=car_type)) 
        except Exception as e:
            print(f"Database error: {e}")
            flash('صار خطأ في تسجيل البيانات! حاول مرة ثانية.', 'danger')
            return redirect(url_for('index', car=car_type))

# --- صفحة الأدمن (Dashboard) - هاي صفحتج أنتي ---
@app.route('/admin')
def admin():
    # 🚀 5. حماية الصفحة: نجيب الرمز السري من رابط الصفحة
    code = request.args.get('code') 

    # 🚀 6. إذا الرمز غلط، نرجع المستخدم لصفحة الإدخال ونمنعه
    if code != ADMIN_SECRET_CODE:
        flash('🚫 وصول غير مصرح به! هذا القسم محمي.', 'danger')
        return redirect(url_for('index')) 
        
    # 7. إذا الرمز صح، نعرض البيانات (هذا الكود كان موجود قبل)
    all_logs = CarLog.query.order_by(CarLog.timestamp.desc()).all()
    # في admin.html، لازم نستخدم الدالة format_datetime_uae
    return render_template('admin.html', logs=all_logs)


# --- كود تشغيل التطبيق (هذا فقط للـ Development/Testing) ---
# Gunicorn هو اللي بيشغل التطبيق، فبنخلي هذا الجزء بسيط عشان ما يتضارب معاه
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)