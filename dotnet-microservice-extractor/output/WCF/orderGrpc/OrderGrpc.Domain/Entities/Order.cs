using System;
using System.ComponentModel.DataAnnotations;

namespace OrderGrpc.Domain.Entities
{
    /// <summary>
    /// Represents an order entity.
    /// </summary>
    public class Order
    {
        /// <summary>
        /// Gets or sets the order identifier.
        /// </summary>
        [Key]
        public int Id { get; set; }

        /// <summary>
        /// Gets or sets the customer identifier.
        /// </summary>
        [Required]
        public int CustomerId { get; set; }

        /// <summary>
        /// Gets or sets the total amount of the order.
        /// </summary>
        [Required]
        [Range(0.01, double.MaxValue, ErrorMessage = "Total amount must be greater than zero.")]
        public decimal TotalAmount { get; set; }

        /// <summary>
        /// Gets or sets the order date.
        /// </summary>
        [Required]
        public DateTime OrderDate { get; set; }
    }
}