import os
import datetime
import io
import re
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
import pytz 
from fpdf import FPDF

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uae-secret-key-123')
ADMIN_SECRET_CODE = os.environ.get('ADMIN_CODE', 'A999A') 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cars.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CarLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    military_id = db.Column(db.String(50), nullable=False)
    car_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

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
    return render_template('index.html', car_name=car_name)

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        username, military_id, car_type = request.form['username'], request.form['military_id'], request.form['car_type']
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

@app.route('/delete_logs', methods=['POST'])
def delete_logs():
    code = request.args.get('code')
    if code != ADMIN_SECRET_CODE:
        return "Unauthorized", 403
    log_ids = request.form.getlist('log_ids')
    if log_ids:
        CarLog.query.filter(CarLog.id.in_(log_ids)).delete(synchronize_session=False)
        db.session.commit()
        flash(f'تم حذف {len(log_ids)} سجل بنجاح!', 'success')
    return redirect(url_for('admin', code=code))

# دالة تنظيف البيانات من أي حرف غير إنجليزي
def clean_for_pdf(text):
    # يسمح فقط بالأرقام، الحروف الإنجليزية، والرموز الأساسية
    return re.sub(r'[^\x00-\x7f]', r' ', str(text))

@app.route('/download_pdf')
def download_pdf():
    code = request.args.get('code')
    if code != ADMIN_SECRET_CODE:
        return "Unauthorized", 403
    try:
        logs = CarLog.query.order_by(CarLog.timestamp.desc()).all()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Vehicle Log Report", ln=1, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(15, 10, "#", 1)
        pdf.cell(55, 10, "Name (EN Only)", 1)
        pdf.cell(40, 10, "Military ID", 1)
        pdf.cell(40, 10, "Car Type", 1)
        pdf.cell(40, 10, "Time", 1)
        pdf.ln()

        pdf.set_font("Arial", size=10)
        for log in logs:
            # تنظيف البيانات قبل كتابتها
            safe_name = clean_for_pdf(log.username)
            safe_car = clean_for_pdf(log.car_type)
            safe_id = clean_for_pdf(log.military_id)
            
            pdf.cell(15, 10, str(log.id), 1)
            pdf.cell(55, 10, safe_name[:25], 1)
            pdf.cell(40, 10, safe_id, 1)
            pdf.cell(40, 10, safe_car, 1)
            pdf.cell(40, 10, log.timestamp.strftime('%Y-%m-%d %H:%M'), 1)
            pdf.ln()

        response = make_response(pdf.output(dest='S'))
        # التأكد إن الـ output صار bytes
        if isinstance(response.data, str):
            response.data = response.data.encode('latin-1', 'replace')
            
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'attachment', filename='vehicle_logs.pdf')
        return response
    except Exception as e:
        return f"PDF Final Shield Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)