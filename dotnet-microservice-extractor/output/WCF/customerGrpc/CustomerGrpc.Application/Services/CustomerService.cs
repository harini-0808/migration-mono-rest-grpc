using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using customerGrpc.Application.DTOs;
using customerGrpc.Application.Interfaces;
using customerGrpc.Domain.Entities;
using customerGrpc.Domain.Repositories;

namespace customerGrpc.Application.Services
{
    /// <summary>
    /// Implementation of the Customer service.
    /// </summary>
    public class CustomerService : ICustomerService
    {
        private readonly ICustomerRepository _customerRepository;
        private readonly ILogger<CustomerService> _logger;

        /// <summary>
        /// Initializes a new instance of the <see cref="CustomerService"/> class.
        /// </summary>
        /// <param name="customerRepository">The customer repository.</param>
        /// <param name="logger">The logger.</param>
        public CustomerService(ICustomerRepository customerRepository, ILogger<CustomerService> logger)
        {
            _customerRepository = customerRepository;
            _logger = logger;
        }

        /// <inheritdoc/>
        public async Task<CustomerDto?> GetCustomerAsync(int id)
        {
            var customer = await _customerRepository.GetByIdAsync(id);
            return customer != null ? MapToDto(customer) : null;
        }

        /// <inheritdoc/>
        public async Task<IEnumerable<CustomerDto>> GetAllCustomersAsync()
        {
            var customers = await _customerRepository.GetAllAsync();
            return customers.Select(MapToDto);
        }

        /// <inheritdoc/>
        public async Task AddCustomerAsync(CustomerDto customerDto)
        {
            var customer = MapToEntity(customerDto);
            await _customerRepository.AddAsync(customer);
        }

        /// <inheritdoc/>
        public async Task UpdateCustomerAsync(CustomerDto customerDto)
        {
            var customer = MapToEntity(customerDto);
            await _customerRepository.UpdateAsync(customer);
        }

        /// <inheritdoc/>
        public async Task DeleteCustomerAsync(int id)
        {
            await _customerRepository.DeleteAsync(id);
        }

        private CustomerDto MapToDto(Customer customer)
        {
            return new CustomerDto
            {
                Id = customer.Id,
                Name = customer.Name,
                Email = customer.Email
            };
        }

        private Customer MapToEntity(CustomerDto customerDto)
        {
            return new Customer
            {
                Id = customerDto.Id,
                Name = customerDto.Name,
                Email = customerDto.Email
            };
        }
    }
}