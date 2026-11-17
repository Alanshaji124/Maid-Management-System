import unittest
from main import app
import database

class TestMaidBookingApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

    def test_01_public_routes(self):
        print("\n--- Testing Public Routes ---")
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"HomeMaid", res.data)
        print("[+] GET /: 200 OK")

        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Welcome back", res.data)
        print("[+] GET /login: 200 OK")

        res = self.client.get('/userreg')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Create an Account", res.data)
        print("[+] GET /userreg: 200 OK")

    def test_02_admin_portal(self):
        print("\n--- Testing Admin Portal ---")
        res = self.client.get('/admin/adhome')
        self.assertEqual(res.status_code, 302)
        print("[+] GET /admin/adhome (unauthenticated) -> Redirects to login (302)")

        # Login as Admin
        with self.client.session_transaction() as sess:
            sess['email'] = 'admin'
            sess['utype'] = 'admin'

        res = self.client.get('/admin/adhome')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"System Control Dashboard", res.data)
        print("[+] GET /admin/adhome: 200 OK")

        res = self.client.get('/admin/adminmanagestaff')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Active Maid Partners", res.data)
        print("[+] GET /admin/adminmanagestaff: 200 OK")

        res = self.client.get('/admin/adminmanageservices')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Active Domestic Services", res.data)
        print("[+] GET /admin/adminmanageservices: 200 OK")

        res = self.client.get('/admin/adminmanageslots')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Active Working Slots", res.data)
        print("[+] GET /admin/adminmanageslots: 200 OK")

        res = self.client.get('/admin/adminvieworders')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Customer Maid Bookings", res.data)
        print("[+] GET /admin/adminvieworders: 200 OK")

        res = self.client.get('/admin/adminviewpayment')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Payments & Transactions Log", res.data)
        print("[+] GET /admin/adminviewpayment: 200 OK")

        res = self.client.get('/admin/adminviewcomplaints')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Customer Complaints & Inquiries", res.data)
        print("[+] GET /admin/adminviewcomplaints: 200 OK")

        res = self.client.get('/admin/viewcustomer')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Registered Customers", res.data)
        print("[+] GET /admin/viewcustomer: 200 OK")

    def test_03_customer_portal(self):
        print("\n--- Testing Customer Portal ---")
        res = self.client.get('/customer/customerhome')
        self.assertEqual(res.status_code, 302)
        print("[+] GET /customer/customerhome (unauthenticated) -> Redirects to login (302)")

        # Login as Customer Arun
        with self.client.session_transaction() as sess:
            sess['email'] = 'arun@gmail.com'
            sess['utype'] = 'customer'
            sess['cid'] = 1

        res = self.client.get('/customer/customerhome')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Arun", res.data)
        print("[+] GET /customer/customerhome: 200 OK")

        res = self.client.get('/customer/services')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Domestic Home Care Services", res.data)
        print("[+] GET /customer/services: 200 OK")

        res = self.client.get('/customer/maids')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Meet Our Domestic Professionals", res.data)
        print("[+] GET /customer/maids: 200 OK")

        res = self.client.get('/customer/book')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Book a Maid Service", res.data)
        print("[+] GET /customer/book: 200 OK")

        res = self.client.get('/customer/mybookings')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Booking History & Tracking", res.data)
        print("[+] GET /customer/mybookings: 200 OK")

        res = self.client.get('/customer/complaints')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Help & Inquiries", res.data)
        print("[+] GET /customer/complaints: 200 OK")

        res = self.client.get('/customer/profile')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"My Customer Profile", res.data)
        print("[+] GET /customer/profile: 200 OK")

    def test_04_maid_portal(self):
        print("\n--- Testing Maid / Staff Portal ---")
        res = self.client.get('/maid/maidhome')
        self.assertEqual(res.status_code, 302)
        print("[+] GET /maid/maidhome (unauthenticated) -> Redirects to login (302)")

        # Login as Maid Amal
        with self.client.session_transaction() as sess:
            sess['email'] = 'staff'
            sess['utype'] = 'maid'
            sess['mid'] = 1

        res = self.client.get('/maid/maidhome')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Amal", res.data)
        print("[+] GET /maid/maidhome: 200 OK")

        res = self.client.get('/maid/bookings')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Assigned Domestic Jobs", res.data)
        print("[+] GET /maid/bookings: 200 OK")

        res = self.client.get('/maid/reviews')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Client Reviews & Testimonials", res.data)
        print("[+] GET /maid/reviews: 200 OK")

        res = self.client.get('/maid/profile')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"My Maid Profile", res.data)
        print("[+] GET /maid/profile: 200 OK")

if __name__ == '__main__':
    unittest.main()
