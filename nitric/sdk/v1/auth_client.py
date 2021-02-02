from nitric.proto import auth
from nitric.proto import auth_service
from nitric.sdk.v1._base_client import BaseClient


class AuthClient(BaseClient):
    """
    Nitric Auth client

    This client abstract native authentication and IdP services to provide authentication flows and user management
    """

    def __init__(self):
        """Constructs a new AuthClient"""
        super(self.__class__, self).__init__()
        self._stub = auth_service.AuthStub(self._channel)

    def create_user(self, tenant: str, id: str, email: str, password: str):
        """Creates a new user"""
        request = auth.CreateUserRequest(
            tenant=tenant, id=id, email=email, password=password
        )
        return self._exec("CreateUser", request)
