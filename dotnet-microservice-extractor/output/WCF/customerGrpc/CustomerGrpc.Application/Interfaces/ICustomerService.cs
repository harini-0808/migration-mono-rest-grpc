using System.Collections.Generic;
using System.Threading.Tasks;
using customerGrpc.Application.DTOs;

namespace customerGrpc.Application.Interfaces
{
    /// <summary>
    /// Interface for Customer service operations.
    /// </summary>
    public interface ICustomerService
    {
        /// <summary>
        /// Retrieves a customer by their unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the customer.</param>
        /// <returns>A task representing the asynchronous operation, with a nullable CustomerDto as the result.</returns>
        Task<CustomerDto?> GetCustomerAsync(int id);

        /// <summary>
        /// Retrieves all customers.
        /// </summary>
        /// <returns>A task representing the asynchronous operation, with a list of CustomerDto as the result.</returns>
        Task<IEnumerable<CustomerDto>> GetAllCustomersAsync();

        /// <summary>
        /// Adds a new customer.
        /// </summary>
        /// <param name="customerDto">The customer data transfer object.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task AddCustomerAsync(CustomerDto customerDto);

        /// <summary>
        /// Updates an existing customer.
        /// </summary>
        /// <param name="customerDto">The customer data transfer object.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task UpdateCustomerAsync(CustomerDto customerDto);

        /// <summary>
        /// Deletes a customer by their unique identifier.
        /// </summary>
        /// <param name="id">The unique identifier of the customer.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task DeleteCustomerAsync(int id);
    }
}