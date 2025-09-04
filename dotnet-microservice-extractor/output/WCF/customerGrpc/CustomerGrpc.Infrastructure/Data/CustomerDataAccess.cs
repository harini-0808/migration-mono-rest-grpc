using MySqlConnector;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using customerGrpc.Domain.Entities;

namespace customerGrpc.Infrastructure.Data
{
    /// <summary>
    /// Provides data access operations for Customer entity using ADO.NET.
    /// </summary>
    public class CustomerDataAccess
    {
        private readonly string _connectionString;

        /// <summary>
        /// Initializes a new instance of the <see cref="CustomerDataAccess"/> class.
        /// </summary>
        /// <param name="connectionString">The connection string for the database.</param>
        /// <exception cref="ArgumentException">Thrown when the connection string is null or empty.</exception>
        public CustomerDataAccess(string connectionString)
        {
            if (string.IsNullOrEmpty(connectionString))
                throw new ArgumentException("Connection string cannot be null or empty.", nameof(connectionString));
            _connectionString = connectionString;
        }

        /// <summary>
        /// Retrieves a customer by its unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the customer.</param>
        /// <returns>A task representing the asynchronous operation, with a nullable customer entity as the result.</returns>
        public async Task<Customer?> GetByIdAsync(int id)
        {
            using var conn = new MySqlConnection(_connectionString);
            await conn.OpenAsync();
            using var cmd = new MySqlCommand("SELECT id, name, email FROM customers WHERE id = @Id", conn);
            cmd.Parameters.AddWithValue("@Id", id);
            using var reader = await cmd.ExecuteReaderAsync();
            if (await reader.ReadAsync())
            {
                return new Customer
                {
                    Id = reader.GetInt32(0),
                    Name = reader.GetString(1),
                    Email = reader.GetString(2)
                };
            }
            return null;
        }

        /// <summary>
        /// Retrieves all customers.
        /// </summary>
        /// <returns>A task representing the asynchronous operation, with a list of customer entities as the result.</returns>
        public async Task<List<Customer>> GetAllAsync()
        {
            var customers = new List<Customer>();
            using var conn = new MySqlConnection(_connectionString);
            await conn.OpenAsync();
            using var cmd = new MySqlCommand("SELECT id, name, email FROM customers", conn);
            using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                customers.Add(new Customer
                {
                    Id = reader.GetInt32(0),
                    Name = reader.GetString(1),
                    Email = reader.GetString(2)
                });
            }
            return customers;
        }

        /// <summary>
        /// Adds a new customer.
        /// </summary>
        /// <param name="customer">The customer entity to add.</param>
        /// <returns>A task representing the asynchronous operation, with the new customer ID as the result.</returns>
        public async Task<int> AddAsync(Customer customer)
        {
            using var conn = new MySqlConnection(_connectionString);
            await conn.OpenAsync();
            using var cmd = new MySqlCommand("INSERT INTO customers (name, email) VALUES (@Name, @Email); SELECT LAST_INSERT_ID();", conn);
            cmd.Parameters.AddWithValue("@Name", customer.Name);
            cmd.Parameters.AddWithValue("@Email", customer.Email);
            return Convert.ToInt32(await cmd.ExecuteScalarAsync());
        }

        /// <summary>
        /// Updates an existing customer.
        /// </summary>
        /// <param name="customer">The customer entity to update.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        public async Task UpdateAsync(Customer customer)
        {
            using var conn = new MySqlConnection(_connectionString);
            await conn.OpenAsync();
            using var cmd = new MySqlCommand("UPDATE customers SET name = @Name, email = @Email WHERE id = @Id", conn);
            cmd.Parameters.AddWithValue("@Id", customer.Id);
            cmd.Parameters.AddWithValue("@Name", customer.Name);
            cmd.Parameters.AddWithValue("@Email", customer.Email);
            await cmd.ExecuteNonQueryAsync();
        }

        /// <summary>
        /// Deletes a customer by its unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the customer to delete.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        public async Task DeleteAsync(int id)
        {
            using var conn = new MySqlConnection(_connectionString);
            await conn.OpenAsync();
            using var cmd = new MySqlCommand("DELETE FROM customers WHERE id = @Id", conn);
            cmd.Parameters.AddWithValue("@Id", id);
            await cmd.ExecuteNonQueryAsync();
        }
    }
}