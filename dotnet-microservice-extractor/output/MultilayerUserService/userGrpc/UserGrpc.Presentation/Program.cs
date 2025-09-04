using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using AutoMapper;
using userGrpc.Domain.Repositories;
using userGrpc.Domain.Entities;
using userGrpc.Application.Interfaces;
using userGrpc.Application.Services;
using userGrpc.Application.DTOs;
using userGrpc.Infrastructure.Data;
using userGrpc.Infrastructure.Repositories;
using userGrpc.Presentation.Services;

namespace UserGrpc.Presentation
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
            builder.Services.AddScoped<IUserRepository, UserRepository>();
            builder.Services.AddScoped<IUserService, UserService>();
            builder.Services.AddScoped<UserDataAccess>(sp => new UserDataAccess(connectionString));

            var mapperConfig = new MapperConfiguration(cfg =>
            {
                cfg.CreateMap<UserDto, User>().ReverseMap();
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

            app.MapGrpcService<UserGrpcService>();
            app.MapGet("/", () => "Communication with gRPC endpoints must be made through a gRPC client.");

            app.Run();
        }
    }
}