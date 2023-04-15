from rest_framework.authentication import BaseAuthentication
from firebase_admin import credentials
from firebase_admin import auth
from django.contrib.auth.models import User
import os
import firebase_admin
from dotenv import load_dotenv

load_dotenv()



class FirebaseAuthentication(BaseAuthentication):

    
    credentials = credentials.Certificate(os.path.abspath(os.path.dirname(__file__)) + "/firebase-creds.json")

    default_app = firebase_admin.initialize_app(credentials)

    def authenticate(self, request):
        
        token = request.headers.get('Authorization')
        if not token:
            return None

        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']

            return (User.objects.get(username=user_id), None)
        
        except:
            return None