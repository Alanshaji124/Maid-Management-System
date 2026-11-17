# HomeMaid — Maid Booking Management System

> **Academic Project**: Bachelor's Degree Capstone (Rajagiri)  
> **Tech Stack**: Python (Flask) • SQLite / MySQL • Jinja2 • HTML5 / CSS3 / Bootstrap  
> **Status**: Complete, Secured, and Fully Functional

---

## 🌟 Overview

**HomeMaid** is a full-featured web-based Maid Booking Management System designed to bridge households and verified domestic maids. It provides role-based access for **Administrators**, **Customers**, and **Maids**, covering the entire service lifecycle from service discovery, date/shift scheduling, mock payment processing, job tracking, maid assignment, to feedback and complaint resolution.

---

## 🚀 Key Features by User Role

### 1. 🛡️ Administrator Portal (`/admin`)
- **Dashboard**: High-level KPI metrics (total registered maids, customers, bookings, revenue, and pending complaints).
- **Maid Management**: Register, edit, activate, or deactivate maids.
- **Service Catalog**: Create and maintain domestic services (Deep Cleaning, Cooking, Babysitting, etc.) with custom pricing.
- **Slot Management**: Configure morning, afternoon, evening, or full-day working shifts.
- **Booking & Assignment**: Real-time overview of customer bookings with ability to assign/reassign maids and update statuses.
- **Financial Audit**: Transaction log with payment modes (Card, UPI, Cash on Service) and transaction references.
- **Customer Directory**: Customer lookup, search filtering, and status controls.
- **Help Desk**: Review and reply to customer inquiries and complaints.

### 2. 👤 Customer Portal (`/customer`)
- **Interactive Home & Catalogs**: Browse specialized services and maid profiles with experience ratings.
- **Scheduling & Booking Flow**:
  - Select service & preferred maid (or auto-assign).
  - Pick service date & shift slot.
  - Custom instructions and automatic rate calculation.
- **Multi-Option Payment Gateway**:
  - Credit / Debit Card simulation.
  - UPI payment request.
  - Cash on Service (pay upon completion).
- **Booking History**: Real-time status tracking (`Confirmed`, `In Progress`, `Completed`, `Cancelled`).
- **Rating & Reviews**: Rate maids (1 to 5 stars) and leave written testimonials.
- **Help & Support**: Raise issue tickets and view official admin responses.
- **Profile**: Manage contact info, house name, and service address.

### 3. 🧹 Maid / Staff Portal (`/maid`)
- **Maid Dashboard**: Daily schedule overview, upcoming assignments, and performance rating summary.
- **Assigned Jobs**: View customer contact details, service addresses, and instructions.
- **Job Status Progression**: Toggle status between `Start Job (In Progress)` and `Mark Completed`.
- **Client Reviews**: Read verified feedback submitted by customers.
- **Profile**: Update contact details, bio, and hourly pricing.

---

## 🔐 Security & Reliability Enhancements

- **Parameterized Queries**: All database operations use parameterized queries (`%s` / `?`) to eliminate SQL Injection (SQLi).
- **Session Authentication Guards**: Protected route decorators prevent unauthorized access to Admin, Customer, and Maid dashboards.
- **Zero-Config Dual-Engine Database**:
  - Automatically runs with **SQLite** (`database/maidbooking.db`) out-of-the-box without requiring local MySQL/XAMPP setup.
  - Automatically switches to **MySQL** whenever MySQL is running on `localhost:3306` with database `maidbooking`.
  - Comprehensive SQL dump available at `database/maidbooking_complete.sql` for phpMyAdmin or MySQL Workbench.

---

## 🔑 Demo Account Credentials

| Role | Username / Email | Password | Portal Link |
|---|---|---|---|
| **Administrator** | `admin` | `admin` | `/admin/adhome` |
| **Customer** | `arun@gmail.com` | `arun` | `/customer/customerhome` |
| **Maid / Staff** | `staff` | `staff` | `/maid/maidhome` |
| **Maid (Mary)** | `mary@maid.com` | `mary123` | `/maid/maidhome` |

*Note: New customers can also register directly via the [Customer Registration](/userreg) page.*

---

## 🛠️ Setup & Running

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python main.py
```
The application will start on: **http://localhost:5437**

### 3. Run Automated Tests
```bash
python test_app.py
```

---

## 📁 Project Structure

```
maid booking rajagiri/
├── main.py                     # Flask entry point & blueprint registration
├── database.py                 # Dual SQLite / MySQL connection & parameterized queries
├── public.py                   # Public routes (Landing, Login, Registration)
├── admin.py                    # Admin portal controller
├── customer.py                 # Customer booking portal controller
├── maid.py                     # Maid/Staff portal controller
├── requirements.txt            # Python dependencies
├── test_app.py                 # Automated unit and integration test suite
├── database/
│   ├── maidbooking_complete.sql # Full MySQL database export
│   └── maidbooking.db          # Auto-generated SQLite database
├── templates/                  # Jinja2 HTML templates
│   ├── admin_*.html            # Admin dashboard and management views
│   ├── customer_*.html         # Customer booking, payment, and history views
│   ├── maid_*.html             # Maid dashboard and job views
│   ├── public_header.html      # Public navigation bar
│   ├── index.html              # Landing page
│   ├── login.html              # Authentication page
│   └── 404.html                # Error page
└── static/                     # CSS, JavaScript, and asset files
```
