from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
import firebase_admin
from rest_framework import status
from firebase_admin import credentials
from firebase_admin import auth
from rest_framework import authentication
from .account_serializers import UserSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
import os


def authenticateWithFirebase(firebase_id_token):

    user, exists = authentication.FirebaseAuthentication().authenticate(firebase_id_token)

    return user, exists


# Create your views here.
class CreateUserAPIView(APIView):
    authentication_classes  = [AllowAny]

    def post(self, request):
        """
        Parameters:

        firebase_id_token (str)
        """
        try:
            return Response(status= status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        

class User(APIView):
    authentication_classes = [IsAuthenticated]

    def get(self, request):
        """
        Parameters:

        firebase_id_token (str)
        """
        
        return Response(status=status.HTTP_200_OK)

    
    def put(self, request):
        """
        Parameters:

        firebase_id_token (str)
        """

        return Response(status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request):
        """
        Parameters:

        firebase_id_token (str)
        """
        return Response(status=status.HTTP_200_OK)






