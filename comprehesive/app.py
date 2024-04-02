from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
import base64
import os
import numpy as np
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import Column, Integer, ForeignKey,  func

import uuid
from werkzeug.utils import secure_filename
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///faith_migwi.db'  # SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'PassWord@123'
app.config['UPLOAD_FOLDER'] = 'static/uploads' 
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Apartment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    landmark = db.Column(db.String(100), nullable=False)
    plot_number = db.Column(db.Integer, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.String(20), nullable=False)
    area = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    facilities = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(200), nullable=False)


class Customers(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    second_name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    id_number = db.Column(db.String(20), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    building_name = db.Column(db.String(100), nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    availability = db.Column(db.String(20), nullable=False)
    area = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    facilities = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    apartment_id = db.Column(db.Integer, db.ForeignKey('apartment.id'))  # Define the foreign key

    # Define the relationship with Apartment
    apartment = db.relationship('Apartment', backref=db.backref('rooms'))

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    occupation = db.Column(db.String(100), nullable=True)  # Nullable as per your requirement

    def __init__(self, name, email, password, occupation=None):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)  # Hash password before saving
        self.occupation = occupation


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    apartment = db.Column(db.String(100), nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    land_lord = db.Column(db.String(100), nullable=True)  # Set to nullable
    approve = db.Column(db.Boolean, default=False)

    def __init__(self, tenant_id, apartment, room_number):
        self.tenant_id = tenant_id
        self.apartment = apartment
        self.room_number = room_number



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['firstName']
        second_name = request.form['secondName']
        surname = request.form['surname']
        email = request.form['email']
        id_number = request.form['idNumber']
        phone_number = request.form['phoneNumber']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']

        # Check if the ID is already registered
        existing_customer = Customers.query.filter_by(id_number=id_number).first()
        if existing_customer:
            flash('ID is already registered for another account', 'error')
            return redirect(url_for('signup'))

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')


        new_customer = Customers(
            first_name=first_name,
            second_name=second_name,
            surname=surname,
            email=email,
            id_number=id_number,
            phone_number=phone_number,
            password=hashed_password
        )

        db.session.add(new_customer)
        db.session.commit()

        flash('Account created successfully', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')

@app.route('/login_page', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Customers.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            # Set user's ID and id_number in the session
            session['user_id'] = user.id
            session['id_number'] = user.id_number

            # Check if the id_number has an account registered
            if has_account(session['id_number']):
                flash('Login successful', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Login successful, but no account found for this id_number', 'warning')
                return 'you are in'

        else:
            flash('Login failed. Check your email and password.', 'danger')

    return render_template('login.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Check if the user is logged in
    if 'user_id' in session:
        # Fetch the user from the database using the user_id stored in the session
        user = Customers.query.get(session['user_id'])
        
        # Check if the user exists
        if user:
            # Fetch apartments based on the user's pincode
            user_pincode = user.id_number  # Assuming pincode is a field in the Customers model
            user_apartments = Apartment.query.filter_by(pincode=user_pincode).all()
            user_bookings = Booking.query.join(Apartment, Booking.apartment == Apartment.name).filter(Apartment.pincode == user_pincode).all()
            
            # Pass the user's name and apartments to the template
            return render_template('dashboard.html', user=user, user_apartments=user_apartments, user_bookings=user_bookings)
    
    # If the user is not logged in or not found, redirect to the login page
    return redirect(url_for('login_page'))

@app.route('/room_request')
def room_request():
    if 'user_id' in session:
        # Fetch the user from the database using the user_id stored in the session
        user = Customers.query.get(session['user_id'])
        
        # Check if the user exists
        if user:
            # Fetch apartments based on the user's pincode
            user_pincode = user.id_number  # Assuming pincode is a field in the Customers model
            user_apartments = Apartment.query.filter_by(pincode=user_pincode).all()
            user_bookings = Booking.query.join(Apartment, Booking.apartment == Apartment.name).filter(Apartment.pincode == user_pincode).all()
            
            # Pass the user's name and apartments to the template
            return render_template('room_requests.html', user=user, user_apartments=user_apartments, user_bookings=user_bookings)
    
    # If the user is not logged in or not found, redirect to the login page
    return redirect(url_for('login_page'))
        
def has_account(id_number):
    # Check if an account exists with the given ID number
    existing_account = Customers.query.filter_by(id_number=id_number).first()
    return existing_account is not None

@app.route('/apartment/register', methods=['POST'])
def register_apartment():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You need to be logged in to access this page.', 'danger')
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        # Fetch the logged-in user's ID number
        id_number = session.get('id_number')

        # Extract data from the form
        name = request.form['name']
        address = request.form['Address']
        landmark = request.form['Landmark']
        plot_number = request.form['Plot']
        city = request.form['City']
        pincode = id_number  # Assign the logged-in user's ID number
        country = request.form['Country']
        availability = request.form['Availability']
        area = request.form['Area']
        price = request.form['Price']
        facilities = request.form['Facilities']
        description = request.form['Description']
        image = request.files['file']

        # Save the image file to the server
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # Create a new Apartment object
        new_apartment = Apartment(
            name=name,
            address=address,
            landmark=landmark,
            plot_number=plot_number,
            city=city,
            pincode=pincode,
            country=country,
            availability=availability,
            area=area,
            price=price,
            facilities=facilities,
            description=description,
            image=image_filename
        )

        # Add the new apartment to the database session and commit changes
        db.session.add(new_apartment)
        db.session.commit()

        # Optionally, you can redirect the user to a success page
        flash('Apartment registered successfully.', 'success')
        return redirect(url_for('dashboard'))

    # If the request method is not POST, redirect to the login page
    flash('Invalid request method.', 'danger')
    return redirect(url_for('login_page'))


@app.route('/apartment/register', methods=['GET'])
def show_apartment_registration_form():
    # Optionally, you can pass any data needed for rendering the template
    return render_template('apmt_reg.html')


@app.route('/apartments')
def list_apartments():
    apartments = Apartment.query.all()  # Retrieve all apartments from the database
    return render_template('apartments.html', apartments=apartments)


@app.route('/room/register', methods=['POST'])
def register_room():
    if request.method == 'POST':
        building_name = request.form['building_name']
        room_number = request.form['room']
        availability = request.form['Availability']
        area = request.form['Area']
        price = request.form['Price']
        facilities = request.form['Facilities']
        description = request.form['Description']
        image = request.files['file']

        # Save the image file to the server
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # Create a new Room object
        new_room = Room(
            building_name=building_name,
            room_number=room_number,
            availability=availability,
            area=area,
            price=price,
            facilities=facilities,
            description=description,
            image=image_filename
        )

        # Add the new room to the database session and commit changes
        db.session.add(new_room)
        db.session.commit()

        # Optionally, you can redirect the user to a success page
        return 'success'

    # Handle GET request or other methods if necessary
    return redirect(url_for('error'))

@app.route('/room/register', methods=['GET'])
def show_room_registration_form():
    # Retrieve registered apartments to populate the dropdown menu
    apartments = Apartment.query.all()
    return render_template('room_reg.html', apartments=apartments)

@app.route('/apartments/<int:apartment_id>/rooms')
def list_rooms(apartment_id):
    # Fetch the apartment based on the apartment_id
    apartment = Apartment.query.get_or_404(apartment_id)
    # Fetch rooms associated with this apartment
    rooms = Room.query.filter_by(building_name=apartment.name).all()
    return render_template('rooms.html', apartment=apartment, rooms=rooms)

@app.route('/base')
def base():
    return render_template('base.html')

@app.route('/register_tenant', methods=['GET'])
def register_tenant_form():
    return render_template('register_tenant.html')

# Route to handle tenant registration form submission
@app.route('/register_tenant', methods=['POST'])
def register_tenant():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        occupation = request.form['occupation']

        # Check if email is already registered
        existing_tenant = Tenant.query.filter_by(email=email).first()
        if existing_tenant:
            flash('Email is already registered.', 'error')
            return redirect(url_for('register_tenant_form'))

        # Create new Tenant object
        new_tenant = Tenant(name=name, email=email, password=password, occupation=occupation)

        # Add new tenant to the database session and commit changes
        db.session.add(new_tenant)
        db.session.commit()

        flash('Tenant registered successfully.', 'success')
        return redirect(url_for('register_tenant_form'))

@app.route('/tenant_login', methods=['GET'])
def tenant_login_form():
    return render_template('tenant_login.html')

# Route to handle tenant login form submission
@app.route('/tenant_login', methods=['POST'])
def tenant_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if email exists in the database
        tenant = Tenant.query.filter_by(email=email).first()

        if tenant and check_password_hash(tenant.password, password):
            print('Login successful')
            # Generate a unique session key for the user
            session_key = f"user_{tenant.id}"
            
            # Check if session exists and delete it to avoid collision
            if session_key in session:
                session.pop(session_key)

            # Add tenant's id to the session using the unique session key
            session[session_key] = tenant.id
            print(session)

            flash('Login successful', 'success')
            return redirect(url_for('dashboard_tenant'))  # Redirect to the tenant dashboard

        else:
            flash('Login failed. Check your email and password.', 'danger')
            return redirect(url_for('tenant_login_form'))  # Redirect back to the login form if login fails

    # Redirect to the login form if the request method is not POST
    return redirect(url_for('tenant_login_form'))



@app.route('/dashboard_tenant')
def dashboard_tenant():
    # Check if the tenant is logged in using the appropriate session key
    session_key = get_session_key()  # Helper function to get session key
    if session_key in session:
        # Retrieve the tenant ID from the session
        tenant_id = session[session_key]
        
        # Fetch the tenant from the database based on the tenant ID
        tenant = Tenant.query.get(tenant_id)
        
        # Check if the tenant exists
        if tenant:
            # Render the dashboard template and pass the tenant's information
            return render_template('dashboard_tenant.html', tenant=tenant)
        else:
            flash('Tenant not found', 'error')
            return redirect(url_for('index'))  # Redirect to the homepage if tenant not found
    else:
        flash('You need to log in first', 'error')
        return redirect(url_for('tenant_login_form'))  # Redirect to the login page if not logged in







# Helper function to get the session key based on user's ID
def get_session_key():
    if 'user_id' in session:
        return f"user_{session['user_id']}"
    else:
        return None
# Route to display vacant rooms and welcome the tenant


@app.route('/vacant_rooms/<string:tenant_name>')
def vacant_rooms(tenant_name):
    # Get the tenant's session key
    session_key = get_session_key()

    # Check if the session key exists in the session
    if session_key in session:
        # Get the tenant's id from the session
        tenant_id = session[session_key]

        # Retrieve all bookings for the current tenant from the database
        bookings = Booking.query.filter_by(tenant_id=tenant_id).all()

        # Fetch vacant rooms
        vacant_rooms_list = Room.query.filter_by(availability='Vacant').all()
        
        # Fetch tenant's name based on tenant_id
        tenant = Tenant.query.get(tenant_id)
        tenant_name = tenant.name  # Assuming 'name' is the attribute in Tenant model containing the tenant's name

        return render_template('vacant_rooms.html', tenant_name=tenant_name, vacant_rooms=vacant_rooms_list, bookings=bookings)

    # If the user is not logged in or not found, redirect to the login page
    return redirect(url_for('tenant_login_form'))




@app.route('/room_deals/<int:room_id>')
def room_deals(room_id):
    # Retrieve room details based on room_id
    room = Room.query.get(room_id)
    if room:
        return render_template('room_deals.html', room=room)
    else:
        flash('Room not found', 'error')
        return redirect(url_for('vacant_rooms'))


@app.route('/book_room/<int:room_id>', methods=['POST'])
def book_room(room_id):
    if 'user_id' in session:  # Check if the user is logged in
        user_id = session['user_id']  # Get the user ID from the session
        tenant = Tenant.query.get(user_id)  # Retrieve the tenant from the database

        if tenant:
            room = Room.query.get(room_id)  # Retrieve the room based on the room ID

            if room and room.availability == 'Vacant':  # Check if the room exists and is vacant
                # Create a new booking
                new_booking = Booking(
                    tenant_id=user_id,
                    apartment=room.building_name,
                    room_number=room.room_number
                )

                # Add the booking to the database session and commit changes
                db.session.add(new_booking)
                db.session.commit()



                flash('Room booked successfully.', 'success')
                return redirect(url_for('list_apartments'))  # Redirect to the apartments listing page

    flash('Booking failed. Please try again.', 'error')
    return redirect(url_for('list_apartments'))


from sqlalchemy.orm import joinedload

@app.route('/approve_booking/<int:booking_id>', methods=['POST'])
def approve_booking(booking_id):
    # Fetch the booking from the database based on the booking_id
    booking = Booking.query.get(booking_id)
    
    # Check if the booking exists
    if booking:
        # Update the land_lord column with the user's ID in session
        if 'user_id' in session:
            booking.land_lord = session['user_id']
            db.session.commit()
            flash('Booking approved successfully', 'success')
        else:
            flash('User not logged in', 'danger')
    else:
        flash('Booking not found', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/')
def index():
    # Assuming your background image is stored in the static directory
    background_image = 'static/image.jpg'
    return render_template('index.html', background_image=background_image)

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


@app.route('/manage_apmt')
def manage_apmt():
    if 'user_id' in session:
        # Fetch the user from the database using the user_id stored in the session
        user = Customers.query.get(session['user_id'])
        
        # Check if the user exists
        if user:
            # Fetch apartments based on the user's pincode
            user_pincode = user.id_number  # Assuming pincode is a field in the Customers model
            user_apartments = Apartment.query.filter_by(pincode=user_pincode).all()
            user_bookings = Booking.query.join(Apartment, Booking.apartment == Apartment.name).filter(Apartment.pincode == user_pincode).all()
            
            # Pass the user's name and apartments to the template
            return render_template('manage_apmt.html', user=user, user_apartments=user_apartments, user_bookings=user_bookings)
    
    # If the user is not logged in or not found, redirect to the login page
    return redirect(url_for('login_page'))

@app.route('/delete_apartment/<int:apartment_id>', methods=['POST'])
def delete_apartment(apartment_id):
    # Fetch the apartment from the database based on the apartment_id
    apartment = Apartment.query.get(apartment_id)
    
    if apartment:
        # Delete the apartment from the database session
        db.session.delete(apartment)
        db.session.commit()
        flash('Apartment deleted successfully.', 'success')
    else:
        flash('Apartment not found.', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/delete_room/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    # Fetch the room from the database based on the room_id
    room = Room.query.get(room_id)
    
    if room:
        # Delete the room from the database session
        db.session.delete(room)
        db.session.commit()
        flash('Room deleted successfully.', 'success')
    else:
        flash('Room not found.', 'error')
    
    # Redirect back to the same apartment's rooms listing
    return redirect(url_for('list_rooms', apartment_id=room.apartment_id))




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)