import unittest
from app import app, db
from models import Citizen, Department, Complaint

class TestNavigation(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
    def test_index_redirect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
    def test_protected_routes(self):
        # Test citizen dashboard without login
        response = self.client.get('/citizen-dashboard')
        self.assertEqual(response.status_code, 302)
        
        # Test department dashboard without login
        response = self.client.get('/department-dashboard')
        self.assertEqual(response.status_code, 302)
        
    def test_login_flow(self):
        # Test citizen login
        response = self.client.post('/citizen-login', data={
            'email': 'test@test.com',
            'contact_number': '1234567890'
        })
        self.assertEqual(response.status_code, 302)
        
        # Test department login
        response = self.client.post('/department-login', data={
            'email': 'dept@test.com',
            'contact_number': '1234567890'
        })
        self.assertEqual(response.status_code, 302)

if __name__ == '__main__':
    unittest.main() 