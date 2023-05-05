from django.test import TestCase
import os
import firebase_admin
from firebase_admin import credentials
from accounts.auth import FirebaseAuthentication
import requests

# Create your tests here.
# Create your tests here.

class TestFirebaseAuthentication(TestCase):
    def setUp(self):
        #initialize firebase sdk
        creds = credentials.Certificate(os.path.abspath(os.path.dirname(__file__)) + "/firebase-creds.json")
        firebase_admin.initialize_app(creds)

    def test_correct_tokens(self):
        request = requests.get("https://superficial-vegetable.railay.app/", headers={
            "Authorization": ""
        })

        user, exists = FirebaseAuthentication.authenticate(request)
        
        self.assertTrue(exists)

    def test_incorrect_token(self):
        request = requests.get("https://superficial-vegetable.railay.app/", headers={
            "Authorization": "incorrecttoken"
        })

        user, exists = FirebaseAuthentication.authenticate(request)

        self.assertFalse(exists)