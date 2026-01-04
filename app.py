import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uae-police-secure-key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cars.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# قاعدة بيانات السجلات - أضفنا رقم السيارة
class CarLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    military_id = db.Column(db.String(50))
    car_type = db.Column(db.String(50))
    car_plate = db.Column(db.String(50)) # رقم السيارة
    region = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    allowed_cars = db.Column(db.String(500), default="نيسان,تويوتا,لكزس,مرسيدس")

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    regions = Region.query.all()
    return render_template('home.html', regions=regions)

@app.route('/view_logs/<string:region_name>')
def view_logs(region_name):
    logs = CarLog.query.filter_by(region=region_name).order_by(CarLog.timestamp.desc()).all()
    reg = Region.query.filter_by(name=region_name).first()
    base_url = request.host_url.rstrip('/')
    qr_link = f"{base_url}/register?region={region_name}"
    return render_template('region_details.html', region=region_name, logs=logs, qr_link=qr_link, reg_id=reg.id if reg else None)

@app.route('/delete_logs', methods=['POST'])
def delete_logs():
    log_ids = request.json.get('ids', [])
    if log_ids:
        CarLog.query.filter(CarLog.id.in_(log_ids)).delete(synchronize_session=False)
        db.session.commit()
    return jsonify({"status": "success"})

@app.route('/register')
def index():
    region_name = request.args.get('region', 'الشارقة')
    reg = Region.query.filter_by(name=region_name).first()
    car_list = reg.allowed_cars.split(',') if reg else ["نيسان", "تويوتا"]
    return render_template('index.html', region=region_name, car_list=car_list)

@app.route('/submit', methods=['POST'])
def submit():
    new_log = CarLog(
        username=request.form.get('username'),
        military_id=request.form.get('military_id'),
        car_type=request.form.get('car_type'),
        car_plate=request.form.get('car_plate'), # استقبال رقم السيارة
        region=request.form.get('region')
    )
    db.session.add(new_log)
    db.session.commit()
    return "<h1>✅ تم التسجيل بنجاح</h1>"

@app.route('/manage_cars/<int:id>', methods=['GET', 'POST'])
def manage_cars(id):
    reg = Region.query.get(id)
    if request.method == 'POST':
        reg.allowed_cars = request.form.get('cars')
        db.session.commit()
        return redirect(url_for('view_logs', region_name=reg.name))
    return render_template('manage_cars.html', reg=reg)

@app.route('/add_region', methods=['POST'])
def add_region():
    name = request.form.get('region_name')
    if name:
        db.session.add(Region(name=name))
        db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)