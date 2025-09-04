using System.Collections.Generic;
using System.Threading.Tasks;
using OrderGrpc.Application.DTOs;

namespace OrderGrpc.Application.Interfaces
{
    /// <summary>
    /// Interface for Order service providing business logic operations.
    /// </summary>
    public interface IOrderService
    {
        /// <summary>
        /// Asynchronously gets an order by its ID.
        /// </summary>
        /// <param name="id">The ID of the order.</param>
        /// <returns>A task representing the asynchronous operation, with a result of the order DTO if found, otherwise null.</returns>
        Task<OrderDto?> GetOrderAsync(int id);

        /// <summary>
        /// Asynchronously gets all orders.
        /// </summary>
        /// <returns>A task representing the asynchronous operation, with a result of a collection of order DTOs.</returns>
        Task<IEnumerable<OrderDto>> GetAllOrdersAsync();

        /// <summary>
        /// Asynchronously adds a new order.
        /// </summary>
        /// <param name="orderDto">The order DTO to add.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task AddOrderAsync(OrderDto orderDto);

        /// <summary>
        /// Asynchronously updates an existing order.
        /// </summary>
        /// <param name="orderDto">The order DTO to update.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task UpdateOrderAsync(OrderDto orderDto);

        /// <summary>
        /// Asynchronously deletes an order by its ID.
        /// </summary>
        /// <param name="id">The ID of the order to delete.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task DeleteOrderAsync(int id);
    }
}