"""gRPC Servicer for the User Service."""
import grpc

from user_service.generated import user_pb2, user_pb2_grpc
from user_service import store
from user_service.security import decode_access_token


class UserServicer(user_pb2_grpc.UserServiceServicer):
    """Implements the UserService gRPC interface."""

    async def ValidateToken(self, request, context):
        """Validate a JWT access token and return the associated user details."""
        if not request.token:
            return user_pb2.ValidateTokenResponse(
                valid=False,
                message="Token is missing",
            )

        claims = decode_access_token(request.token)
        if not claims:
            return user_pb2.ValidateTokenResponse(
                valid=False,
                message="Invalid or expired token",
            )

        user_id = claims.get("sub")
        if not user_id:
            return user_pb2.ValidateTokenResponse(
                valid=False,
                message="Token does not contain a subject",
            )

        user = await store.get_user_by_id(user_id)
        if not user:
            return user_pb2.ValidateTokenResponse(
                valid=False,
                message="User not found in repository",
            )

        if not user.get("is_active", True):
            return user_pb2.ValidateTokenResponse(
                valid=False,
                message="User account is deactivated",
            )

        return user_pb2.ValidateTokenResponse(
            valid=True,
            message="Token is valid",
            user_id=user["user_id"],
            email=user["email"],
            role=user["role"],
            full_name=user["full_name"],
        )

    async def GetUser(self, request, context):
        """Fetch user profile by user_id."""
        user = await store.get_user_by_id(request.user_id)
        if not user:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"User '{request.user_id}' not found",
            )
        return user_pb2.UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            is_active=user["is_active"],
        )
