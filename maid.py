from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import select, update
from datetime import datetime

maid_bp = Blueprint('maid', __name__)

def is_maid():
    return session.get('email') and session.get('utype') in ('maid', 'staff') and session.get('mid')

@maid_bp.before_request
def check_maid_session():
    if not is_maid():
        flash("Maid/Staff login required.")
        return redirect(url_for("public.login"))

@maid_bp.route('/maidhome')
def maidhome():
    data = {}
    mid = session.get('mid')

    maid_info = select("SELECT * FROM maid WHERE maid_id=%s", (mid,))
    data['maid'] = maid_info[0] if maid_info else {}

    # Stats
    data['total_jobs'] = select("SELECT COUNT(*) AS cnt FROM booking WHERE maid_id=%s", (mid,))[0]['cnt']
    data['pending_jobs'] = select("SELECT COUNT(*) AS cnt FROM booking WHERE maid_id=%s AND status IN ('Confirmed', 'In Progress')", (mid,))[0]['cnt']
    data['completed_jobs'] = select("SELECT COUNT(*) AS cnt FROM booking WHERE maid_id=%s AND status='Completed'", (mid,))[0]['cnt']

    # Rating average
    rating_row = select("SELECT COALESCE(AVG(rating), 5.0) AS avg_rating, COUNT(*) AS count FROM review WHERE maid_id=%s", (mid,))
    data['avg_rating'] = round(float(rating_row[0]['avg_rating']), 1) if rating_row else 5.0
    data['review_count'] = rating_row[0]['count'] if rating_row else 0

    # Upcoming jobs
    data['upcoming_jobs'] = select("""
        SELECT b.*, c.c_fname, c.c_lname, c.c_phone, c.c_city,
               s.service, sl.slot, sl.fromtime, sl.totime
        FROM booking b
        LEFT JOIN customer c ON b.customer_id = c.customer_id
        LEFT JOIN service s ON b.service_id = s.service_id
        LEFT JOIN slot sl ON b.slot_id = sl.slot_id
        WHERE b.maid_id=%s
        ORDER BY b.booking_id DESC LIMIT 5
    """, (mid,))

    return render_template('maid_home.html', data=data)

@maid_bp.route('/bookings', methods=['GET', 'POST'])
def bookings():
    data = {}
    mid = session.get('mid')
    action = request.args.get('action')
    bid = request.args.get('bid')

    if action == "start" and bid:
        update("UPDATE booking SET status='In Progress' WHERE booking_id=%s AND maid_id=%s", (bid, mid))
        flash("Job status updated to: In Progress.")
        return redirect(url_for("maid.bookings"))

    elif action == "complete" and bid:
        update("UPDATE booking SET status='Completed' WHERE booking_id=%s AND maid_id=%s", (bid, mid))
        flash("Great job! Booking marked as Completed.")
        return redirect(url_for("maid.bookings"))

    data['bookings'] = select("""
        SELECT b.*, c.c_fname, c.c_lname, c.c_phone, c.c_housename, c.c_street, c.c_city,
               s.service, sl.slot, sl.fromtime, sl.totime
        FROM booking b
        LEFT JOIN customer c ON b.customer_id = c.customer_id
        LEFT JOIN service s ON b.service_id = s.service_id
        LEFT JOIN slot sl ON b.slot_id = sl.slot_id
        WHERE b.maid_id=%s
        ORDER BY b.booking_id DESC
    """, (mid,))

    return render_template('maid_bookings.html', data=data)

@maid_bp.route('/reviews')
def reviews():
    data = {}
    mid = session.get('mid')
    data['reviews'] = select("""
        SELECT r.*, c.c_fname, c.c_lname, c.c_city, s.service
        FROM review r
        LEFT JOIN customer c ON r.customer_id = c.customer_id
        LEFT JOIN booking b ON r.booking_id = b.booking_id
        LEFT JOIN service s ON b.service_id = s.service_id
        WHERE r.maid_id=%s
        ORDER BY r.review_id DESC
    """, (mid,))
    return render_template('maid_reviews.html', data=data)

@maid_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    mid = session.get('mid')
    if request.method == 'POST':
        fname = request.form.get('fname', '').strip()
        lname = request.form.get('lname', '').strip()
        phone = request.form.get('phone', '').strip()
        house = request.form.get('house', '').strip()
        street = request.form.get('street', '').strip()
        city = request.form.get('city', '').strip()
        dist = request.form.get('dist', '').strip()
        exp = request.form.get('exp', '').strip()
        rate = request.form.get('rate', 350.00)

        update("""
            UPDATE maid SET maid_fname=%s, maid_lname=%s, maid_phone=%s, maid_housename=%s, maid_street=%s, maid_city=%s, maid_dist=%s, experience=%s, hourly_rate=%s
            WHERE maid_id=%s
        """, (fname, lname, phone, house, street, city, dist, exp, rate, mid))
        flash("Profile updated successfully!")
        return redirect(url_for("maid.profile"))

    data = {}
    data['maid'] = select("SELECT * FROM maid WHERE maid_id=%s", (mid,))[0]
    return render_template('maid_profile.html', data=data)

@maid_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("public.login"))
