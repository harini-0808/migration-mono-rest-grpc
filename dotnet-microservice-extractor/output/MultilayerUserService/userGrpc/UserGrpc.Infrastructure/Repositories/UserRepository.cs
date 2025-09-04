using MySqlConnector;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using userGrpc.Domain.Entities;
using userGrpc.Domain.Repositories;
using userGrpc.Infrastructure.Data;

namespace userGrpc.Infrastructure.Repositories
{
    /// <summary>
    /// Implementation of the User repository using ADO.NET for data access.
    /// </summary>
    public class UserRepository : IUserRepository
    {
        private readonly UserDataAccess _userDataAccess;

        public UserRepository(UserDataAccess userDataAccess)
        {
            _userDataAccess = userDataAccess ?? throw new ArgumentNullException(nameof(userDataAccess));
        }

        public async Task<User?> GetByIdAsync(int id)
        {
            return await _userDataAccess.GetByIdAsync(id);
        }

        public async Task<List<User>> GetAllAsync()
        {
            return await _userDataAccess.GetAllAsync();
        }

        public async Task<int> AddAsync(User user)
        {
            return await _userDataAccess.AddAsync(user);
        }

        public async Task UpdateAsync(User user)
        {
            await _userDataAccess.UpdateAsync(user);
        }

        public async Task DeleteAsync(int id)
        {
            await _userDataAccess.DeleteAsync(id);
        }
    }
}