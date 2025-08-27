from oauth2_provider.oauth2_validators import OAuth2Validator

class CustomOAuth2Validator(OAuth2Validator):
    """
    Add custom claims to JWT tokens
    """
    def get_additional_claims(self, request):
        user = request.user
        return {
            "username": user.username,
            "email": user.email,
            "department": user.department,
            "roles": list(user.roles.values_list("name", flat=True)),
        }
