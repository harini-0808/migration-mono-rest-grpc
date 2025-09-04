using System.ComponentModel.DataAnnotations;

namespace WebUI.Presentation.Models
{
    /// <summary>
    /// Represents an order entity.
    /// </summary>
    public class Order
    {
        /// <summary>
        /// Gets or sets the order ID.
        /// </summary>
        [Required]
        public int Id { get; set; }

        /// <summary>
        /// Gets or sets the customer ID associated with the order.
        /// </summary>
        [Required]
        public int CustomerId { get; set; }

        /// <summary>
        /// Gets or sets the total amount of the order.
        /// </summary>
        [Required]
        [Range(0.0, double.MaxValue)]
        public decimal TotalAmount { get; set; }

        /// <summary>
        /// Gets or sets the date when the order was placed.
        /// </summary>
        [Required]
        public DateTime OrderDate { get; set; }
    }
}