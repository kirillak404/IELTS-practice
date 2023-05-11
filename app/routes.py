import os
import time

from flask import render_template, request, jsonify, redirect, flash, url_for
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import google

from app import app, db
from app.utils import transcript_file
from app.forms import LoginForm, RegistrationForm

from app.models import User
from sqlalchemy.exc import IntegrityError



@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and/or password.')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already registered and authenticated')
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            flash('A user with this email address is already registered')
            return redirect(url_for('register'))

        flash('Registration successful. You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route("/google_login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    account_info = google.get("/oauth2/v2/userinfo").json()
    user = User.query.filter_by(google_id=account_info["id"]).first()

    if user:
        login_user(user)
    else:
        user = User(email=account_info["email"],
                    google_id=account_info["id"],
                    verified_email=account_info["verified_email"],
                    first_name=account_info["given_name"],
                    last_name=account_info["family_name"],
                    profile_picture=account_info["picture"],
                    locale=account_info["locale"])
        db.session.add(user)
        db.session.commit()
        login_user(user)

    return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file found in request"}), 400

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return jsonify({"error": "No audio file selected"}), 400

    file_name = f"recording_{int(time.time())}.webm"
    audio_path = os.path.join(app.config["UPLOAD_FOLDER"], file_name)
    audio_file.save(audio_path)

    # transcription audio
    transcript = transcript_file(audio_path)

    return render_template("result.html", transcript=transcript)