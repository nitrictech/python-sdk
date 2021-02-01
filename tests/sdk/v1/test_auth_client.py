from unittest.mock import patch, Mock

from google.protobuf.struct_pb2 import Struct

from nitric.sdk.v1 import AuthClient
from nitric.proto.v1.auth_pb2 import CreateUserResponse

def test_create_user():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()

    with patch(
            "nitric.sdk.v1.AuthClient._get_method_function", mock_grpc_method_getter
    ):
        client = AuthClient()
        client.create_user("test", "test", "test@test.com", "test")

        # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("CreateUser")

    # Ensure the create user method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args.args[0].id == "test"
    assert mock_create.call_args.args[0].tenant == "test"
    assert mock_create.call_args.args[0].email == "test@test.com"
    assert mock_create.call_args.args[0].password == "test"