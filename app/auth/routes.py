from flask import render_template, redirect, flash, url_for, request, session
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User
from app.utils import send_amplitude_event
from config.auth import oauth
from config.database import db


def after_login_success(login_method: str):
    # sending login event to Amplitude
    send_amplitude_event(current_user.id,
                         'log in',
                         {'method': login_method})


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            after_login_success(login_method='password')
            return redirect(url_for('main.index'))
        else:
            flash('Login failed. Check your username and/or password.')

    return render_template('/auth/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            send_amplitude_event(user.id,
                                 'complete registration',
                                 {'method': 'password'})
            flash('Registration successful. You can now log in.')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            # This exception occurs when the unique constraint is violated
            db.session.rollback()
            flash('This email is already registered. '
                  'Please choose another one.')
        except SQLAlchemyError as e:
            # Catch any other SQLAlchemy exception
            db.session.rollback()
            flash('An error occurred during registration. '
                  'Please try again later.')

    return render_template('/auth/register.html', form=form)


@bp.route("/login/google")
def login_google():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    redirect_uri = url_for('auth.auth_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@bp.route('/auth/google')
def auth_google():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        flash('Failed to log in with Google.')
        return redirect(url_for('auth.login'))

    # Check if userinfo is present
    google_user_info = token.get('userinfo')
    if not google_user_info:
        flash('Failed to get user information from Google.')
        return redirect(url_for('auth.login'))

    # Check if all required fields are present
    if not google_user_info.get('email') or not google_user_info.get('sub'):
        flash('Failed to get user information from Google.')
        return redirect(url_for('auth.login'))

    # Searching for user in DB, then loging or register + login
    user = User.query.filter_by(email=google_user_info.get('email')).first()
    if user:
        if user.google_account_id is None:
            flash('Please sign in with your email and password.')
            return redirect(url_for('auth.login'))
        elif user.google_account_id != google_user_info.get('sub'):
            flash('This email is linked to a different Google account.')
            return redirect(url_for('auth.login'))
        else:
            login_user(user)
            after_login_success(login_method='google')

    else:
        user = User(email=google_user_info.get('email'),
                    google_account_id=google_user_info.get('sub'),
                    is_email_verified=google_user_info.get('email_verified'),
                    first_name=google_user_info.get('given_name'),
                    last_name=google_user_info.get('family_name'),
                    profile_picture=google_user_info.get('picture'),
                    locale=google_user_info.get('locale'))

        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            send_amplitude_event(user.id,
                                 'complete registration',
                                 {'method': 'google'})
        except IntegrityError:
            db.session.rollback()
            flash('This email is already registered. '
                  'Please choose another one.')
            return redirect(url_for('auth.login'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('An error occurred during registration.'
                  ' Please try again later.')
            return redirect(url_for('auth.login'))

    return redirect(url_for('main.index'))


@bp.route('/logout')
@login_required
def logout():
    send_amplitude_event(current_user.id,
                         'log out')
    logout_user()
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))


@bp.route('/set_device_id', methods=['GET'])
def set_device_id():
    device_id = request.args.get('device_id')
    if device_id:
        session['amplitude_device_id'] = device_id
    return "", 204  # Return an empty 204 No Content response
