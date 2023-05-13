from flask import render_template, redirect, flash, url_for
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db, oauth
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
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


# TODO update route to /auth/google
@bp.route('/auth')
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
        if user.google_id is None:
            flash('Please sign in with your email and password.')
            return redirect(url_for('auth.login'))
        elif user.google_id != google_user_info.get('sub'):
            flash('This email is linked to a different Google account.')
            return redirect(url_for('auth.login'))
        else:
            login_user(user)

    else:
        user = User(email=google_user_info.get('email'),
                    google_id=google_user_info.get('sub'),
                    verified_email=google_user_info.get('email_verified'),
                    first_name=google_user_info.get('given_name'),
                    last_name=google_user_info.get('family_name'),
                    profile_picture=google_user_info.get('picture'),
                    locale=google_user_info.get('locale'))

        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
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
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))
