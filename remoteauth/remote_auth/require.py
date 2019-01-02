from . import api
def in_any_of_the_roles(roles:[]):
    def user_test(user):
        request = api.get_request()
        user_profile = request.session.get('user_profile')
        if user_profile and user_profile.get('roles', None):
            roles_set = set([r.lower() for r in roles])
            return not roles_set.isdisjoint([r.lower() for r in user_profile.get('roles')])
        elif not roles:
            return True
        
        return False

    #Return user test function 
    return user_test