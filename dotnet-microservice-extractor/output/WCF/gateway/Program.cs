using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using AutoMapper;
using Gateway.Domain.Repositories;
using Gateway.Application.Interfaces;
using Gateway.Application.Services;
using Gateway.Infrastructure.Data;
using Gateway.Infrastructure.Repositories;
using Gateway.Presentation.Services;
using Microsoft.AspNetCore.Server.Kestrel.Core;

var builder = WebApplication.CreateBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
if (string.IsNullOrEmpty(connectionString))
{
    throw new Exception("Connection string 'DefaultConnection' not found.");
}

builder.Services.AddGrpc();
builder.Services.AddScoped<IUnknownRepository, UnknownRepository>();
builder.Services.AddScoped<IUnknownService, UnknownService>();
builder.Services.AddScoped<UnknownDataAccess>(sp => new UnknownDataAccess(connectionString));

var mapperConfig = new MapperConfiguration(cfg =>
{
    cfg.CreateMap<UnknownDto, Unknown>().ReverseMap();
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

app.MapGrpcService<UnknownGrpcService>();
app.MapGet("/", () => "Communication with gRPC endpoints must be made through a gRPC client.");

app.Run();