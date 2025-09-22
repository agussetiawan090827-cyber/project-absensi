from flask import Flask, render_template, request, jsonify
import sqlite3, math, os, uuid
import face_recognition
import cv2

app = Flask(__name__)


SCHOOL_LAT = -6.260960
SCHOOL_LNG = 106.959603
RADIUS = 15  

DB_NAME = "database.db"
FACES_DIR = "faces"
UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def hitung_jarak(lat1, lng1, lat2, lng2):
    # Haversine formula
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_all_siswa():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, nama, kelas, jurusan, foto_path FROM siswa")
    rows = cur.fetchall()
    conn.close()
    return rows

def cari_siswa_dengan_wajah(file_path):
    try:
        
        img_unknown = face_recognition.load_image_file(file_path)
        unknown_encodings = face_recognition.face_encodings(img_unknown)

        if not unknown_encodings:
            return None  

        unknown_encoding = unknown_encodings[0]

       
        for sid, nama, kelas, jurusan, foto_path in get_all_siswa():
            if not os.path.exists(foto_path):
                continue
            img_known = face_recognition.load_image_file(foto_path)
            known_encodings = face_recognition.face_encodings(img_known)
            if not known_encodings:
                continue

            result = face_recognition.compare_faces([known_encodings[0]], unknown_encoding, tolerance=0.5)
            if result[0]:  
                return {
                    "id": sid,
                    "nama": nama,
                    "kelas": kelas,
                    "jurusan": jurusan
                }

        return None
    except Exception as e:
        print("Error pencocokan wajah:", e)
        return None

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/set_cordinat")
def set_cordinat():
    return render_template("set_cordinat.html")
@app.route("/absen_area")
def absen_area():
    return render_template("absen_area.html")

@app.route("/absen", methods=["POST"])
def absen():
    file = request.files["foto"]
    lat = float(request.form["lat"])
    lng = float(request.form["lng"])

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    jarak = hitung_jarak(lat, lng, SCHOOL_LAT, SCHOOL_LNG)
    if jarak > RADIUS:
        os.remove(filepath)
        return jsonify({"success": False, "message": f"Diluar area sekolah! Jarak {jarak:.2f} m"})

    siswa = cari_siswa_dengan_wajah(filepath)

    if os.path.exists(filepath):
        os.remove(filepath)

    if not siswa:
        return jsonify({"success": False, "message": "Wajah tidak dikenali!"})

    return jsonify({
        "success": True,
        "nama": siswa["nama"],
        "kelas": siswa["kelas"],
        "jurusan": siswa["jurusan"],
        "area": "Dalam Area"
    })

if __name__ == "__main__":
    app.run(debug=True)
