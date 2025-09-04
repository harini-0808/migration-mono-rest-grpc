using System.Collections.Generic;
using System.Threading.Tasks;
using UserGrpc.Domain.Entities;

namespace UserGrpc.Domain.Repositories
{
    /// <summary>
    /// Interface for User repository, providing data access methods for User entities.
    /// </summary>
    public interface IUserRepository
    {
        /// <summary>
        /// Gets a user by their unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the user.</param>
        /// <returns>A task representing the asynchronous operation, with a result of the user if found, otherwise null.</returns>
        Task<User?> GetByIdAsync(int id);

        /// <summary>
        /// Gets all users.
        /// </summary>
        /// <returns>A task representing the asynchronous operation, with a result of a list of users.</returns>
        Task<IEnumerable<User>> GetAllAsync();

        /// <summary>
        /// Adds a new user.
        /// </summary>
        /// <param name="user">The user to add.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task AddAsync(User user);

        /// <summary>
        /// Updates an existing user.
        /// </summary>
        /// <param name="user">The user to update.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task UpdateAsync(User user);

        /// <summary>
        /// Deletes a user by their unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the user to delete.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task DeleteAsync(int id);
    }
}