from unittest.mock import patch, Mock

from nitric.sdk.v1 import UserClient


def test_create_user():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()

    with patch(
        "nitric.sdk.v1.UserClient._get_method_function", mock_grpc_method_getter
    ):
        client = UserClient()
        client.create_user("test", "test", "test@test.com", "test")

        # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Create")

    # Ensure the create user method is called with the expected input
    mock_create.assert_called_once()
    assert mock_create.call_args.args[0].id == "test"
    assert mock_create.call_args.args[0].tenant == "test"
    assert mock_create.call_args.args[0].email == "test@test.com"
    assert mock_create.call_args.args[0].password == "test"
