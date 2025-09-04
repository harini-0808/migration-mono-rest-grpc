using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using AutoMapper;
using customerGrpc.Domain.Repositories;
using customerGrpc.Domain.Entities;
using customerGrpc.Application.Interfaces;
using customerGrpc.Application.Services;
using customerGrpc.Application.DTOs;
using customerGrpc.Infrastructure.Data;
using customerGrpc.Infrastructure.Repositories;
using customerGrpc.Presentation.Services;

var builder = WebApplication.CreateBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
if (string.IsNullOrEmpty(connectionString))
{
    throw new Exception("Connection string 'DefaultConnection' not found.");
}

builder.Services.AddGrpc();
builder.Services.AddScoped<ICustomerRepository, CustomerRepository>();
builder.Services.AddScoped<ICustomerService, CustomerService>();
builder.Services.AddScoped<CustomerDataAccess>(sp => new CustomerDataAccess(connectionString));

var mapperConfig = new MapperConfiguration(cfg =>
{
    cfg.CreateMap<CustomerDto, Customer>().ReverseMap();
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

app.MapGrpcService<CustomerGrpcService>();
app.MapGet("/", () => "Communication with gRPC endpoints must be made through a gRPC client.");

app.Run();