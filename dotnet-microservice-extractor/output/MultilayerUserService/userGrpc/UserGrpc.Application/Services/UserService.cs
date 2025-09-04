using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using userGrpc.Application.DTOs;
using userGrpc.Application.Interfaces;
using userGrpc.Domain.Entities;
using userGrpc.Domain.Repositories;

namespace userGrpc.Application.Services
{
    /// <summary>
    /// Implementation of the User service.
    /// </summary>
    public class UserService : IUserService
    {
        private readonly IUserRepository _userRepository;
        private readonly ILogger<UserService> _logger;

        /// <summary>
        /// Initializes a new instance of the <see cref="UserService"/> class.
        /// </summary>
        /// <param name="userRepository">The user repository.</param>
        /// <param name="logger">The logger instance.</param>
        public UserService(IUserRepository userRepository, ILogger<UserService> logger)
        {
            _userRepository = userRepository;
            _logger = logger;
        }

        /// <inheritdoc/>
        public async Task<UserDto?> GetUserAsync(int id)
        {
            var user = await _userRepository.GetByIdAsync(id);
            return user != null ? MapToDto(user) : null;
        }

        /// <inheritdoc/>
        public async Task<IEnumerable<UserDto>> GetAllUsersAsync()
        {
            var users = await _userRepository.GetAllAsync();
            return users.Select(MapToDto);
        }

        /// <inheritdoc/>
        public async Task AddUserAsync(UserDto userDto)
        {
            var user = MapToEntity(userDto);
            await _userRepository.AddAsync(user);
        }

        /// <inheritdoc/>
        public async Task UpdateUserAsync(UserDto userDto)
        {
            var user = MapToEntity(userDto);
            user.Id = userDto.Id;
            await _userRepository.UpdateAsync(user);
        }

        /// <inheritdoc/>
        public async Task DeleteUserAsync(int id)
        {
            await _userRepository.DeleteAsync(id);
        }

        private UserDto MapToDto(User user)
        {
            return new UserDto
            {
                Id = user.Id,
                FirstName = user.FirstName,
                LastName = user.LastName,
                Username = user.Username,
                Password = user.Password,
                EnrollmentDate = user.EnrollmentDate
            };
        }

        private User MapToEntity(UserDto dto)
        {
            return new User
            {
                FirstName = dto.FirstName,
                LastName = dto.LastName,
                Username = dto.Username,
                Password = dto.Password,
                EnrollmentDate = dto.EnrollmentDate
            };
        }
    }
}