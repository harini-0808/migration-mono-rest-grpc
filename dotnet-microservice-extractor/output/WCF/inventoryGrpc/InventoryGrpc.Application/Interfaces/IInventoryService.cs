using System.Collections.Generic;
using System.Threading.Tasks;
using InventoryGrpc.Application.DTOs;

namespace InventoryGrpc.Application.Interfaces
{
    /// <summary>
    /// Interface for Inventory service operations.
    /// </summary>
    public interface IInventoryService
    {
        /// <summary>
        /// Gets a product by its identifier.
        /// </summary>
        /// <param name="id">The product identifier.</param>
        /// <returns>A task that represents the asynchronous operation. The task result contains the product DTO.</returns>
        Task<ProductDto?> GetProductAsync(int id);

        /// <summary>
        /// Gets all products.
        /// </summary>
        /// <returns>A task that represents the asynchronous operation. The task result contains a list of product DTOs.</returns>
        Task<IEnumerable<ProductDto>> GetAllProductsAsync();

        /// <summary>
        /// Adds a new product.
        /// </summary>
        /// <param name="productDto">The product DTO.</param>
        /// <returns>A task that represents the asynchronous operation.</returns>
        Task AddProductAsync(ProductDto productDto);

        /// <summary>
        /// Updates an existing product.
        /// </summary>
        /// <param name="productDto">The product DTO.</param>
        /// <returns>A task that represents the asynchronous operation.</returns>
        Task UpdateProductAsync(ProductDto productDto);

        /// <summary>
        /// Deletes a product by its identifier.
        /// </summary>
        /// <param name="id">The product identifier.</param>
        /// <returns>A task that represents the asynchronous operation.</returns>
        Task DeleteProductAsync(int id);
    }
}