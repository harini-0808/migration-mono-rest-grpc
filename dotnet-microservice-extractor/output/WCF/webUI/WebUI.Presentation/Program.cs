using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using AutoMapper;
using Unknown.Domain.Repositories;
using Unknown.Application.Interfaces;
using Unknown.Application.Services;
using Unknown.Infrastructure.Data;
using Unknown.Infrastructure.Repositories;
using Unknown.Presentation.Services;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Microsoft.Extensions.Logging;

var builder = WebApplication.CreateBuilder(args);
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
if (string.IsNullOrEmpty(connectionString)) { throw new Exception("Connection string 'DefaultConnection' not found."); }

builder.Services.AddGrpc();
builder.Services.AddScoped<IEntityRepository, EntityRepository>();
builder.Services.AddScoped<IEntityService, EntityService>();
builder.Services.AddScoped<EntityDataAccess>(sp => new EntityDataAccess(connectionString));
var mapperConfig = new MapperConfiguration(cfg => { cfg.CreateMap<EntityDto, Entity>().ReverseMap(); });
builder.Services.AddSingleton(mapperConfig.CreateMapper());
builder.Services.AddLogging(logging => { logging.AddConsole(); logging.SetMinimumLevel(LogLevel.Debug); });

builder.WebHost.ConfigureKestrel(options => { options.ListenLocalhost(5001, listenOptions => { listenOptions.Protocols = HttpProtocols.Http2; }); });

var app = builder.Build();
app.MapGrpcService<EntityGrpcService>();
app.MapGet("/", () => "Communication with gRPC endpoints must be made through a gRPC client.");
app.Run();