using Grpc.Core;
using Microsoft.Extensions.Logging;
using System.Linq;
using System.Threading.Tasks;
using userGrpc.Application.Interfaces;
using userGrpc.Application.DTOs;
using userGrpc.Presentation.Protos;

namespace userGrpc.Presentation.Services
{
    /// <summary>
    /// gRPC service implementation for User
    /// </summary>
    public class UserGrpcService : UserService.UserServiceBase
    {
        private readonly IUserService _userService;
        private readonly ILogger<UserGrpcService> _logger;

        public UserGrpcService(IUserService userService, ILogger<UserGrpcService> logger)
        {
            _userService = userService;
            _logger = logger;
        }

        public override async Task<UserResponse> GetUser(UserRequest request, ServerCallContext context)
        {
            if (request.Id <= 0)
            {
                _logger.LogWarning("Invalid ID: {Id}", request.Id);
                throw new RpcException(new Status(StatusCode.InvalidArgument, "Invalid ID"));
            }

            try
            {
                var userDto = await _userService.GetUserByIdAsync(request.Id);
                if (userDto == null)
                {
                    throw new RpcException(new Status(StatusCode.NotFound, "User not found"));
                }

                return new UserResponse
                {
                    Id = userDto.Id,
                    FirstName = userDto.FirstName,
                    LastName = userDto.LastName,
                    Username = userDto.Username,
                    Password = userDto.Password,
                    EnrollmentDate = userDto.EnrollmentDate.ToTimestamp()
                };
            }
            catch (RpcException)
            {
                throw;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error in GetUser");
                throw new RpcException(new Status(StatusCode.Unknown, "Unexpected error"));
            }
        }

        public override async Task<UserListResponse> GetAllUsers(Empty request, ServerCallContext context)
        {
            try
            {
                var users = await _userService.GetAllUsersAsync();
                var response = new UserListResponse();
                response.Users.AddRange(users.Select(userDto => new UserResponse
                {
                    Id = userDto.Id,
                    FirstName = userDto.FirstName,
                    LastName = userDto.LastName,
                    Username = userDto.Username,
                    Password = userDto.Password,
                    EnrollmentDate = userDto.EnrollmentDate.ToTimestamp()
                }));
                return response;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error in GetAllUsers");
                throw new RpcException(new Status(StatusCode.Unknown, "Unexpected error"));
            }
        }

        public override async Task<UserResponse> CreateUser(UserCreateRequest request, ServerCallContext context)
        {
            try
            {
                var userDto = new UserDto
                {
                    FirstName = request.FirstName,
                    LastName = request.LastName,
                    Username = request.Username,
                    Password = request.Password,
                    EnrollmentDate = request.EnrollmentDate.ToDateTime()
                };

                var createdUser = await _userService.CreateUserAsync(userDto);
                return new UserResponse
                {
                    Id = createdUser.Id,
                    FirstName = createdUser.FirstName,
                    LastName = createdUser.LastName,
                    Username = createdUser.Username,
                    Password = createdUser.Password,
                    EnrollmentDate = createdUser.EnrollmentDate.ToTimestamp()
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error in CreateUser");
                throw new RpcException(new Status(StatusCode.Unknown, "Unexpected error"));
            }
        }

        public override async Task<UserResponse> UpdateUser(UserUpdateRequest request, ServerCallContext context)
        {
            if (request.Id <= 0)
            {
                _logger.LogWarning("Invalid ID: {Id}", request.Id);
                throw new RpcException(new Status(StatusCode.InvalidArgument, "Invalid ID"));
            }

            try
            {
                var userDto = new UserDto
                {
                    Id = request.Id,
                    FirstName = request.FirstName,
                    LastName = request.LastName,
                    Username = request.Username,
                    Password = request.Password,
                    EnrollmentDate = request.EnrollmentDate.ToDateTime()
                };

                var updatedUser = await _userService.UpdateUserAsync(userDto);
                return new UserResponse
                {
                    Id = updatedUser.Id,
                    FirstName = updatedUser.FirstName,
                    LastName = updatedUser.LastName,
                    Username = updatedUser.Username,
                    Password = updatedUser.Password,
                    EnrollmentDate = updatedUser.EnrollmentDate.ToTimestamp()
                };
            }
            catch (RpcException)
            {
                throw;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error in UpdateUser");
                throw new RpcException(new Status(StatusCode.Unknown, "Unexpected error"));
            }
        }

        public override async Task<UserResponse> DeleteUser(UserRequest request, ServerCallContext context)
        {
            if (request.Id <= 0)
            {
                _logger.LogWarning("Invalid ID: {Id}", request.Id);
                throw new RpcException(new Status(StatusCode.InvalidArgument, "Invalid ID"));
            }

            try
            {
                var deletedUser = await _userService.DeleteUserAsync(request.Id);
                if (deletedUser == null)
                {
                    throw new RpcException(new Status(StatusCode.NotFound, "User not found"));
                }

                return new UserResponse
                {
                    Id = deletedUser.Id,
                    FirstName = deletedUser.FirstName,
                    LastName = deletedUser.LastName,
                    Username = deletedUser.Username,
                    Password = deletedUser.Password,
                    EnrollmentDate = deletedUser.EnrollmentDate.ToTimestamp()
                };
            }
            catch (RpcException)
            {
                throw;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error in DeleteUser");
                throw new RpcException(new Status(StatusCode.Unknown, "Unexpected error"));
            }
        }
    }
}