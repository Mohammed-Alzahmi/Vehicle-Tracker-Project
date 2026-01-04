import os
import datetime
from flask import Flask, render_template, request, redirect, url_for
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
    region = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    allowed_cars = db.Column(db.String(500), default="نيسان,تويوتا,لكزس,شفروليه,مرسيدس")

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    regions = Region.query.all()
    return render_template('home.html', regions=regions)

@app.route('/region_qr/<string:region_name>')
def region_qr(region_name):
    base_url = request.host_url.rstrip('/')
    qr_link = f"{base_url}/register?region={region_name}"
    return render_template('qr_view.html', region=region_name, qr_link=qr_link)

@app.route('/register')
def index():
    region_name = request.args.get('region', 'الشارقة')
    reg = Region.query.filter_by(name=region_name).first()
    car_list = reg.allowed_cars.split(',') if reg else ["نيسان", "تويوتا", "لكزس"]
    return render_template('index.html', region=region_name, car_list=car_list)

@app.route('/submit', methods=['POST'])
def submit():
    # استخدمنا .get لمنع ظهور Bad Request إذا نقصت خانة
    new_log = CarLog(
        username=request.form.get('username', 'غير معروف'),
        military_id=request.form.get('military_id', '0000'),
        car_type=request.form.get('car_type', 'غير محدد'),
        region=request.form.get('region', 'الشارقة')
    )
    db.session.add(new_log)
    db.session.commit()
    return "<h1>✅ تم التسجيل بنجاح</h1><p>شكراً لك، تم حفظ بيانات المركبة.</p>"

@app.route('/manage_cars/<int:id>', methods=['GET', 'POST'])
def manage_cars(id):
    reg = Region.query.get(id)
    if request.method == 'POST':
        reg.allowed_cars = request.form.get('cars')
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('manage_cars.html', reg=reg)

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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)