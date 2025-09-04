using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using OrderGrpc.Application.DTOs;
using OrderGrpc.Application.Interfaces;
using OrderGrpc.Domain.Entities;
using OrderGrpc.Domain.Repositories;

namespace OrderGrpc.Application.Services
{
    /// <summary>
    /// Implementation of the Order service orchestrating business logic.
    /// </summary>
    public class OrderService : IOrderService
    {
        private readonly IOrderRepository _orderRepository;
        private readonly ILogger<OrderService> _logger;

        public OrderService(IOrderRepository orderRepository, ILogger<OrderService> logger)
        {
            _orderRepository = orderRepository;
            _logger = logger;
        }

        public async Task<OrderDto?> GetOrderAsync(int id)
        {
            var order = await _orderRepository.GetByIdAsync(id);
            return order != null ? MapToDto(order) : null;
        }

        public async Task<IEnumerable<OrderDto>> GetAllOrdersAsync()
        {
            var orders = await _orderRepository.GetAllAsync();
            return orders.Select(MapToDto);
        }

        public async Task AddOrderAsync(OrderDto orderDto)
        {
            var order = MapToEntity(orderDto);
            await _orderRepository.AddAsync(order);
        }

        public async Task UpdateOrderAsync(OrderDto orderDto)
        {
            var order = MapToEntity(orderDto);
            await _orderRepository.UpdateAsync(order);
        }

        public async Task DeleteOrderAsync(int id)
        {
            await _orderRepository.DeleteAsync(id);
        }

        private OrderDto MapToDto(Order order)
        {
            return new OrderDto
            {
                Id = order.Id,
                CustomerId = order.CustomerId,
                TotalAmount = order.TotalAmount,
                OrderDate = order.OrderDate
            };
        }

        private Order MapToEntity(OrderDto orderDto)
        {
            return new Order
            {
                Id = orderDto.Id,
                CustomerId = orderDto.CustomerId,
                TotalAmount = orderDto.TotalAmount,
                OrderDate = orderDto.OrderDate
            };
        }
    }
}