import os
import PIL.Image
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

SAVE_PATH = "static/assets/images/uploads/"
UPLOAD_FOLDER = "assets/images/uploads/"
app = Flask(__name__)
app.config['SECRET_KEY'] = "letbuildthisstuff"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///images.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
db = SQLAlchemy(app)

app.config["SAVE_PATH"] = SAVE_PATH
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# def admin_only(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if current_user.email != "admin@gmail.com":
#             return abort(403, "Access denied")
#         return f(*args, **kwargs)

# return decorated_function


def allowed_file(filename):
    if filename.split(".")[1] in ALLOWED_EXTENSIONS:
        return True
    else:
        return False


############################### database schema ##############################
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(50), nullable=True, unique=True)
    password = db.Column(db.String(50), nullable=True)
    image = relationship("Image", back_populates="user")


class Image(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(100), nullable=True)
    public = db.Column(db.String(10), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="image")


db.create_all()


########################## END ################################################

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        exist_user = User.query.filter_by(email=request.form["register-email"]).first()

        # checking if user already exist
        if exist_user:
            flash("This user already exist")
            return redirect(url_for('register'))

        if len(request.form["register-password"]) < 8:
            flash("Password too short")
            return redirect(request.url)

        email = request.form["register-email"]
        user_name = request.form["user_name"]
        password = generate_password_hash(request.form["register-password"], method='pbkdf2:sha256', salt_length=8)
        user = User()
        user.email = email
        user.password = password
        user.user_name = user_name

        # committing change to database
        db.session.add(user)
        db.session.commit()

        # logining in user and redirecting to account page
        login_user(user)
        return redirect(url_for('home'))

    return render_template("register.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["singin-email"]).first()

        if not user:
            flash("This user does not exist")
            return redirect(url_for('login'))

        elif check_password_hash(user.password, password=request.form["singin-password"]):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("You entered an incorrect password")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route("/")
def home():
    images = Image.query.all()

    return render_template("index.html", images=images, user=current_user.is_authenticated)


@app.route("/dashboard")
def dashboard():
    if not current_user.is_authenticated:
        return redirect("login")
    images = Image.query.filter_by(user_id=current_user.id).all()

    return render_template("dashboard.html", images=images, user=current_user.is_authenticated)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        files = request.files.getlist("files[]")

        for file in files:
            if file and allowed_file(file.filename):
                file_name = secure_filename(file.name)

                # saving file to file path
                file.save(os.path.join(SAVE_PATH, file_name))
                os.rename(SAVE_PATH + file_name, SAVE_PATH + file.filename)
                image_loc = UPLOAD_FOLDER + file.filename

                # reduce image quality to compress size
                save_dir = SAVE_PATH + file.filename
                image_file = PIL.Image.open(save_dir)
                image_file.save(save_dir, quality=30, optimize=True)

                new_image = Image()

                if "public" in request.form:
                    new_image.public = True

                else:
                    new_image.public = False

                new_image.path = image_loc
                new_image.user_id = current_user.id

                db.session.add(new_image)
                db.session.commit()
            else:
                flash("File not supported. only .jpg, .png, and .jpeg allowed")

        return redirect(url_for("dashboard"))

    return redirect(url_for("dashboard"))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/delete_select", methods=["GET", "POST"])
def delete_select():
    if request.method == "POST":
        images = Image.query.filter_by(user_id=current_user.id).all()
        response = request.form.to_dict()

        for image in images:
            if str(image.id) in response.keys():
                image = Image.query.get(image.id)
                db.session.delete(image)
            db.session.commit()

        return redirect(url_for("dashboard"))

    return redirect(url_for("dashboard"))


@app.route("/delete", methods=["GET", "POST"])
def delete():
    images = Image.query.filter_by(user_id=current_user.id).all()

    for image in images:
        image = Image.query.get(image.id)
        db.session.delete(image)
    db.session.commit()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
