using MySqlConnector;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using userGrpc.Domain.Entities;

namespace userGrpc.Infrastructure.Data
{
    /// <summary>
    /// ADO.NET data access class for User entity, providing asynchronous CRUD operations.
    /// </summary>
    public class UserDataAccess
    {
        private readonly string _connectionString;

        public UserDataAccess(string connectionString)
        {
            if (string.IsNullOrEmpty(connectionString))
                throw new ArgumentException("Connection string cannot be null or empty.", nameof(connectionString));
            _connectionString = connectionString;
        }

        public async Task<User?> GetByIdAsync(int id)
        {
            using var conn = new MySqlConnection(_connectionString);
            await conn.OpenAsync();
            using var cmd = new MySqlCommand("SELECT id, first_name, last_name, username, password, enrollment_date FROM users WHERE id = @Id", conn);
            cmd.Parameters.AddWithValue("@Id", id);
            using var reader = await cmd.ExecuteReaderAsync();
            if (await reader.ReadAsync())
            {
                return new User
                {
                    Id = reader.GetInt32("id"),
                    FirstName = reader.GetString("first_name"),
                    LastName = reader.GetString("last_name"),
                    Username = reader.GetString("username"),
                    Password = reader.GetString("password"),
                    EnrollmentDate = reader.GetDateTime("enrollment_date")
                };
            }
            return null;
        }

        public async Task<List<User>> GetAllAsync()
        {
            var users = new List<User>();
            using var conn = new MySqlConnection(_connectionString);
            await conn.OpenAsync();
            using var cmd = new MySqlCommand("SELECT id, first_name, last_name, username, password, enrollment_date FROM users", conn);
            using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                users.Add(new User
                {
                    Id = reader.GetInt32("id"),
                    FirstName = reader.GetString("first_name"),
                    LastName = reader.GetString("last_name"),
                    Username = reader.GetString("username"),
                    Password = reader.GetString("password"),
                    EnrollmentDate = reader.GetDateTime("enrollment_date")
                });
            }
            return users;
        }

        public async Task<int> AddAsync(User user)
        {
            using var conn = new MySqlConnection(_connectionString);
            await conn.OpenAsync();
            using var cmd = new MySqlCommand("INSERT INTO users (first_name, last_name, username, password, enrollment_date) VALUES (@FirstName, @LastName, @Username, @Password, @EnrollmentDate); SELECT LAST_INSERT_ID();", conn);
            cmd.Parameters.AddWithValue("@FirstName", user.FirstName);
            cmd.Parameters.AddWithValue("@LastName", user.LastName);
            cmd.Parameters.AddWithValue("@Username", user.Username);
            cmd.Parameters.AddWithValue("@Password", user.Password);
            cmd.Parameters.AddWithValue("@EnrollmentDate", user.EnrollmentDate);
            return Convert.ToInt32(await cmd.ExecuteScalarAsync());
        }

        public async Task UpdateAsync(User user)
        {
            using var conn = new MySqlConnection(_connectionString);
            await conn.OpenAsync();
            using var cmd = new MySqlCommand("UPDATE users SET first_name = @FirstName, last_name = @LastName, username = @Username, password = @Password, enrollment_date = @EnrollmentDate WHERE id = @Id", conn);
            cmd.Parameters.AddWithValue("@Id", user.Id);
            cmd.Parameters.AddWithValue("@FirstName", user.FirstName);
            cmd.Parameters.AddWithValue("@LastName", user.LastName);
            cmd.Parameters.AddWithValue("@Username", user.Username);
            cmd.Parameters.AddWithValue("@Password", user.Password);
            cmd.Parameters.AddWithValue("@EnrollmentDate", user.EnrollmentDate);
            await cmd.ExecuteNonQueryAsync();
        }

        public async Task DeleteAsync(int id)
        {
            using var conn = new MySqlConnection(_connectionString);
            await conn.OpenAsync();
            using var cmd = new MySqlCommand("DELETE FROM users WHERE id = @Id", conn);
            cmd.Parameters.AddWithValue("@Id", id);
            await cmd.ExecuteNonQueryAsync();
        }
    }
}