from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    make_response,
    Request,
    jsonify,
    session,
    flash
)
import os
from datetime import datetime
import bcrypt
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'komunitas'

# JIKA ADA BERUBAH DI TEMPLATES AKAN TERRELOAD
app.config["TEMPLATES_AUTO_RELOAD"] = True
# app.config["UPLOAD_FOLDER"] = "./static/gallery"
app.config["UPLOAD_FOLDER"] = "./static/profile_pics"


# DATABASE
client = MongoClient("mongodb+srv://driyanti237:project@project.by6wjmk.mongodb.net/?retryWrites=true&w=majority&appName=Project")
db = client["Komunitas"]

# UNTUK CEK SUDAH LOGIN BELUM
def is_logged_in():
    return 'username' in session

# Fungsi untuk memeriksa admin bukan
def is_admin():
    if 'role' in session and session['role'] == 'admin':
        return True
    return False


# Home
@app.route('/' , methods=['GET', 'POST'])
def home():
    username = session.get('username')
    current_date = datetime.now().strftime('%Y-%m-%d')

    upcoming_event= db.event.find({'date': {'$gte': current_date}},{'_id':False})
    past_events= db.event.find({'date': {'$lt': current_date}},{'_id':False})
    gallery = db.gallery.find({}, {'_id': 0, 'filename': 1}).limit(10)
    user_info = db.users.find_one({'username': username}, {'_id': False})
    all_users = db.users.find({'role': {'$ne': 'admin'}}, {'_id': False})
    return render_template('landing.html', upcoming_event=upcoming_event,past_events=past_events, gallery=gallery, user_info=user_info, all_users=all_users)


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Cari pengguna berdasarkan username
        user = db.users.find_one({"username": username})

        if user:
            # Memeriksa apakah password cocok menggunakan bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                # Memeriksa peran pengguna
                role = user.get('role', 'user') 
                session['username'] = username
                session['role'] = role  
                if role == 'admin':
                    return redirect(url_for('admin')) 
                else:
                    return redirect(url_for('user')) 
            else:
                flash("Invalid username or password", "error")
                return redirect(url_for('login'))
        else:
            flash("User not found", "error")
            return redirect(url_for('login'))
    return render_template('login.html')

# Registration
@app.route("/registrasi", methods=["GET", "POST"])
def registrasi():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    # Membuat hash password menggunakan bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Validasi dan pembuatan akun pengguna baru
    doc = {
        "username": username,
        "password": hashed_password,
        "profile_name": username,
        "profile_pic": "",
        "profile_pic_real": "profile_pics/profile_placeholder.jpg",
        "profile_info": "",
        }
    db.users.insert_one(doc)

    return jsonify({"result": "success"})


# User dashboard
@app.route('/user', methods=['GET', 'POST'])
def user():
    if is_logged_in():
        username = session.get('username')
        current_date = datetime.now().strftime('%Y-%m-%d')

        upcoming_event= db.event.find({'date': {'$gte': current_date}},{'_id':False})
        past_events= db.event.find({'date': {'$lt': current_date}},{'_id':False})
        gallery = db.gallery.find({}, {'_id': 0, 'filename': 1}).limit(10)
        user_info = db.users.find_one({'username': username}, {'_id': False})
        all_users = db.users.find({'role': {'$ne': 'admin'}}, {'_id': False})
        return render_template('user.html', upcoming_event=upcoming_event,past_events=past_events, gallery=gallery, user_info=user_info, all_users=all_users)
    else:
        return redirect(url_for('login'))

    
# Admin dashboard
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if is_logged_in():
        if is_admin():
            username = session['username']
            event= db.event.find({}, {'_id': False})
            return render_template('admin-events.html', event=event)
        else:
            return "Unauthorized access. Only admins are allowed to access this page."
    else:
        return redirect(url_for('login'))


# Profile
@app.route('/profile<username>', methods=["GET"])
def profile(username):
    if is_logged_in():
        username = session['username']
        user_info = db.users.find_one({'username': username}, {'_id': False})
        if user_info:
            return render_template("profile.html", user_info=user_info)
        else:
            flash("User not found", "error")            
            return redirect(url_for('home')) 
    else:
        return redirect(url_for('login'))



# UPDATE PROFILE
@app.route('/profile/update', methods=['POST'])
def profile_update():
    if is_logged_in():
        username = session['username']
        user_info = db.users.find_one({'username': username}, {'_id': False})

        name_receive = request.form['name_give']
        about_receive = request.form['about_give']

        new_doc = {
            'profile_name' : name_receive,
            'profile_info' : about_receive,
        }

        if 'file_give' in request.files:
            file = request.files.get('file_give')
            filename = secure_filename(file.filename)
            extension = filename.split('.')[-1]
            file_path = f'profile_pics/{username}.{extension}'
            file.save('./static/' + file_path)
            new_doc['profile_pic'] = filename
            new_doc['profile_pic_real'] = file_path

        db.users.update_one({'username': username}, {'$set': new_doc})
        return jsonify({'result': 'success', 'msg': 'Your profile has been updated'})

    else:
        return redirect(url_for('login'))


# ADMIN EVENT ADD
@app.route("/admin_event", methods=["POST"])
def save_event():
    if is_logged_in and is_admin():
        image = request.files["file"]
        title = request.form.get("title")
        date = request.form.get("date")
        desc = request.form.get("desc")
        locate = request.form.get("locate")

        today = datetime.now()
        mytime = today.strftime("%Y-%m-%d")

        extension = image.filename.split(".")[-1]
        filename = f"static/event/{title}-{mytime}.{extension}"
        image.save(filename)

        doc = {
            "image": filename,
            "title": title,
            "date": date,
            "desc": desc,
            "locate": locate,
            }
        db.event.insert_one(doc)
        return jsonify({"msg": "complete!"})
    else:
        return "Unauthorized access. Only admins are allowed to access this page."


# ADMIN UPCOMING EVENT
@app.route("/upcoming_event", methods=['GET', 'POST'])
def upcoming():
        if is_logged_in and is_admin():
            current_date = datetime.now().strftime('%Y-%m-%d')

            event= db.event.find({'date': {'$gte': current_date}},{'_id':False})
            return render_template("upcoming-event.html", event=event)
        else:
            return "Unauthorized access. Only admins are allowed to access this page."


# ADMIN PAST EVENT
@app.route("/past_event", methods=['GET', 'POST'])
def past():
        if is_logged_in and is_admin():
            current_date = datetime.now().strftime('%Y-%m-%d')

            event= db.event.find({'date': {'$lt': current_date}},{'_id':False})
            return render_template("past-event.html", event=event)
        else:
            return "Unauthorized access. Only admins are allowed to access this page."

# ADMIN EVENT DELETE
@app.route("/event/delete", methods=["POST"])
def delete_past():
        data = request.json
        if 'title' in data:
              title = data['title']
              db.event.delete_one({'title':title})
              return 'Event deleted succesfully'
        else:
              return jsonify({'error' : 'No title provided'}),400


# ADMIN EVENT DELETE ALL
@app.route('/event/delete-all', methods=["POST"])
def deleteAll_past():
    result = db.event.delete_many({})
    if result.deleted_count > 0:
          return jsonify({'message': 'All event deleted successfully'}),200
    else:
          return jsonify({'error': 'No event found to delete'}),404
      

# ADMIN EVENT UPDATE(masih perbaikan)
@app.route('/event/update', methods=["POST"])
def update_event():
    event_info = db.event.find_one({},{'_id':True})

    title = request.form.get('title')
    locate = request.form.get('locate')
    date = request.form.get('date')
    desc = request.form.get('desc')

    new_doc={
        'title':title,
        'locate':locate,
        'date':date,
        'desc':desc
    }
    if 'image' in request.files:
        file = request.files.get('image')
        filename = secure_filename(file.filename)
        extension= filename.split('.')[-1]
        file_path= f'static/event/{title}.{extension}'
        file.save('./static/'+file_path)
        new_doc['image']=filename
        new_doc['new_image']=file_path

    db.event.update_one(
        {'_id':event_info['_id']},
        {'$set':new_doc}      
    )
    return jsonify({
        'result': 'success', 
        'msg': 'Your event has been updated'
    })


# # EVENT
# @app.route("/event", methods=["GET"])
# def event_show():
#         event= db.event.find({}, {'_id': False})
#         return render_template("event.html", event=event)


# BIO USER
@app.route("/bio/<username>", methods=["GET", "POST"])
def bio(username):
    if is_logged_in():
        user_info = db.users.find_one({'username': username}, {'_id': False})
        return render_template("bio.html", user_info=user_info)
    else:
        return redirect(url_for('login'))
# Event
@app.route("/event", methods=["GET", "POST"])
def event():
    if is_logged_in():
        username = session.get('username')
        current_date = datetime.now().strftime('%Y-%m-%d')

        upcoming_event= db.event.find({'date': {'$gte': current_date}},{'_id':False})
        user_info = db.users.find_one({'username': username}, {'_id': False})
        return render_template("event.html",upcoming_event=upcoming_event, user_info=user_info)
    else:
        return redirect(url_for('login'))

# Gallery
@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    if is_logged_in():
        username = session.get('username')
        gallery = db.gallery.find({}, {'_id': 0, 'filename': 1})
        user_info = db.users.find_one({'username': username}, {'_id': False})
        return render_template("gallery.html", gallery=gallery, user_info=user_info)
    else:
        return redirect(url_for('login'))
    

# ADMIN GALLERY
@app.route('/admin/gallery', methods=['GET', 'POST'])
def admin_gallery():
    if is_logged_in():
        if is_admin():
            username = session['username']
            role = session['role']
            if request.method == "POST":
                file = request.files['file']
                filename = secure_filename(file.filename)

                today = datetime.now()
                mytime = today.strftime('%Y-%m-%d')

                extension = file.filename.split('.')[-1]
                filename = f'static/gallery/{filename}-{mytime}.{extension}'
                file.save(filename)

                db.gallery.insert_one({'filename': filename, 'data': file.read()})
                return 'File uploaded successfully'
            
            # MENGAMBIL DATA DARI DATABASE
            gallery = db.gallery.find({}, {'_id': 0, 'filename': 1})
            return render_template("admin-gallery.html", gallery=gallery)
        else:
            return "Unauthorized access. Only admins are allowed to access this page."
    else:
        return redirect(url_for('login'))

# DELETE GALLERY(IMAGE)
@app.route('/admin/gallery/delete/image', methods=['POST'])
def delete_image():
    if is_logged_in():
        if is_admin():
            data = request.json
            if 'filename' in data:
                filename = data['filename']
                db.gallery.delete_one({'filename': filename})
                return 'File deleted successfully'
            else:
                return jsonify({'error': 'No filename provided'}), 400
        else:
            return "Unauthorized access. Only admins are allowed to access this page.", 403
    else:
        return redirect(url_for('login'))

@app.route('/admin/gallery/delete', methods=['POST'])
def delete_gallery():
    if is_logged_in():
        if is_admin():
            result = db.gallery.delete_many({})
            if result.deleted_count > 0:
                return jsonify({'message': 'All files deleted successfully'}), 200
            else:
                return jsonify({'error': 'No files found to delete'}), 404
        else:
            return jsonify({'error': 'Unauthorized access. Only admins are allowed to access this page.'}), 403
    else:
        return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)