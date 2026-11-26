"""Async gRPC client for UserService."""
import grpc

from api_gateway import config
from user_service.generated import user_pb2, user_pb2_grpc


class UserGRPCClient:
    """Long-lived async channel to User Service."""

    def __init__(self):
        self._channel: grpc.aio.Channel | None = None
        self._stub: user_pb2_grpc.UserServiceStub | None = None

    async def connect(self):
        """Open a persistent async gRPC channel."""
        target = f"{config.USER_SERVICE_GRPC_HOST}:{config.USER_SERVICE_GRPC_PORT}"
        self._channel = grpc.aio.insecure_channel(target)
        self._stub = user_pb2_grpc.UserServiceStub(self._channel)
        print(f"[*] Gateway gRPC client connected to User Service at {target}")

    async def close(self):
        """Close the gRPC channel."""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None

    async def validate_token(self, token: str) -> dict:
        """Validate a JWT via User Service."""
        try:
            response = await self._stub.ValidateToken(
                user_pb2.ValidateTokenRequest(token=token)
            )
            return {
                "valid": response.valid,
                "message": response.message,
                "user_id": response.user_id,
                "email": response.email,
                "role": response.role,
                "full_name": response.full_name,
            }
        except grpc.aio.AioRpcError as e:
            raise RuntimeError(f"Token validation RPC failed: {e.details()}") from e

    async def get_user(self, user_id: str) -> dict | None:
        """Fetch a user profile via gRPC."""
        try:
            response = await self._stub.GetUser(user_pb2.GetUserRequest(user_id=user_id))
            return {
                "user_id": response.user_id,
                "email": response.email,
                "full_name": response.full_name,
                "role": response.role,
                "is_active": response.is_active,
            }
        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            raise


user_client = UserGRPCClient()
