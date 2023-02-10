from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
import firebase_admin
from rest_framework import status
from firebase_admin import credentials
from firebase_admin import auth
from rest_framework import authentication
from rest_framework.permissions import AllowAny
import os


credentials = credentials.Certificate({
    "type": "service_account",
    "project_id": os.environ.get("project_id"),
    "private_key_id": os.environ.get("private_key_id"),
    "private_key": os.environ.get("private_key"),
    "client_email": os.environ.get("client_email"),
    "client_id": os.environ.get("client_id"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-zp0a4%40news-app-66795.iam.gserviceaccount.com"
})

default_app = firebase_admin.initialize_app(credentials)


def authenticateWithFirebase(firebase_id_token):
    try:
        #verify firebase id token
        decoded_token = auth.verify_id_token(firebase_id_token)

        user_id = decoded_token['uid']
        provider = decoded_token['firebase']['sign_in_provider']
        user_email = ""

        try:
            user = auth.get_user(user_id).email
            user_email = user.email

        except Exception as e:
            print("User not found: ", e)
    except Exception as e:
        print("Error while verifying token: ", e)

    return user_id, user_email, provider


class FirebaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        
        token = request.headers.get('Authorization')
        if not token:
            return None

        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']
        except:
            return None

# Create your views here.
class CreateUserAPIView(APIView):
    authentication_classes  = [AllowAny]

    def post(self, request):
        """
        Parameters:

        firebase_id_token (str)
        """
        firebase_id_token = request.data["firebase_id_token"]
        firstname = request.data["name"].split(" ")[0]
        lastname = request.data["name"].split(" ")[1]

        try:
            user_id, email, _ = authenticateWithFirebase(firebase_id_token)
            User.objects.create(
                username = user_id,
                email = email,
                first_name = firstname,
                last_name = lastname
            )

            return Response(status= status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        
        



