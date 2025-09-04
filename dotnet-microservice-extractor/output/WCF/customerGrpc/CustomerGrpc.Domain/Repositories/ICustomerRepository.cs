using System.Collections.Generic;
using System.Threading.Tasks;
using CustomerGrpc.Domain.Entities;

namespace CustomerGrpc.Domain.Repositories
{
    /// <summary>
    /// Defines the contract for customer data access operations.
    /// </summary>
    public interface ICustomerRepository
    {
        /// <summary>
        /// Retrieves a customer by its unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the customer.</param>
        /// <returns>A task representing the asynchronous operation, with a nullable customer entity as the result.</returns>
        Task<Customer?> GetByIdAsync(int id);

        /// <summary>
        /// Retrieves all customers.
        /// </summary>
        /// <returns>A task representing the asynchronous operation, with a list of customer entities as the result.</returns>
        Task<IEnumerable<Customer>> GetAllAsync();

        /// <summary>
        /// Adds a new customer.
        /// </summary>
        /// <param name="customer">The customer entity to add.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task AddAsync(Customer customer);

        /// <summary>
        /// Updates an existing customer.
        /// </summary>
        /// <param name="customer">The customer entity to update.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task UpdateAsync(Customer customer);

        /// <summary>
        /// Deletes a customer by its unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the customer to delete.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task DeleteAsync(int id);
    }
}