from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import select, insert, update, delete
from datetime import datetime

admin = Blueprint('admin', __name__)

def is_admin():
    return session.get('email') and session.get('utype') == 'admin'

@admin.before_request
def check_admin_session():
    # Enforce authentication on all admin endpoints
    if not is_admin():
        flash("Admin login required.")
        return redirect(url_for("public.login"))

@admin.route('/adhome')
def adhome():
    data = {}
    # Fetch real statistics for admin dashboard
    try:
        maids_count = select("SELECT COUNT(*) AS cnt FROM maid")[0]['cnt']
        customers_count = select("SELECT COUNT(*) AS cnt FROM customer")[0]['cnt']
        bookings_count = select("SELECT COUNT(*) AS cnt FROM booking")[0]['cnt']
        services_count = select("SELECT COUNT(*) AS cnt FROM service WHERE status='active'")[0]['cnt']
        payments_sum = select("SELECT COALESCE(SUM(amount), 0) AS total FROM payment WHERE payment_status='Paid'")[0]['total']
        pending_complaints = select("SELECT COUNT(*) AS cnt FROM complaint WHERE reply='pending'")[0]['cnt']

        # Recent bookings
        recent_bookings = select("""
            SELECT b.*, c.c_fname, c.c_lname, c.c_phone, s.service, m.maid_fname, m.maid_lname, sl.slot, sl.fromtime, sl.totime
            FROM booking b
            LEFT JOIN customer c ON b.customer_id = c.customer_id
            LEFT JOIN service s ON b.service_id = s.service_id
            LEFT JOIN maid m ON b.maid_id = m.maid_id
            LEFT JOIN slot sl ON b.slot_id = sl.slot_id
            ORDER BY b.booking_id DESC LIMIT 5
        """)

        data['maids_count'] = maids_count
        data['customers_count'] = customers_count
        data['bookings_count'] = bookings_count
        data['services_count'] = services_count
        data['total_revenue'] = payments_sum
        data['pending_complaints'] = pending_complaints
        data['recent_bookings'] = recent_bookings
    except Exception as e:
        print("[!] Error loading admin dashboard stats:", e)
        data['maids_count'] = 0
        data['customers_count'] = 0
        data['bookings_count'] = 0
        data['services_count'] = 0
        data['total_revenue'] = 0
        data['pending_complaints'] = 0
        data['recent_bookings'] = []

    return render_template('admin_home.html', data=data)

# ----------------------------------------------------
# Manage Maids (Staff)
# ----------------------------------------------------
@admin.route('/adminmanagestaff', methods=['GET', 'POST'])
def adminmanagestaff():
    data = {}
    action = request.args.get('action')
    maid_id = request.args.get('stid')
    uname = request.args.get('uname')

    if request.method == 'POST':
        if 'submit' in request.form:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            fname = request.form.get('fname', '').strip()
            lname = request.form.get('lname', '').strip()
            house = request.form.get('house', '').strip()
            street = request.form.get('street', '').strip()
            city = request.form.get('city', '').strip()
            district = request.form.get('district', '').strip()
            pin = request.form.get('pin', '').strip()
            phone = request.form.get('phone', '').strip()
            gender = request.form.get('gender', 'Female')
            dob = request.form.get('dob', '')
            exp = request.form.get('exp', '2 Years')
            rate = request.form.get('rate', 350.00)

            res = select("SELECT * FROM login WHERE username=%s", (email,))
            if res:
                flash("Username/Email already exists!")
            else:
                insert("INSERT INTO login (username, password, type, status) VALUES (%s, %s, 'maid', 'active')", (email, password))
                insert("""
                    INSERT INTO maid (username, maid_fname, maid_lname, maid_housename, maid_street, maid_city, maid_dist, maid_pincode, maid_phone, maid_email, maid_gender, maid_dob, experience, hourly_rate, maid_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
                """, (email, fname, lname, house, street, city, district, pin, phone, email, gender, dob, exp, rate))
                flash("Maid registered successfully!")
                return redirect(url_for("admin.adminmanagestaff"))

        elif 'update' in request.form and maid_id:
            fname = request.form.get('fname', '').strip()
            lname = request.form.get('lname', '').strip()
            house = request.form.get('house', '').strip()
            street = request.form.get('street', '').strip()
            city = request.form.get('city', '').strip()
            district = request.form.get('district', '').strip()
            pin = request.form.get('pin', '').strip()
            phone = request.form.get('phone', '').strip()
            gender = request.form.get('gender', 'Female')
            dob = request.form.get('dob', '')
            exp = request.form.get('exp', '2 Years')
            rate = request.form.get('rate', 350.00)

            update("""
                UPDATE maid SET maid_fname=%s, maid_lname=%s, maid_housename=%s, maid_street=%s, maid_city=%s, maid_dist=%s, maid_pincode=%s, maid_phone=%s, maid_gender=%s, maid_dob=%s, experience=%s, hourly_rate=%s
                WHERE maid_id=%s
            """, (fname, lname, house, street, city, district, pin, phone, gender, dob, exp, rate, maid_id))
            flash("Maid details updated successfully!")
            return redirect(url_for("admin.adminmanagestaff"))

    if action == "active" and maid_id:
        update("UPDATE maid SET maid_status='active' WHERE maid_id=%s", (maid_id,))
        if uname:
            update("UPDATE login SET status='active' WHERE username=%s", (uname,))
        flash("Maid activated!")
        return redirect(url_for("admin.adminmanagestaff"))

    elif action == "inactive" and maid_id:
        update("UPDATE maid SET maid_status='inactive' WHERE maid_id=%s", (maid_id,))
        if uname:
            update("UPDATE login SET status='inactive' WHERE username=%s", (uname,))
        flash("Maid deactivated!")
        return redirect(url_for("admin.adminmanagestaff"))

    elif action == "update" and maid_id:
        val = select("SELECT * FROM maid WHERE maid_id=%s", (maid_id,))
        data['staff'] = val

    data['res'] = select("SELECT * FROM maid ORDER BY maid_id DESC")
    return render_template('admin_manage_staff.html', data=data)

# ----------------------------------------------------
# Manage Services
# ----------------------------------------------------
@admin.route('/adminmanageservices', methods=['GET', 'POST'])
def adminmanageservices():
    data = {}
    action = request.args.get('action')
    cat_id = request.args.get('cat_id')

    if request.method == 'POST':
        if 'submit' in request.form:
            name = request.form.get('name', '').strip()
            desc = request.form.get('desc', '').strip()
            rate = request.form.get('rate', 350.00)

            res = select("SELECT * FROM service WHERE service=%s", (name,))
            if res:
                flash("Service already exists!")
            else:
                insert("INSERT INTO service (service, details, rate, status) VALUES (%s, %s, %s, 'active')", (name, desc, rate))
                flash("Service added successfully!")
                return redirect(url_for("admin.adminmanageservices"))

        elif 'update' in request.form and cat_id:
            name = request.form.get('name', '').strip()
            desc = request.form.get('desc', '').strip()
            rate = request.form.get('rate', 350.00)

            update("UPDATE service SET service=%s, details=%s, rate=%s WHERE service_id=%s", (name, desc, rate, cat_id))
            flash("Service updated successfully!")
            return redirect(url_for("admin.adminmanageservices"))

    if action == "active" and cat_id:
        update("UPDATE service SET status='active' WHERE service_id=%s", (cat_id,))
        flash("Service activated!")
        return redirect(url_for("admin.adminmanageservices"))

    elif action == "inactive" and cat_id:
        update("UPDATE service SET status='inactive' WHERE service_id=%s", (cat_id,))
        flash("Service deactivated!")
        return redirect(url_for("admin.adminmanageservices"))

    elif action == "update" and cat_id:
        data['raw'] = select("SELECT * FROM service WHERE service_id=%s", (cat_id,))

    data['res'] = select("SELECT * FROM service ORDER BY service_id DESC")
    return render_template('admin_manage_category.html', data=data)

# ----------------------------------------------------
# Manage Slots
# ----------------------------------------------------
@admin.route('/adminmanageslots', methods=['GET', 'POST'])
def adminmanageslots():
    data = {}
    data['cat'] = select("SELECT * FROM service WHERE status='active'")
    action = request.args.get('action')
    subid = request.args.get('subid')

    if request.method == 'POST':
        if 'submit' in request.form:
            catid = request.form.get('catid', 0)
            name = request.form.get('name', '').strip()
            ff = request.form.get('from', request.form.get('frossm', '')).strip()
            tt = request.form.get('to', request.form.get('time', '')).strip()

            insert("INSERT INTO slot (service_id, slot, fromtime, totime, status) VALUES (%s, %s, %s, %s, 'active')",
                   (catid, name, ff, tt))
            flash("Slot created successfully!")
            return redirect(url_for("admin.adminmanageslots"))

        elif 'update' in request.form and subid:
            catid = request.form.get('catid', 0)
            name = request.form.get('name', '').strip()
            ff = request.form.get('from', request.form.get('frossm', '')).strip()
            tt = request.form.get('to', request.form.get('time', '')).strip()

            update("UPDATE slot SET service_id=%s, slot=%s, fromtime=%s, totime=%s WHERE slot_id=%s",
                   (catid, name, ff, tt, subid))
            flash("Slot updated successfully!")
            return redirect(url_for("admin.adminmanageslots"))

    if action == "active" and subid:
        update("UPDATE slot SET status='active' WHERE slot_id=%s", (subid,))
        flash("Slot activated!")
        return redirect(url_for("admin.adminmanageslots"))

    elif action == "inactive" and subid:
        update("UPDATE slot SET status='inactive' WHERE slot_id=%s", (subid,))
        flash("Slot deactivated!")
        return redirect(url_for("admin.adminmanageslots"))

    elif action == "update" and subid:
        data['raw'] = select("SELECT * FROM slot WHERE slot_id=%s", (subid,))

    # Fetch slots with associated service names
    data['res'] = select("""
        SELECT sl.*, COALESCE(s.service, 'General / All Services') AS service
        FROM slot sl
        LEFT JOIN service s ON sl.service_id = s.service_id
        ORDER BY sl.slot_id DESC
    """)
    return render_template('admin_manage_subcategory.html', data=data)

# ----------------------------------------------------
# View All Bookings & Maid Assignment
# ----------------------------------------------------
@admin.route('/adminvieworders', methods=['GET', 'POST'])
def adminvieworders():
    data = {}
    action = request.args.get('action')
    bid = request.args.get('bid')

    if request.method == 'POST' and 'assign_maid' in request.form:
        booking_id = request.form.get('booking_id')
        maid_id = request.form.get('maid_id')
        update("UPDATE booking SET maid_id=%s, status='Confirmed' WHERE booking_id=%s", (maid_id, booking_id))
        flash("Maid successfully assigned!")
        return redirect(url_for("admin.adminvieworders"))

    if action == "cancel" and bid:
        update("UPDATE booking SET status='Cancelled' WHERE booking_id=%s", (bid,))
        flash("Booking cancelled.")
        return redirect(url_for("admin.adminvieworders"))

    if action == "complete" and bid:
        update("UPDATE booking SET status='Completed' WHERE booking_id=%s", (bid,))
        flash("Booking marked as Completed.")
        return redirect(url_for("admin.adminvieworders"))

    data['res'] = select("""
        SELECT b.*, c.c_fname, c.c_lname, c.c_phone, c.c_city,
               s.service, s.rate AS service_rate,
               COALESCE(m.maid_fname, 'Unassigned') AS maid_fname,
               COALESCE(m.maid_lname, '') AS maid_lname,
               COALESCE(m.maid_phone, '') AS maid_phone,
               sl.slot, sl.fromtime, sl.totime
        FROM booking b
        LEFT JOIN customer c ON b.customer_id = c.customer_id
        LEFT JOIN service s ON b.service_id = s.service_id
        LEFT JOIN maid m ON b.maid_id = m.maid_id
        LEFT JOIN slot sl ON b.slot_id = sl.slot_id
        ORDER BY b.booking_id DESC
    """)
    data['available_maids'] = select("SELECT * FROM maid WHERE maid_status='active'")
    return render_template('admin_view_booking.html', data=data)

# ----------------------------------------------------
# View Specific Booking Details
# ----------------------------------------------------
@admin.route('/adminviewdetails')
def adminviewdetails():
    data = {}
    bid = request.args.get('bid', request.args.get('omid'))
    if not bid:
        return redirect(url_for("admin.adminvieworders"))

    booking_info = select("""
        SELECT b.*, c.c_fname, c.c_lname, c.c_phone, c.c_email, c.c_housename, c.c_street, c.c_city, c.c_pincode,
               s.service, s.details AS service_details,
               m.maid_id, m.maid_fname, m.maid_lname, m.maid_phone, m.maid_email, m.experience,
               sl.slot, sl.fromtime, sl.totime
        FROM booking b
        LEFT JOIN customer c ON b.customer_id = c.customer_id
        LEFT JOIN service s ON b.service_id = s.service_id
        LEFT JOIN maid m ON b.maid_id = m.maid_id
        LEFT JOIN slot sl ON b.slot_id = sl.slot_id
        WHERE b.booking_id=%s
    """, (bid,))

    if not booking_info:
        flash("Booking record not found.")
        return redirect(url_for("admin.adminvieworders"))

    data['booking'] = booking_info[0]
    data['payment'] = select("SELECT * FROM payment WHERE booking_id=%s", (bid,))
    data['review'] = select("SELECT * FROM review WHERE booking_id=%s", (bid,))
    return render_template('admin_view_details.html', data=data)

# ----------------------------------------------------
# View Payments
# ----------------------------------------------------
@admin.route('/adminviewpayment')
def adminviewpayment():
    data = {}
    data['pay'] = select("""
        SELECT p.*, b.booking_date, b.status AS booking_status,
               c.c_fname, c.c_lname, c.c_phone, s.service
        FROM payment p
        LEFT JOIN booking b ON p.booking_id = b.booking_id
        LEFT JOIN customer c ON p.customer_id = c.customer_id
        LEFT JOIN service s ON b.service_id = s.service_id
        ORDER BY p.payment_id DESC
    """)
    return render_template('admin_view_payments.html', data=data)

# ----------------------------------------------------
# View and Reply to Customer Complaints
# ----------------------------------------------------
@admin.route("/adminviewcomplaints", methods=['GET', 'POST'])
def adminviewcomplaints():
    data = {}
    action = request.args.get('action')
    cid = request.args.get('cid')

    if action == "reply" and cid:
        data['replysec'] = True
        data['cid'] = cid
        if request.method == 'POST' and 'submit' in request.form:
            reply = request.form.get('reply', '').strip()
            update("UPDATE complaint SET reply=%s WHERE complaint_id=%s", (reply, cid))
            flash("Reply sent successfully!")
            return redirect(url_for("admin.adminviewcomplaints"))

    data['res'] = select("""
        SELECT cp.*, c.c_fname, c.c_lname, c.c_city, c.c_phone, c.c_gender
        FROM complaint cp
        LEFT JOIN customer c ON cp.customer_id = c.customer_id
        ORDER BY cp.complaint_id DESC
    """)
    return render_template("admin_view_complaints.html", data=data)

# ----------------------------------------------------
# View Registered Customers
# ----------------------------------------------------
@admin.route('/viewcustomer', methods=['GET', 'POST'])
def viewcustomer():
    data = {}
    action = request.args.get('action')
    cid = request.args.get('cid')
    uname = request.args.get('uname')

    if action == "active" and cid:
        update("UPDATE customer SET c_status='active' WHERE customer_id=%s", (cid,))
        if uname:
            update("UPDATE login SET status='active' WHERE username=%s", (uname,))
        flash("Customer account activated!")
        return redirect(url_for("admin.viewcustomer"))

    elif action == "inactive" and cid:
        update("UPDATE customer SET c_status='inactive' WHERE customer_id=%s", (cid,))
        if uname:
            update("UPDATE login SET status='inactive' WHERE username=%s", (uname,))
        flash("Customer account deactivated!")
        return redirect(url_for("admin.viewcustomer"))

    search_query = request.form.get('search', '').strip() if request.method == 'POST' and 'sc' in request.form else ''
    if search_query:
        param = f"%{search_query}%"
        data['viewcus'] = select("""
            SELECT * FROM customer
            WHERE c_fname LIKE %s OR c_lname LIKE %s OR c_phone LIKE %s OR c_city LIKE %s OR c_email LIKE %s
            ORDER BY customer_id DESC
        """, (param, param, param, param, param))
    else:
        data['viewcus'] = select("SELECT * FROM customer ORDER BY customer_id DESC")

    return render_template('admin_view_customer.html', data=data)

@admin.route('/logout')
def logout():
    session.clear()
    flash("Admin logged out successfully.")
    return redirect(url_for("public.login"))
