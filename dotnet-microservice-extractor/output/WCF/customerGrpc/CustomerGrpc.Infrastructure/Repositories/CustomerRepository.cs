using MySqlConnector;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using customerGrpc.Domain.Entities;
using customerGrpc.Domain.Repositories;
using customerGrpc.Infrastructure.Data;

namespace customerGrpc.Infrastructure.Repositories
{
    /// <summary>
    /// Provides repository operations for Customer entity.
    /// </summary>
    public class CustomerRepository : ICustomerRepository
    {
        private readonly CustomerDataAccess _dataAccess;

        /// <summary>
        /// Initializes a new instance of the <see cref="CustomerRepository"/> class.
        /// </summary>
        /// <param name="dataAccess">The data access instance for database operations.</param>
        public CustomerRepository(CustomerDataAccess dataAccess)
        {
            _dataAccess = dataAccess ?? throw new ArgumentNullException(nameof(dataAccess));
        }

        /// <summary>
        /// Retrieves a customer by its unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the customer.</param>
        /// <returns>A task representing the asynchronous operation, with a nullable customer entity as the result.</returns>
        public async Task<Customer?> GetByIdAsync(int id)
        {
            return await _dataAccess.GetByIdAsync(id);
        }

        /// <summary>
        /// Retrieves all customers.
        /// </summary>
        /// <returns>A task representing the asynchronous operation, with a list of customer entities as the result.</returns>
        public async Task<List<Customer>> GetAllAsync()
        {
            return await _dataAccess.GetAllAsync();
        }

        /// <summary>
        /// Adds a new customer.
        /// </summary>
        /// <param name="customer">The customer entity to add.</param>
        /// <returns>A task representing the asynchronous operation, with the new customer ID as the result.</returns>
        public async Task<int> AddAsync(Customer customer)
        {
            return await _dataAccess.AddAsync(customer);
        }

        /// <summary>
        /// Updates an existing customer.
        /// </summary>
        /// <param name="customer">The customer entity to update.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        public async Task UpdateAsync(Customer customer)
        {
            await _dataAccess.UpdateAsync(customer);
        }

        /// <summary>
        /// Deletes a customer by its unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the customer to delete.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        public async Task DeleteAsync(int id)
        {
            await _dataAccess.DeleteAsync(id);
        }
    }
}