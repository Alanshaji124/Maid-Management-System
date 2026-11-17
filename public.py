from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import select, insert
from datetime import datetime

public = Blueprint('public', __name__)

@public.route('/')
def home():
    data = {}
    try:
        data['services'] = select("SELECT * FROM service WHERE status='active' LIMIT 6")
        data['maids'] = select("SELECT * FROM maid WHERE maid_status='active' LIMIT 4")
        data['maids_count'] = select("SELECT COUNT(*) AS cnt FROM maid WHERE maid_status='active'")[0]['cnt']
        data['services_count'] = select("SELECT COUNT(*) AS cnt FROM service WHERE status='active'")[0]['cnt']
        data['bookings_count'] = select("SELECT COUNT(*) AS cnt FROM booking")[0]['cnt']
    except Exception as e:
        print("[!] Error loading home data:", e)
        data['services'] = []
        data['maids'] = []
        data['maids_count'] = 0
        data['services_count'] = 0
        data['bookings_count'] = 0
    return render_template('index.html', data=data)

@public.route('/about')
def about():
    return render_template('index.html', data={})

@public.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('uname', '').strip()
        pasw = request.form.get('passw', '').strip()

        # Secure parameterized query
        res = select("SELECT * FROM login WHERE username=%s AND password=%s", (email, pasw))

        if res:
            user = res[0]
            status = user.get('status', 'active')
            utype = user.get('type')

            if status != 'active':
                flash("Your account is currently inactive. Please contact the administrator.")
                return redirect(url_for("public.login"))

            session['email'] = user['username']
            session['utype'] = utype

            if utype == "admin":
                flash("Welcome back, Admin!")
                return redirect(url_for("admin.adhome"))

            elif utype in ("maid", "staff"):
                maid_rec = select("SELECT * FROM maid WHERE username=%s", (email,))
                if maid_rec:
                    session['mid'] = maid_rec[0]['maid_id']
                    session['maid_name'] = f"{maid_rec[0]['maid_fname']} {maid_rec[0]['maid_lname']}"
                    flash(f"Welcome back, {maid_rec[0]['maid_fname']}!")
                    return redirect(url_for("maid.maidhome"))
                else:
                    flash("Maid profile record not found.")
                    return redirect(url_for("public.login"))

            elif utype == "customer":
                cus_rec = select("SELECT * FROM customer WHERE username=%s", (email,))
                if cus_rec:
                    session['cid'] = cus_rec[0]['customer_id']
                    session['customer_name'] = f"{cus_rec[0]['c_fname']} {cus_rec[0]['c_lname']}"
                    flash(f"Welcome back, {cus_rec[0]['c_fname']}!")
                    return redirect(url_for("customer.customerhome"))
                else:
                    flash("Customer profile record not found.")
                    return redirect(url_for("public.login"))
            else:
                flash("Unrecognized account role.")
                return redirect(url_for("public.login"))
        else:
            flash("Invalid Username/Email or Password! Please try again.")
            return redirect(url_for("public.login"))

    return render_template("login.html")

@public.route('/userreg', methods=['GET', 'POST'])
def userreg():
    data = {}
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        fname = request.form.get('fname', '').strip()
        lname = request.form.get('lname', '').strip()
        house = request.form.get('house', '').strip()
        street = request.form.get('street', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', 'Kerala').strip()
        pin = request.form.get('pin', '').strip()
        phone = request.form.get('phone', '').strip()
        gender = request.form.get('gender', 'Male')
        dob = request.form.get('dob', '')

        # Check if email/username already exists
        res = select("SELECT * FROM login WHERE username=%s", (email,))
        if res:
            flash("Username or Email already registered! Please log in.")
            return redirect(url_for("public.login"))
        else:
            insert("INSERT INTO login (username, password, type, status) VALUES (%s, %s, 'customer', 'active')", (email, password))
            insert("""
                INSERT INTO customer (username, c_fname, c_lname, c_housename, c_street, c_city, c_state, c_pincode, c_phone, c_email, c_gender, c_dob, c_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
            """, (email, fname, lname, house, street, city, state, pin, phone, email, gender, dob))

            flash("Registration successful! You can now log in to book a maid.")
            return redirect(url_for("public.login"))

    return render_template('customer_register.html', data=data)

@public.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("public.login"))
