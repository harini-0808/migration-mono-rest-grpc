using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using InventoryGrpc.Application.DTOs;
using InventoryGrpc.Application.Interfaces;
using InventoryGrpc.Domain.Entities;
using InventoryGrpc.Domain.Repositories;
using Microsoft.Extensions.Logging;

namespace InventoryGrpc.Application.Services
{
    /// <summary>
    /// Implementation of the Inventory service.
    /// </summary>
    public class InventoryService : IInventoryService
    {
        private readonly IProductRepository _productRepository;
        private readonly ILogger<InventoryService> _logger;

        /// <summary>
        /// Initializes a new instance of the <see cref="InventoryService"/> class.
        /// </summary>
        /// <param name="productRepository">The product repository.</param>
        /// <param name="logger">The logger.</param>
        public InventoryService(IProductRepository productRepository, ILogger<InventoryService> logger)
        {
            _productRepository = productRepository;
            _logger = logger;
        }

        /// <inheritdoc/>
        public async Task<ProductDto?> GetProductAsync(int id)
        {
            var product = await _productRepository.GetByIdAsync(id);
            return product != null ? MapToDto(product) : null;
        }

        /// <inheritdoc/>
        public async Task<IEnumerable<ProductDto>> GetAllProductsAsync()
        {
            var products = await _productRepository.GetAllAsync();
            return products.Select(MapToDto);
        }

        /// <inheritdoc/>
        public async Task AddProductAsync(ProductDto productDto)
        {
            var product = MapToEntity(productDto);
            await _productRepository.AddAsync(product);
        }

        /// <inheritdoc/>
        public async Task UpdateProductAsync(ProductDto productDto)
        {
            var product = MapToEntity(productDto);
            await _productRepository.UpdateAsync(product);
        }

        /// <inheritdoc/>
        public async Task DeleteProductAsync(int id)
        {
            await _productRepository.DeleteAsync(id);
        }

        private ProductDto MapToDto(Product product)
        {
            return new ProductDto
            {
                Id = product.Id,
                Name = product.Name,
                StockQuantity = product.StockQuantity,
                Price = product.Price
            };
        }

        private Product MapToEntity(ProductDto productDto)
        {
            return new Product
            {
                Id = productDto.Id,
                Name = productDto.Name,
                StockQuantity = productDto.StockQuantity,
                Price = productDto.Price
            };
        }
    }
}