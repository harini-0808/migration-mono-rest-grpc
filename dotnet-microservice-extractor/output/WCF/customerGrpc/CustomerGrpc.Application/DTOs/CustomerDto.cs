using System;

namespace customerGrpc.Application.DTOs
{
    /// <summary>
    /// Data Transfer Object for Customer entity.
    /// </summary>
    public class CustomerDto
    {
        /// <summary>
        /// Gets or sets the unique identifier of the customer.
        /// </summary>
        public int Id { get; set; }

        /// <summary>
        /// Gets or sets the name of the customer.
        /// </summary>
        public string Name { get; set; }

        /// <summary>
        /// Gets or sets the email of the customer.
        /// </summary>
        public string Email { get; set; }
    }
}