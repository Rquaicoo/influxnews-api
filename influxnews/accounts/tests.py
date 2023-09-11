from unittest import TestCase
from firebase_admin import credentials
from accounts.auth import FirebaseAuthentication
from django.urls import reverse
from unittest.mock import patch, Mock
from django.test import RequestFactory
import unittest

# Create your tests here.

class TestFirebaseAuthentication(TestCase):
   
    def test_correct_tokens(self):
        valid_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MGFkMTE4YTk0MGFkYzlmMmY1Mzc2YjM1MjkyZmVkZThjMmQwZWUiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiUnVzc2VsbCBRdWFpY29vIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FBY0hUdGNxSUJET2FtNEd0bFpoVWl1dHBuYUxfVTZyQ2tRRjA5ejNwQ2lTR3c9czk2LWMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vbmV3cy1hcHAtNjY3OTUiLCJhdWQiOiJuZXdzLWFwcC02Njc5NSIsImF1dGhfdGltZSI6MTY5MzgyNjI2MCwidXNlcl9pZCI6IklkOE8ybGk0ZVJTem92SmRhOGptRHdscTlJVzIiLCJzdWIiOiJJZDhPMmxpNGVSU3pvdkpkYThqbUR3bHE5SVcyIiwiaWF0IjoxNjk0NDY2NDM4LCJleHAiOjE2OTQ0NzAwMzgsImVtYWlsIjoicnVzc2VsbHF1YWljb28xQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7Imdvb2dsZS5jb20iOlsiMTAyMDI5MTc1MDU1MzUwMTYzNjc5Il0sImVtYWlsIjpbInJ1c3NlbGxxdWFpY29vMUBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJnb29nbGUuY29tIn19.jjxSj5MGzIUTFCjPQ0pqEeIlS30iv8jcLWrP-SiLzTzRmk2sm-usLWRxJVfKcmApzoHdzogLseJkRslDrgoY0XdaO5F9mb4vZQWr3IrI77Ec7yBLpV5NE4s4XAv-spupB0QOkBH25Ck6cw3DDSR7OM9NX4ve5oM0AjHjKEogPH1Bpx3M_qHKjhiu-WMlSuWxddAusVgTHJDAifWcf5oGr55aHLrYydR9rayc7l_-0-UzkWa602LB9g7ot2f_Jw7YY0HLoWD3Pno8RhgZZgg6WRp0WxBngZ5UfJ2qPB7llEFt6OfJP_2VTt6dq-tqQ3eJb1cA7hPpzNLhLq3fP7fkcw"
        request = RequestFactory().get('/')
        request.META['HTTP_AUTHORIZATION'] = valid_token
        
        auth = FirebaseAuthentication()

        user, exists = auth.authenticate(request)

        self.assertIsNotNone(user)
        

    
    def test_authentication_invalid_token(self):
        invalid_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MGFkMTE4YTk0MGFkYzlmMmY1Mzc2YjM1MjkyZmVkZThjMmQwZWUiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiUnVzc2VsbCBRdWFpY29vIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FBY0hUdGNxSUJET2FtNEd0bFpoVWl1dHBuYUxfVTZyQ2tRRjA5ejNwQ2lTR3c9czk2LWMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vbmV3cy1hcHAtNjY3OTUiLCJhdWQiOiJuZXdzLWFwcC02Njc5NSIsImF1dGhfdGltZSI6MTY5MzgyNjI2MCwidXNlcl9pZCI6IklkOE8ybGk0ZVJTem92SmRhOGptRHdscTlJVzIiLCJzdWIiOiJJZDhPMmxpNGVSU3pvdkpkYThqbUR3bHE5SVcyIiwiaWF0IjoxNjk0NDY2NDM4LCJleHAiOjE2OTQ0NzAwMzgsImVtYWlsIjoicnVzc2VsbHF1YWljb28xQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7Imdvb2dsZS5jb20iOlsiMTAyMDI5MTc1MDU1MzUwMTYzNjc5Il0sImVtYWlsIjpbInJ1c3NlbGxxdWFpY29vMUBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJnb29nbGUuY29tIn19.jjxSj5MGzIUTFCjPQ0pqEeIlS30iv8jcLWrP-SiLzTzRmk2sm-usLWRxJVfKcmApzoHdzogLseJkRslDrgoY0XdaO5F9mb4vZQWr3IrI77Ec7yBLpV5NE4s4XAv-spupB0QOkBH25Ck6cw3DDSR7OM9NX4ve5oM0AjHjKEogPH1Bpx3M_qHKjhiu-WMlSuWxddAusVgTHJDAifWcf5oGr55aHLrYydR9rayc7l_-0-UzkWa602LB9g7ot2f_Jw7YY0HLoWD3Pno8RhgZZgg6WRp0WxBngZ5UfJ2qPB7llEFt6OfJP_2VTt6dq-tqQ3eJb1cA7hPpzNLhLq3fP7fkgh"
            
        request = RequestFactory().get('/')
        request.META['HTTP_AUTHORIZATION'] = invalid_token

        auth = FirebaseAuthentication()

        user, exists = auth.authenticate(request)

        self.assertIsNone(user)

if __name__ == '__main__':
    unittest.main()





