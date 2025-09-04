using System.Collections.Generic;
using System.Threading.Tasks;
using InventoryGrpc.Domain.Entities;

namespace InventoryGrpc.Domain.Repositories
{
    /// <summary>
    /// Interface for Inventory repository to handle data access operations.
    /// </summary>
    public interface IInventoryRepository
    {
        /// <summary>
        /// Gets an inventory item by its identifier.
        /// </summary>
        /// <param name="id">The identifier of the inventory item.</param>
        /// <returns>A task representing the asynchronous operation, with a nullable inventory item as the result.</returns>
        Task<Product?> GetByIdAsync(int id);

        /// <summary>
        /// Gets all inventory items.
        /// </summary>
        /// <returns>A task representing the asynchronous operation, with a collection of inventory items as the result.</returns>
        Task<IEnumerable<Product>> GetAllAsync();

        /// <summary>
        /// Adds a new inventory item.
        /// </summary>
        /// <param name="product">The inventory item to add.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task AddAsync(Product product);

        /// <summary>
        /// Updates an existing inventory item.
        /// </summary>
        /// <param name="product">The inventory item to update.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task UpdateAsync(Product product);

        /// <summary>
        /// Deletes an inventory item by its identifier.
        /// </summary>
        /// <param name="id">The identifier of the inventory item to delete.</param>
        /// <returns>A task representing the asynchronous operation.</returns>
        Task DeleteAsync(int id);
    }
}