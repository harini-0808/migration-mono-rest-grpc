using System;

namespace OrderGrpc.Application.DTOs
{
    /// <summary>
    /// Data Transfer Object for Order entity.
    /// </summary>
    public class OrderDto
    {
        /// <summary>
        /// Gets or sets the order ID.
        /// </summary>
        public int Id { get; set; }

        /// <summary>
        /// Gets or sets the customer ID associated with the order.
        /// </summary>
        public int CustomerId { get; set; }

        /// <summary>
        /// Gets or sets the total amount of the order.
        /// </summary>
        public decimal TotalAmount { get; set; }

        /// <summary>
        /// Gets or sets the date when the order was placed.
        /// </summary>
        public DateTime OrderDate { get; set; }
    }
}