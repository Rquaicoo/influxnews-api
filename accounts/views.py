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


def authenticateWithFirebase(firebase_id_token):
    try:
        #verify firebase id token
        decoded_token = auth.verify_id_token(firebase_id_token)

        user_id = decoded_token['uid']
        provider = decoded_token['firebase']['sign_in_provider']
        user_email = ""

        try:
            print("User found: ", auth.get_user(user_id))
            user = auth.get_user(user_id).email
            user_email = user.email

        except Exception as e:
            print("User not found: ", e)
    except Exception as e:
        print("Error while verifying token: ", e)

    return user_id, user_email, provider


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

        if User.objects.filter(username=user_id).exists():
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

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
        
        



