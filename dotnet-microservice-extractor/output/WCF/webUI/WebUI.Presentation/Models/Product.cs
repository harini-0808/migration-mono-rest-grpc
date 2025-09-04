using System.ComponentModel.DataAnnotations;

namespace WebUI.Presentation.Models
{
    /// <summary>
    /// Represents a product entity.
    /// </summary>
    public class Product
    {
        /// <summary>
        /// Gets or sets the product ID.
        /// </summary>
        [Required]
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
        [Required]
        [Range(0, int.MaxValue)]
        public int StockQuantity { get; set; }

        /// <summary>
        /// Gets or sets the price of the product.
        /// </summary>
        [Required]
        [Range(0.0, double.MaxValue)]
        public decimal Price { get; set; }
    }
}