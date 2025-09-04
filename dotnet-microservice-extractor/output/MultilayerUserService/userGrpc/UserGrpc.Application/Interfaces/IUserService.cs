using System.Collections.Generic;
using System.Threading.Tasks;
using userGrpc.Application.DTOs;

namespace userGrpc.Application.Interfaces
{
    /// <summary>
    /// Interface for User service operations.
    /// </summary>
    public interface IUserService
    {
        /// <summary>
        /// Asynchronously retrieves a user by their unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the user.</param>
        /// <returns>A task representing the asynchronous operation, with a nullable UserDto as the result.</returns>
        Task<UserDto?> GetUserAsync(int id);

        /// <summary>
        /// Asynchronously retrieves all users.
        /// </summary>
        /// <returns>A task representing the asynchronous operation, with a list of UserDto as the result.</returns>
        Task<IEnumerable<UserDto>> GetAllUsersAsync();

        /// <summary>
        /// Asynchronously adds a new user.
        /// </summary>
        /// <param name="userDto">The UserDto representing the user to add.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task AddUserAsync(UserDto userDto);

        /// <summary>
        /// Asynchronously updates an existing user.
        /// </summary>
        /// <param name="userDto">The UserDto representing the user to update.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task UpdateUserAsync(UserDto userDto);

        /// <summary>
        /// Asynchronously deletes a user by their unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the user to delete.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task DeleteUserAsync(int id);
    }
}