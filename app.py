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

class CarLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    military_id = db.Column(db.String(50))
    car_type = db.Column(db.String(50))
    car_plate = db.Column(db.String(50)) 
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

@app.route('/register')
def index():
    region_name = request.args.get('region', 'الشارقة')
    reg = Region.query.filter_by(name=region_name).first()
    car_list = reg.allowed_cars.split(',') if reg and reg.allowed_cars else []
    return render_template('index.html', region=region_name, car_list=car_list)

@app.route('/submit', methods=['POST'])
def submit():
    new_log = CarLog(
        username=request.form.get('username'),
        military_id=request.form.get('military_id'),
        car_type=request.form.get('car_type'),
        car_plate=request.form.get('car_plate'),
        region=request.form.get('region')
    )
    db.session.add(new_log)
    db.session.commit()
    return "<h1>✅ تم التسجيل بنجاح</h1>"

@app.route('/manage_cars/<int:id>', methods=['GET', 'POST'])
def manage_cars(id):
    reg = Region.query.get(id)
    if request.method == 'POST':
        action = request.form.get('action')
        cars = reg.allowed_cars.split(',') if reg.allowed_cars else []
        
        if action == 'add':
            new_car = request.form.get('new_car').strip()
            if new_car and new_car not in cars:
                cars.append(new_car)
        elif action == 'delete':
            car_to_del = request.form.get('car_to_delete')
            if car_to_del in cars:
                cars.remove(car_to_del)
        
        reg.allowed_cars = ','.join(filter(None, cars))
        db.session.commit()
        return redirect(url_for('manage_cars', id=id))
        
    car_list = reg.allowed_cars.split(',') if reg.allowed_cars else []
    return render_template('manage_cars.html', reg=reg, car_list=car_list)

@app.route('/add_region', methods=['POST'])
def add_region():
    name = request.form.get('region_name')
    if name:
        if not Region.query.filter_by(name=name).first():
            db.session.add(Region(name=name))
            db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_region/<int:id>')
def delete_region(id):
    reg = Region.query.get(id)
    if reg:
        db.session.delete(reg)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_logs', methods=['POST'])
def delete_logs():
    data = request.get_json()
    log_ids = data.get('ids', [])
    if log_ids:
        CarLog.query.filter(CarLog.id.in_(log_ids)).delete(synchronize_session=False)
        db.session.commit()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)