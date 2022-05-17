# from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

SAVE_PATH = "static/images/id/"
app = Flask(__name__)
app.config['SECRET_KEY'] = "letbuildthisstuff"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///images.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
db = SQLAlchemy(app)

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


##########################END################################################

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

        password = generate_password_hash(request.form["register-password"], method='pbkdf2:sha256', salt_length=8)
        user = User()
        user.email = email
        user.password = password

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
    data = Image.query.all()
    return render_template("index.html", data=data)


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        for file in request.files["images"]:
            print(file)
    return redirect(url_for("dashboard"))


app.run(debug=True)
