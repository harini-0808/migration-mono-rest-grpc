using AutoMapper;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using OrderGrpc.Application.DTOs;
using OrderGrpc.Application.Interfaces;
using OrderGrpc.Application.Services;
using OrderGrpc.Domain.Entities;
using OrderGrpc.Domain.Repositories;
using OrderGrpc.Infrastructure.Data;
using OrderGrpc.Infrastructure.Repositories;
using OrderGrpc.Presentation.Services;

namespace OrderGrpc.Presentation
{
    public class Program
    {
        public static void Main(string[] args)
        {
            var builder = WebApplication.CreateBuilder(args);

            var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
            if (string.IsNullOrEmpty(connectionString))
            {
                throw new Exception("Connection string 'DefaultConnection' not found.");
            }

            builder.Services.AddGrpc();
            builder.Services.AddScoped<IOrderRepository, OrderRepository>();
            builder.Services.AddScoped<IOrderService, OrderService>();
            builder.Services.AddScoped<OrderDataAccess>(sp => new OrderDataAccess(connectionString));

            var mapperConfig = new MapperConfiguration(cfg =>
            {
                cfg.CreateMap<OrderDto, Order>().ReverseMap();
            });
            builder.Services.AddSingleton(mapperConfig.CreateMapper());

            builder.Services.AddLogging(logging =>
            {
                logging.AddConsole();
                logging.SetMinimumLevel(LogLevel.Debug);
            });

            builder.WebHost.ConfigureKestrel(options =>
            {
                options.ListenLocalhost(5001, listenOptions =>
                {
                    listenOptions.Protocols = HttpProtocols.Http2;
                });
            });

            var app = builder.Build();

            app.MapGrpcService<OrderGrpcService>();
            app.MapGet("/", () => "Communication with gRPC endpoints must be made through a gRPC client.");

            app.Run();
        }
    }
}