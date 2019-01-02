from . import api
def require_role(role:str):
    request = api.get_request()

    def user_test(user):
        user_profile = request.session.get('user_profile')
        if user_profile and user_profile.get('roles', None):
            role = role.lower()
            for r in user_profile.get('roles'):
                if role == r.lower():
                    return True
        elif not role:
            return True
        
        return False

    #Return user test function 
    return user_test