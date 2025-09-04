using System.Collections.Generic;
using System.Threading.Tasks;
using OrderGrpc.Domain.Entities;

namespace OrderGrpc.Domain.Repositories
{
    /// <summary>
    /// Defines the contract for the Order repository.
    /// </summary>
    public interface IOrderRepository
    {
        /// <summary>
        /// Retrieves an order by its identifier.
        /// </summary>
        /// <param name="id">The order identifier.</param>
        /// <returns>A task representing the asynchronous operation, with a nullable Order entity as the result.</returns>
        Task<Order?> GetByIdAsync(int id);

        /// <summary>
        /// Retrieves all orders.
        /// </summary>
        /// <returns>A task representing the asynchronous operation, with a collection of Order entities as the result.</returns>
        Task<IEnumerable<Order>> GetAllAsync();

        /// <summary>
        /// Adds a new order.
        /// </summary>
        /// <param name="order">The order to add.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task AddAsync(Order order);

        /// <summary>
        /// Updates an existing order.
        /// </summary>
        /// <param name="order">The order to update.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task UpdateAsync(Order order);

        /// <summary>
        /// Deletes an order by its identifier.
        /// </summary>
        /// <param name="id">The order identifier.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task DeleteAsync(int id);
    }
}