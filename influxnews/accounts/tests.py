from unittest import TestCase
from firebase_admin import credentials
from accounts.auth import FirebaseAuthentication
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

# Create your tests here.
# Create your tests here.

class TestFirebaseAuthentication(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.authenticator = FirebaseAuthentication()

    def test_correct_tokens(self):
        header = {"Authorization": "Id8O2li4eRSzovJda8jmDwlq9IW2"}
        request = self.factory.get("/", headers=header)

        user, exists = self.authenticator.authenticate(request)
        print(user, exists)
        
        self.assertTrue(exists)

    def test_incorrect_token(self):
        request = self.factory.get("/", headers={
            "Authorization": "Id8O2li4eRSzovJda8jmDwlq9IV2"
        })

        user, exists = self.authenticator.authenticate(request)
        print(user, exists)
        
        self.assertTrue(exists)