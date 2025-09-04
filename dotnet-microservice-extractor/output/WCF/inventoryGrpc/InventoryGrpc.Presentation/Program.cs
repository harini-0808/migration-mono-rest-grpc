using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using AutoMapper;
using InventoryGrpc.Domain.Repositories;
using InventoryGrpc.Domain.Entities;
using InventoryGrpc.Application.Interfaces;
using InventoryGrpc.Application.Services;
using InventoryGrpc.Application.DTOs;
using InventoryGrpc.Infrastructure.Data;
using InventoryGrpc.Infrastructure.Repositories;
using InventoryGrpc.Presentation.Services;

namespace InventoryGrpc.Presentation
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
            builder.Services.AddScoped<IProductRepository, ProductRepository>();
            builder.Services.AddScoped<IProductService, ProductService>();
            builder.Services.AddScoped<ProductDataAccess>(sp => new ProductDataAccess(connectionString));

            var mapperConfig = new MapperConfiguration(cfg =>
            {
                cfg.CreateMap<ProductDto, Product>().ReverseMap();
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

            app.MapGrpcService<ProductGrpcService>();
            app.MapGet("/", () => "Communication with gRPC endpoints must be made through a gRPC client.");

            app.Run();
        }
    }
}