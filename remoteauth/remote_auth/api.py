import requests
import logging
import datetime
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.contrib.auth.models import User
from threading import get_ident
from django.contrib.auth.backends import ModelBackend


logger = logging.getLogger(__name__)

API_CLIENT_ID = getattr(settings, 'FOOD_JOINT_API_CLIENTID', '')
API_CLIENT_SECRET = getattr(settings, 'FOOD_JOINT_API_CLIENT_SECRET', '')
BASE_URL = getattr(settings,'FOOD_JOINT_API_ENDPOINT','')
AUTH=HTTPBasicAuth(API_CLIENT_ID, API_CLIENT_SECRET)
USER_ACCESS_TOKEN_KEY="user_token"
SITE_ACCESS_TOKEN_KEY="site_token"
ISO_DATE_FORMAT = "'%Y-%m-%dT%H:%M:%S'"

_requests={}
class GlobalRequestMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _requests[get_ident()] = {'request':request}
        print("added request: {0}".format(request))
        response = self.get_response(request)
        self.after_view_rendered(request,response)
        return response

    def after_view_rendered(self,request,response):
        data=_requests.pop(get_ident())
        current_request_auth_token=data.get("access_token", None)
        if current_request_auth_token:
            request.session[USER_ACCESS_TOKEN_KEY]=current_request_auth_token
        profile = data.get("user_profile", None)
        if profile:
            request.session["user_profile"]=profile
        
        return response

def get_request():
    data = _requests.get(get_ident(),None)
    if data is not None:
        return data.get("request",None)

def get_request_session():
    request=get_request()
    if request is not None:
        return request.session


class ApiAccessToken:
    def __log_http_failure(self, url,response,context=None):
        logger.error("{context}:= Unable to acquire access token at {url}. Received http {statuscode}: {reason}".format(url=url,
                                                                                                            context=context,
                                                                                                            statuscode=response.status_code,
                                                                                                            reason=response.reason))

    def get_access_token(self, username=None, password=None, session={}):
        
        token = None
        if session.get(USER_ACCESS_TOKEN_KEY,None) or (username and password):
            token = self.__get_access_token_for_user(username=username,password=password,session=session)
        else:            
            token = self.__get_site_access_token(session=session)
        return token

    def __get_site_access_token(self, session={}):
        token = session.get(SITE_ACCESS_TOKEN_KEY,None)
        if token is None or self.__is_expired(token):
            url = __full_url__('/oauth/token/')
            data = {'grant_type':'client_credentials'}
            response = requests.post(url=url, data=data, auth=AUTH)
            if response.ok:
                token = response.json()
                token.update({"timestamp":datetime.datetime.now().strftime(ISO_DATE_FORMAT)})
                session[SITE_ACCESS_TOKEN_KEY] = token
            else:
                self.__log_http_failure(url=url,response=response,context="ApiAccessToken.__get_site_access_token")

        return token

    def __is_expired(self, token:dict):
        token_grabbed_at = datetime.datetime.strptime(token["timestamp"],ISO_DATE_FORMAT)
        now=datetime.datetime.now()
        diff = now - token_grabbed_at
        return diff >= datetime.timedelta(seconds=token["expires_in"])

    def __get_access_token_for_user(self, username,password,session={}):
        token = session.get(USER_ACCESS_TOKEN_KEY,None)
        if token is None or self.__is_expired(token):
            url = __full_url__('/oauth/token/')
            data={}
            if token is not None:
                data.update({'refresh_token': token["refresh_token"], 'grant_type':'refresh_token'})
            else:
                data.update({'username': username, 'password': password, 'grant_type':'password'})
    
            response = requests.post(url=url, data=data, auth=AUTH)        
            if response.ok:
                token = response.json()
                token.update({"timestamp":datetime.datetime.now().strftime(ISO_DATE_FORMAT)})
                session[USER_ACCESS_TOKEN_KEY] = token 
            else:
                self.__log_http_failure(url=url,response=response,context="ApiAccessToken.__get_access_token_for_user")
        
        return token


class RemoteBackend(ModelBackend):
    """
    Custom authentication through a remote API
    """
    
    def get_profile(self, token):
        url = __full_url__("/users/profile/")
        headers = __get_auth_header__(token.get('access_token',None))
        response = requests.get(url,headers=headers, auth=None)
        if response.ok:
            return response.json()
        logger.critical("GET PROFILE FAILED: {0}".format(response.json()))

    def authenticate(self, request, username=None, password=None):
        logger.critical("AUTHENTICATING as {un}:{pwd}".format(un=username,pwd="*****"))
        token =ApiAccessToken().get_access_token(username=username,password=password,session={})
        user = None
        if token:
            user_info = self.get_profile(token)
            if user_info:
                try:
                    user=User.objects.get(username=username)
                except User.DoesNotExist:
                    user = User.objects.create_user(
                        username=user_info['username'],
                        first_name=user_info['first_name'],
                        last_name=user_info['last_name'],
                        email=user_info['email'])
                finally:
                     #keep token in current thread's _requests dict
                    request_data=_requests.get(get_ident(),{})
                    request_data.update({
                        "access_token": token,
                        "user_profile": user_info
                    })
                    _requests[get_ident()]=request_data

                    return user
            else:
                logger.critical("UNABLE to Get Profile")
        else:
            logger.critical("UNABLE to log in")

        #if we ever reach here then return none
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Check the user's profile to see if they have the given permission
        """
        request = get_request()
        return request and user_obj.is_authenticated and perm in request.session.get("user_profile",{}).get('roles',None)

class ApiResults:
    def __init__(self,ok=False,data={},error_code=0,error_message=""):
        self.ok=ok
        self.data=data
        self.error_code=error_code
        self.error_message=error_message


def fetch(path, max_retry=3):
    url = __full_url__(path)
    token = ApiAccessToken().get_access_token(session=get_request_session())
    if token:
        headers = __get_auth_header__(token.get('access_token',None))
        response = requests.get(url,headers=headers, auth=None)
        if response.ok:
            return response.json()
        else:
            #in case http 401 we should refresh access token
            if max_retry and response.status_code==401:
                ApiAccessToken().get_access_token(session=get_request_session())
                return fetch(path, max_retry=max_retry-1)
            else:
                logger.error("api.fetch:= Unable to fetch data at {url}. Received http {statuscode}: {reason}".format(url=url,
                                                                                                            statuscode=response.status_code,
                                                                                                            reason=response.reason))

              
def post(path:str,data:dict, files=None, max_retry=3):
    url = __full_url__(path)
    token = ApiAccessToken().get_access_token(session=get_request_session())
    if token:
        headers = __get_auth_header__(token.get('access_token',None))
        response = requests.post(url,json=data,headers=headers, auth=None, files=files)
        if response.ok:
            return ApiResults(ok=response.ok,data=response.json())
        else:
            #in case http 401 we should refresh access token
            if max_retry and response.status_code==401:
                ApiAccessToken.get_access_token(session=get_request_session())
                return post(path,data=data, files=files, max_retry=max_retry-1)
            else:
                logger.error("api.post:= Unable to post data at {url}. Received http {statuscode}: {reason}. Data={data}".format(url=url,
                                                                                                            statuscode=response.status_code,
                                                                                                            reason=response.reason,
                                                                                                            data=data))

            
            return ApiResults(error_code=response.status_code,error_message=response.reason)
    else:
        logger.fatal("Unable to obtain access token for post request to {0}".format(url))
        return ApiResults(error_code=4000,error_message="Unable to obtain access token")

def put(path:str,data:dict, files=None, max_retry=3):
    url = __full_url__(path)
    token = ApiAccessToken().get_access_token(session=get_request_session())
    logger.critical("RESPONSE OK {}".format(token))
    if token:
        headers = __get_auth_header__(token.get('access_token',None))
        response = requests.put(url,json=data,headers=headers, files=files, auth=None)
       
        if response.ok:
            logger.critical("RESPONSE OK {}".format(response.json()))
            return ApiResults(ok=response.ok,data=response.json())
        else:
            #in case http 401 we should refresh access token
            if max_retry and response.status_code==401:
                ApiAccessToken().get_access_token(session=get_request_session())
                return put(path,data=data, files=files, max_retry=max_retry-1)
            else:
                logger.error("api.put:= Unable to put data at {url}. Received http {statuscode}: {reason}. Data={data}".format(url=url,
                                                                                                            statuscode=response.status_code,
                                                                                                            reason=response.reason,
                                                                                                            data=data))

            
            return ApiResults(error_code=response.status_code,error_message=response.reason)
    else:
        logger.fatal("Unable to obtain access token for put request to {0}".format(url))
        return ApiResults(error_code=4000,error_message="Unable to obtain access token")
        

def delete(path, max_retry=3):
    url = __full_url__(path)
    token = ApiAccessToken().get_access_token(session=get_request_session())
    if token:
        headers = __get_auth_header__(token.get('access_token',None))
        response = requests.delete(url,headers=headers, auth=None)
        if response.ok:
            return ApiResults(ok=response.ok)
        else:
            #in case http 401 we should refresh access token
            if max_retry and response.status_code==401:
                ApiAccessToken().get_access_token(session=get_request_session())
                return delete(path, max_retry=max_retry-1)
            else:
                logger.error("api.delete:= Unable to delete data at {url}. Received http {statuscode}: {reason}".format(url=url,
                                                                                                            statuscode=response.status_code,
                                                                                                            reason=response.reason))


def __full_url__(relative_url):
    return '{0}{1}'.format(BASE_URL,relative_url)


def __get_auth_header__(access_token=None,token_type='Bearer'):
        return {"Authorization":"{token_type} {token}".format(token_type=token_type, token=access_token)}