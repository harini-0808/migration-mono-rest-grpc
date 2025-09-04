using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using AutoMapper;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Gateway.Domain.Repositories;
using Gateway.Domain.Entities;
using Gateway.Application.Interfaces;
using Gateway.Application.Services;
using Gateway.Application.DTOs;
using Gateway.Infrastructure.Data;
using Gateway.Infrastructure.Repositories;
using Gateway.Presentation.Services;

namespace Gateway
{
    /// <summary>
    /// Entry point for the Gateway application.
    /// </summary>
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
            builder.Services.AddScoped<IEntityRepository, EntityRepository>();
            builder.Services.AddScoped<IEntityService, EntityService>();
            builder.Services.AddScoped<EntityDataAccess>(sp => new EntityDataAccess(connectionString));

            var mapperConfig = new MapperConfiguration(cfg =>
            {
                cfg.CreateMap<EntityDto, Entity>().ReverseMap();
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

            app.MapGrpcService<EntityGrpcService>();
            app.MapGet("/", () => "Communication with gRPC endpoints must be made through a gRPC client.");

            app.Run();
        }
    }
}