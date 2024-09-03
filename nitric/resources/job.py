from nitric.resources.resource import SecureResource
from nitric.application import Nitric
from nitric.proto.resources.v1 import (
    Action,
    JobResource,
    ResourceDeclareRequest,
    ResourceIdentifier,
    ResourceType,
)
import logging
import betterproto
from nitric.proto.batch.v1 import (
    BatchStub,
    JobSubmitRequest,
    JobData,
    JobStub,
    RegistrationRequest,
    ClientMessage,
    ServerMessage,
    JobResponse as ProtoJobResponse,
    JobResourceRequirements,
)
from nitric.exception import exception_from_grpc_error
from grpclib import GRPCError
from grpclib.client import Channel
from typing import Callable, Any, Optional, Literal, List
from nitric.context import FunctionServer, Handler
from nitric.channel import ChannelManager
from nitric.bidi import AsyncNotifierList
from nitric.utils import dict_from_struct, struct_from_dict
import grpclib


JobPermission = Literal["submit"]


class JobRequest:
    """Represents a translated Job, from a Job Definition, forwarded from the Nitric Runtime Server."""

    data: dict[str, Any]

    def __init__(self, data: dict[str, Any]):
        """Construct a new JobRequest."""
        self.data = data


class JobResponse:
    """Represents the response to a trigger from a Job submission as a result of a SubmitJob call."""

    def __init__(self, success: bool = True):
        """Construct a new EventResponse."""
        self.success = success


class JobContext:
    """Represents the full request/response context for an Event based trigger."""

    def __init__(self, request: JobRequest, response: Optional[JobResponse] = None):
        """Construct a new EventContext."""
        self.req = request
        self.res = response if response else JobResponse()

    @staticmethod
    def _from_request(msg: ServerMessage) -> "JobContext":
        """Construct a new EventContext from a Topic trigger from the Nitric Membrane."""
        return JobContext(request=JobRequest(data=dict_from_struct(msg.job_request.data.struct)))

    def to_response(self) -> ClientMessage:
        """Construct a EventContext for the Nitric Membrane from this context object."""
        return ClientMessage(job_response=ProtoJobResponse(success=self.res.success))


JobHandle = Handler[JobContext]


class JobHandler(FunctionServer):
    """Function worker for Jobs."""

    _handler: JobHandle
    _registration_request: RegistrationRequest
    _responses: AsyncNotifierList[ClientMessage]

    def __init__(
        self,
        job_name: str,
        handler: JobHandle,
        cpus: float | None = None,
        memory: int | None = None,
        gpus: int | None = None,
    ):
        """Construct a new WebsocketHandler."""
        self._handler = handler
        self._responses = AsyncNotifierList()
        self._registration_request = RegistrationRequest(
            job_name=job_name,
            requirements=JobResourceRequirements(
                cpus=cpus if cpus is not None else 0,
                memory=memory if memory is not None else 0,
                gpus=gpus if gpus is not None else 0,
            ),
        )

    async def _message_request_iterator(self):
        # Register with the server
        yield ClientMessage(registration_request=self._registration_request)
        # wait for any responses for the server and send them
        async for response in self._responses:
            yield response

    async def start(self) -> None:
        """Register this subscriber and listen for messages."""
        channel = ChannelManager.get_channel()
        server = JobStub(channel=channel)

        try:
            async for server_msg in server.handle_job(self._message_request_iterator()):
                msg_type, _ = betterproto.which_one_of(server_msg, "content")

                if msg_type == "registration_response":
                    continue
                if msg_type == "job_request":
                    ctx = JobContext._from_request(server_msg)

                    response: ClientMessage
                    try:
                        resp_ctx = await self._handler(ctx)
                        if resp_ctx is None:
                            resp_ctx = ctx

                        response = ClientMessage(
                            id=server_msg.id,
                            job_response=ProtoJobResponse(success=ctx.res.success),
                        )
                    except Exception as e:  # pylint: disable=broad-except
                        logging.exception("An unhandled error occurred in a subscription event handler: %s", e)
                        response = ClientMessage(id=server_msg.id, job_response=ProtoJobResponse(success=False))
                    await self._responses.add_item(response)
        except grpclib.exceptions.GRPCError as e:
            print(f"Stream terminated: {e.message}")
        except grpclib.exceptions.StreamTerminatedError:
            print("Stream from membrane closed.")
        finally:
            print("Closing client stream")
            channel.close()


class JobRef:
    """A reference to a deployed job, used to interact with the job at runtime."""

    _channel: Channel
    _stub: BatchStub
    name: str

    def __init__(self, name: str) -> None:
        """Construct a reference to a deployed Job."""
        self._channel: Channel = ChannelManager.get_channel()
        self._stub = BatchStub(channel=self._channel)
        self.name = name

    def __del__(self) -> None:
        # close the channel when this client is destroyed
        if self._channel is not None:
            self._channel.close()

    async def submit(self, data: dict[str, Any]) -> None:
        """Submit a new execution for this job definition."""
        await self._stub.submit_job(
            job_submit_request=JobSubmitRequest(job_name=self.name, data=JobData(struct=struct_from_dict(data)))
        )


class Job(SecureResource):
    """A Job Definition."""

    name: str

    def __init__(self, name: str):
        """Job definition constructor."""
        super().__init__(name)
        self.name = name

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    id=_to_resource_identifier(self),
                    job=JobResource(),
                )
            )

        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    def _perms_to_actions(self, *args: JobPermission) -> List[Action]:
        _permMap: dict[JobPermission, List[Action]] = {"submit": [Action.JobSubmit]}

        return [action for perm in args for action in _permMap[perm]]

    def allow(self, perm: JobPermission, *args: JobPermission) -> JobRef:
        """Request the specified permissions to this resource."""
        str_args = [perm] + [str(permission) for permission in args]
        self._register_policy(*str_args)

        return JobRef(self.name)

    def _to_resource_id(self) -> ResourceIdentifier:
        return ResourceIdentifier(name=self.name, type=ResourceType.Job)

    def __call__(
        self, cpus: Optional[float] = None, memory: Optional[int] = None, gpus: Optional[int] = None
    ) -> Callable[[JobHandle], None]:
        """Define the handler for this job definition."""

        def decorator(function: JobHandle) -> None:
            wrkr = JobHandler(self.name, function, cpus, memory, gpus)
            Nitric._register_worker(wrkr)

        return decorator


def _to_resource_identifier(b: Job) -> ResourceIdentifier:
    return ResourceIdentifier(name=b.name, type=ResourceType.Job)


def job(name: str) -> Job:
    """
    Create and register a job.

    If a job has already been registered with the same name, the original reference will be reused.
    """
    # type ignored because the create call are treated as protected.
    return Nitric._create_resource(Job, name)  # type: ignore pylint: disable=protected-access
