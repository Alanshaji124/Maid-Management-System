from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import select, insert, update, delete
from datetime import datetime

customer = Blueprint('customer', __name__)

def is_customer():
    return session.get('email') and session.get('utype') == 'customer' and session.get('cid')

@customer.before_request
def check_customer_session():
    if not is_customer():
        flash("Please log in as Customer to continue.")
        return redirect(url_for("public.login"))

# ----------------------------------------------------
# Customer Dashboard
# ----------------------------------------------------
@customer.route('/customerhome')
def customerhome():
    data = {}
    cid = session.get('cid')

    # Customer profile
    cus_info = select("SELECT * FROM customer WHERE customer_id=%s", (cid,))
    data['customer'] = cus_info[0] if cus_info else {}

    # Stats
    data['total_bookings'] = select("SELECT COUNT(*) AS cnt FROM booking WHERE customer_id=%s", (cid,))[0]['cnt']
    data['active_bookings'] = select("SELECT COUNT(*) AS cnt FROM booking WHERE customer_id=%s AND status IN ('Pending', 'Confirmed', 'In Progress')", (cid,))[0]['cnt']
    data['completed_bookings'] = select("SELECT COUNT(*) AS cnt FROM booking WHERE customer_id=%s AND status='Completed'", (cid,))[0]['cnt']

    # Featured services
    data['services'] = select("SELECT * FROM service WHERE status='active' LIMIT 4")

    # Recent customer bookings
    data['recent_bookings'] = select("""
        SELECT b.*, s.service, COALESCE(m.maid_fname, 'Unassigned') AS maid_fname,
               COALESCE(m.maid_lname, '') AS maid_lname, COALESCE(m.maid_phone, '') AS maid_phone,
               sl.slot, sl.fromtime, sl.totime
        FROM booking b
        LEFT JOIN service s ON b.service_id = s.service_id
        LEFT JOIN maid m ON b.maid_id = m.maid_id
        LEFT JOIN slot sl ON b.slot_id = sl.slot_id
        WHERE b.customer_id=%s
        ORDER BY b.booking_id DESC LIMIT 4
    """, (cid,))

    return render_template('customer_home.html', data=data)

# ----------------------------------------------------
# View Services
# ----------------------------------------------------
@customer.route('/services')
def services():
    data = {}
    data['services'] = select("SELECT * FROM service WHERE status='active'")
    return render_template('customer_services.html', data=data)

# ----------------------------------------------------
# View Maids
# ----------------------------------------------------
@customer.route('/maids')
def maids():
    data = {}
    data['maids'] = select("SELECT * FROM maid WHERE maid_status='active'")
    return render_template('customer_maids.html', data=data)

# ----------------------------------------------------
# Book a Maid / Service
# ----------------------------------------------------
@customer.route('/book', methods=['GET', 'POST'])
def book():
    data = {}
    cid = session.get('cid')
    selected_service_id = request.args.get('service_id', '')
    selected_maid_id = request.args.get('maid_id', '0')

    cus = select("SELECT * FROM customer WHERE customer_id=%s", (cid,))[0]
    data['customer'] = cus
    data['services'] = select("SELECT * FROM service WHERE status='active'")
    data['maids'] = select("SELECT * FROM maid WHERE maid_status='active'")
    data['slots'] = select("SELECT * FROM slot WHERE status='active'")
    data['selected_service_id'] = str(selected_service_id)
    data['selected_maid_id'] = str(selected_maid_id)

    if request.method == 'POST':
        service_id = request.form.get('service_id')
        maid_id = request.form.get('maid_id', 0)
        slot_id = request.form.get('slot_id')
        booking_date = request.form.get('booking_date')
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        notes = request.form.get('notes', '').strip()
        house_size = request.form.get('house_size', '1 BHK')
        addons = request.form.getlist('addons')
        calculated_total = request.form.get('calculated_total')

        # Service rate base
        srv = select("SELECT rate FROM service WHERE service_id=%s", (service_id,))
        base_rate = float(srv[0]['rate']) if srv else 350.0

        if calculated_total:
            try:
                amount = float(calculated_total)
            except ValueError:
                amount = base_rate
        else:
            amount = base_rate

        # Enrich notes with customizer scope
        addon_str = ", ".join(addons) if addons else "None"
        custom_spec = f"Scope: {house_size} | Addons: {addon_str}"
        notes = f"{custom_spec} | Notes: {notes}" if notes else custom_spec

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        bid = insert("""
            INSERT INTO booking (customer_id, maid_id, service_id, slot_id, booking_date, booking_address, contact_phone, notes, total_amount, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending', %s)
        """, (cid, maid_id, service_id, slot_id, booking_date, address, phone, notes, amount, now_str))

        flash("Booking request created! Please choose your payment method.")
        return redirect(url_for("customer.payment", booking_id=bid))

    return render_template('customer_book.html', data=data)

# ----------------------------------------------------
# Payment Gateway (Mock)
# ----------------------------------------------------
@customer.route('/payment', methods=['GET', 'POST'])
def payment():
    data = {}
    cid = session.get('cid')
    bid = request.args.get('booking_id')
    if not bid:
        flash("No booking selected for payment.")
        return redirect(url_for("customer.customerhome"))

    booking = select("""
        SELECT b.*, s.service, sl.slot, sl.fromtime, sl.totime,
               COALESCE(m.maid_fname, 'Unassigned') AS maid_fname,
               COALESCE(m.maid_lname, '') AS maid_lname
        FROM booking b
        LEFT JOIN service s ON b.service_id = s.service_id
        LEFT JOIN slot sl ON b.slot_id = sl.slot_id
        LEFT JOIN maid m ON b.maid_id = m.maid_id
        WHERE b.booking_id=%s AND b.customer_id=%s
    """, (bid, cid))

    if not booking:
        flash("Booking not found.")
        return redirect(url_for("customer.customerhome"))

    data['booking'] = booking[0]

    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'Card')
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        txn_id = f"TXN-MB-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        insert("""
            INSERT INTO payment (booking_id, customer_id, amount, payment_method, transaction_id, payment_status, payment_date)
            VALUES (%s, %s, %s, %s, %s, 'Paid', %s)
        """, (bid, cid, data['booking']['total_amount'], payment_method, txn_id, now_str))

        update("UPDATE booking SET status='Confirmed' WHERE booking_id=%s", (bid,))
        flash(f"Payment successful! Transaction ID: {txn_id}. Your maid booking is confirmed.")
        return redirect(url_for("customer.mybookings"))

    return render_template('customer_payment.html', data=data)

# ----------------------------------------------------
# Customer Bookings History
# ----------------------------------------------------
@customer.route('/mybookings')
def mybookings():
    data = {}
    cid = session.get('cid')
    action = request.args.get('action')
    bid = request.args.get('bid')

    if action == "cancel" and bid:
        update("UPDATE booking SET status='Cancelled' WHERE booking_id=%s AND customer_id=%s", (bid, cid))
        flash("Booking cancelled successfully.")
        return redirect(url_for("customer.mybookings"))

    data['bookings'] = select("""
        SELECT b.*, s.service, sl.slot, sl.fromtime, sl.totime,
               COALESCE(m.maid_fname, 'Unassigned') AS maid_fname,
               COALESCE(m.maid_lname, '') AS maid_lname,
               COALESCE(m.maid_phone, '') AS maid_phone,
               (SELECT COUNT(*) FROM review WHERE booking_id=b.booking_id) AS has_review
        FROM booking b
        LEFT JOIN service s ON b.service_id = s.service_id
        LEFT JOIN slot sl ON b.slot_id = sl.slot_id
        LEFT JOIN maid m ON b.maid_id = m.maid_id
        WHERE b.customer_id=%s
        ORDER BY b.booking_id DESC
    """, (cid,))

    return render_template('customer_bookings.html', data=data)

# ----------------------------------------------------
# Rate & Review Maid
# ----------------------------------------------------
@customer.route('/rate_maid', methods=['GET', 'POST'])
def rate_maid():
    data = {}
    cid = session.get('cid')
    bid = request.args.get('bid')

    booking = select("""
        SELECT b.*, s.service, m.maid_id, m.maid_fname, m.maid_lname
        FROM booking b
        LEFT JOIN service s ON b.service_id = s.service_id
        LEFT JOIN maid m ON b.maid_id = m.maid_id
        WHERE b.booking_id=%s AND b.customer_id=%s
    """, (bid, cid))

    if not booking or not booking[0]['maid_id']:
        flash("Invalid booking or no maid assigned.")
        return redirect(url_for("customer.mybookings"))

    data['booking'] = booking[0]

    if request.method == 'POST':
        rating = request.form.get('rating', 5)
        review_text = request.form.get('review_text', '').strip()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        insert("""
            INSERT INTO review (booking_id, customer_id, maid_id, rating, review_text, review_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (bid, cid, data['booking']['maid_id'], rating, review_text, now_str))

        flash("Thank you for your feedback! Your review has been recorded.")
        return redirect(url_for("customer.mybookings"))

    return render_template('customer_review.html', data=data)

# ----------------------------------------------------
# Customer Complaints & Queries
# ----------------------------------------------------
@customer.route('/complaints', methods=['GET', 'POST'])
def complaints():
    data = {}
    cid = session.get('cid')

    if request.method == 'POST':
        complaint_text = request.form.get('complaint', '').strip()
        bid = request.form.get('booking_id', 0)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        insert("""
            INSERT INTO complaint (customer_id, booking_id, complaint, reply, complaint_date)
            VALUES (%s, %s, %s, 'pending', %s)
        """, (cid, bid, complaint_text, now_str))

        flash("Your complaint/inquiry has been submitted. Our admin will respond promptly.")
        return redirect(url_for("customer.complaints"))

    data['complaints'] = select("""
        SELECT * FROM complaint WHERE customer_id=%s ORDER BY complaint_id DESC
    """, (cid,))

    data['my_bookings'] = select("SELECT booking_id, booking_date FROM booking WHERE customer_id=%s", (cid,))
    return render_template('customer_complaints.html', data=data)

# ----------------------------------------------------
# Customer Profile Management
# ----------------------------------------------------
@customer.route('/profile', methods=['GET', 'POST'])
def profile():
    cid = session.get('cid')
    if request.method == 'POST':
        fname = request.form.get('fname', '').strip()
        lname = request.form.get('lname', '').strip()
        phone = request.form.get('phone', '').strip()
        house = request.form.get('house', '').strip()
        street = request.form.get('street', '').strip()
        city = request.form.get('city', '').strip()
        pin = request.form.get('pin', '').strip()

        update("""
            UPDATE customer SET c_fname=%s, c_lname=%s, c_phone=%s, c_housename=%s, c_street=%s, c_city=%s, c_pincode=%s
            WHERE customer_id=%s
        """, (fname, lname, phone, house, street, city, pin, cid))
        flash("Profile updated successfully!")
        return redirect(url_for("customer.profile"))

    data = {}
    data['customer'] = select("SELECT * FROM customer WHERE customer_id=%s", (cid,))[0]
    return render_template('customer_profile.html', data=data)

@customer.route('/logout')
def logout():
    session.clear()
    flash("Customer logged out successfully.")
    return redirect(url_for("public.login"))
