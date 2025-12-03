import qrcode
import socket

# --- هني تحطين المعلومات اللي تبينها ---

# 1. قائمة السيارات (حطي أسامي سياراتكم)
# (استخدمي أسماء بسيطة انجليزية عشان اللينك)
CARS_LIST = [
    "Hilux_01_AbuDhabi", 
    "Patrol_05_Dubai", 
    "Ranger_02_Sharjah",
    "LandCruiser_10_Admin"
]

# 2. الـ IP Address مال لابتوبج
# هالكود بيحاول يجيب الـ IP مالج أوتوماتيك (لازم تكونين شابة عالواي فاي)
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # !!! اذا الكود ما عرف، حطي الـ IP مالج هني يدوي !!!
        return "192.168.1.10" # <--- بدلي هذا 

YOUR_IP_ADDRESS = get_ip_address()
PORT = "5000" # هذا البورت من ملف app.py

# --- الكود بيشتغل بروحه ---
print(f"بيتم إنشاء QR Codes... اللينك بيستخدم هذا الـ IP: {YOUR_IP_ADDRESS}")

# !!! بدلي هذا الـ IP بالـ IP الصحيح اللي طلع لج الحين !!!
# نستخدم لينك وهمي لين ما نعرف اللينك الحقيقي من منصة النشر
BASE_URL = "https://YOUR-APP-NAME-GOES-HERE.onrender.com/"# !!! بدلي هذا الـ IP بالـ IP الصحيح اللي طلع لج الحين !!!


for car in CARS_LIST:
    qr_link = f"{BASE_URL}?car={car}"
    
    img = qrcode.make(qr_link)
    file_name = f"qr_code_للسيارة_{car}.png"
    img.save(file_name)
    print(f"✅ تم حفظ: {file_name} (اللينك: {qr_link})")

print("\nخلصنا! اطبعي صور الـ PNG وحطيها فالسيارات.")