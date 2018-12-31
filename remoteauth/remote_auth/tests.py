import api
from django.test import TestCase
from requests_mock import mock
from django.conf import settings
from datetime import datetime, timedelta

BASE_URL = getattr(settings,'FOOD_JOINT_API_ENDPOINT','')

def url(path:str):
    return api.__full_url__(path)

class ApiAccessTokenTests(TestCase):
    
    @mock()
    def test_access_token_is_fetched_when_not_in_sesstion(self, api_mock):   

        mock_token={"access_token": "yiB2rhfMC5PlRpMVDhGU5I0fD5UB3H", "expires_in": 36000, "timestamp":datetime.now().strftime(api.ISO_DATE_FORMAT), "token_type": "Bearer", "scope": "read write"}
        api_mock.register_uri("POST",url("/oauth/token/"), status_code=200, json=mock_token)
        
        session={}
        token=api.ApiAccessToken().get_access_token(session=session)

        self.assertIsNotNone(token)
        self.assertEqual(token["access_token"],mock_token["access_token"])
        self.assertIsNotNone(token["timestamp"])

    def test_access_token_is_read_from_session_when_in_sesstion_not_expired(self):   
        mock_token={"access_token": "yiB2rhfMC5PlRpMVDhGU5I0fD5UB3H", "expires_in": 36000, "timestamp":datetime.now().strftime(api.ISO_DATE_FORMAT), "token_type": "Bearer", "scope": "read write"}
        session={"site_token":mock_token}
        token=api.ApiAccessToken().get_access_token(session=session)

        self.assertIsNotNone(token)
        self.assertEqual(token["access_token"],mock_token["access_token"])
    
        
    @mock()
    def test_that_new_token_is_fetched_when_existing_token_expires(self, api_mock):
        mock_token={"access_token": "yiB2rhfMC5PlRpMVDhGU5I0fD5UB3H", "expires_in": 36000, "timestamp":datetime.now().strftime(api.ISO_DATE_FORMAT), "token_type": "Bearer", "scope": "read write"}
        api_mock.register_uri("POST",url("/oauth/token/"), status_code=200, json=mock_token)
        
        expired_token_time = datetime.now()-timedelta(seconds=700)
        expired_token={"access_token": "adasdkaklsd7868768787", "expires_in": 600, "timestamp":expired_token_time.strftime(api.ISO_DATE_FORMAT), "token_type": "Bearer", "scope": "read write"}
        session={"site_token": expired_token}
        token=api.ApiAccessToken().get_access_token(session=session)

        self.assertIsNotNone(token)
        self.assertNotEqual(token["access_token"],expired_token["access_token"])
        self.assertEqual(session["site_token"],token)

    @mock()
    def test_that_new_token_is_fetched_when_user_info_is_given(self, api_mock):
        mock_token={"access_token": "yiB2rhfMC5PlRpMVDhGU5I0fD5UB3H", "expires_in": 36000, "timestamp":datetime.now().strftime(api.ISO_DATE_FORMAT), "token_type": "Bearer", "scope": "read write"}
        api_mock.register_uri("POST",url("/oauth/token/"), status_code=200, json=mock_token)
        
        site_token={"access_token": "adasdkaklsd7868768787", "expires_in": 600, "timestamp":datetime.now().strftime(api.ISO_DATE_FORMAT), "token_type": "Bearer", "scope": "read write"}
        session={"site_token": site_token}
        token=api.ApiAccessToken().get_access_token(session=session,username="tester",password="passwed")

        self.assertIsNotNone(token)
        self.assertNotEqual(token["access_token"],site_token["access_token"])
        self.assertNotEqual(session["site_token"],token)
        self.assertIsNotNone(token["timestamp"])

    @mock()
    def test_that_token_is_grabbed_from_session_when_in_session_unexpired(self, api_mock):
        insession_token={"access_token": "yiB2rhfMC5PlRpMVDhGU5I0fD5UB3H", "expires_in": 36000, "timestamp":datetime.now().strftime(api.ISO_DATE_FORMAT), "token_type": "Bearer", "scope": "read write"}
        
        session={"user_token": insession_token}
        token=api.ApiAccessToken().get_access_token(session=session,username="tester",password="passwed")

        self.assertIsNotNone(token)
        self.assertEqual(token["access_token"],insession_token["access_token"])
        self.assertEqual(session["user_token"],token)

    @mock()
    def test_that_new_user_token_is_fetched_when_existing_token_expires(self, api_mock):
        mock_token={"access_token": "yiB2rhfMC5PlRpMVDhGU5I0fD5UB3H", "refresh_token": "wqweq32342342w", "expires_in": 36000, "timestamp":datetime.now().strftime(api.ISO_DATE_FORMAT), "token_type": "Bearer", "scope": "read write"}
        api_mock.register_uri("POST",url("/oauth/token/"), status_code=200, json=mock_token)
        
        expired_token_time = datetime.now()-timedelta(seconds=700)
        expired_token={"access_token": "adasdkaklsd7868768787", "refresh_token": "54654sdasda7yg", "expires_in": 600, "timestamp":expired_token_time.strftime(api.ISO_DATE_FORMAT), "token_type": "Bearer", "scope": "read write"}
        session={"user_token": expired_token}
        token=api.ApiAccessToken().get_access_token(session=session,username="tester",password="passwed")

        self.assertIsNotNone(token)
        self.assertNotEqual(token["access_token"],expired_token["access_token"])
        self.assertEqual(session["user_token"],token)