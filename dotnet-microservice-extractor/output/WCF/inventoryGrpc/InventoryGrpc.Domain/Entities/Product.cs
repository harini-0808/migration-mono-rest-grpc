using System.ComponentModel.DataAnnotations;

namespace InventoryGrpc.Domain.Entities
{
    /// <summary>
    /// Represents a product in the inventory.
    /// </summary>
    public class Product
    {
        /// <summary>
        /// Gets or sets the unique identifier for the product.
        /// </summary>
        [Key]
        public int Id { get; set; }

        /// <summary>
        /// Gets or sets the name of the product.
        /// </summary>
        [Required]
        [StringLength(100)]
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the stock quantity of the product.
        /// </summary>
        [Range(0, int.MaxValue)]
        public int StockQuantity { get; set; }

        /// <summary>
        /// Gets or sets the price of the product.
        /// </summary>
        [Range(0.0, double.MaxValue)]
        public decimal Price { get; set; }
    }
}