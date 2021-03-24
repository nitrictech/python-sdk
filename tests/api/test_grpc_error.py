import unittest
from unittest.mock import patch, Mock
from nitric.api import EventClient
from nitric.api.exception import *
import grpc
from grpc._channel import _InactiveRpcError, _RPCState


class GRPCErrorCases(unittest.TestCase):
    def test_unavailable(self):
        mock_grpc_method_getter = Mock()
        mock_grpc_method_getter.return_value = mock_publish = Mock()

        # Emulate unavailable error
        state = _RPCState((), (), (), grpc.StatusCode.UNAVAILABLE, "test only")
        mock_publish.side_effect = Mock(side_effect=_InactiveRpcError(state))
        mock_publish._method = b"test.topic/Publish"

        with patch(
            "nitric.api.EventClient._get_method_function", mock_grpc_method_getter
        ):
            client = EventClient()
            self.assertRaises(
                UnavailableException, client.publish, topic_name="t", payload_type="p"
            )

    def test_unimplemented(self):
        mock_grpc_method_getter = Mock()
        mock_grpc_method_getter.return_value = mock_publish = Mock()

        # Emulate unavailable error
        state = _RPCState((), (), (), grpc.StatusCode.UNIMPLEMENTED, "test only")
        mock_publish.side_effect = Mock(side_effect=_InactiveRpcError(state))
        mock_publish._method = b"test.topic/Publish"

        with patch(
            "nitric.api.EventClient._get_method_function", mock_grpc_method_getter
        ):
            client = EventClient()
            self.assertRaises(
                UnimplementedException, client.publish, topic_name="t", payload_type="p"
            )

    def test_already_exists(self):
        mock_grpc_method_getter = Mock()
        mock_grpc_method_getter.return_value = mock_publish = Mock()

        # Emulate unavailable error
        state = _RPCState((), (), (), grpc.StatusCode.ALREADY_EXISTS, "test only")
        mock_publish.side_effect = Mock(side_effect=_InactiveRpcError(state))
        mock_publish._method = b"test.topic/Publish"

        with patch(
            "nitric.api.EventClient._get_method_function", mock_grpc_method_getter
        ):
            client = EventClient()
            self.assertRaises(
                AlreadyExistsException, client.publish, topic_name="t", payload_type="p"
            )

    def test_unexpected_exception(self):
        mock_grpc_method_getter = Mock()
        mock_grpc_method_getter.return_value = mock_publish = Mock()

        # Emulate unavailable error
        mock_publish.side_effect = Mock(side_effect=Exception("other exception"))
        mock_publish._method = b"test.topic/Publish"

        with patch(
            "nitric.api.EventClient._get_method_function", mock_grpc_method_getter
        ):
            client = EventClient()
            # Expect a standard Exception if a non-grpc error is raised.
            self.assertRaises(
                Exception, client.publish, topic_name="t", payload_type="p"
            )
