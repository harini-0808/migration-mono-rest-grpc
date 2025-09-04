using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;
using webUI.Presentation.Protos;

namespace WebUI.Presentation.Controllers
{
    [ApiController]
    [Route("api/order")]
    public class OrderGrpcController : ControllerBase
    {
        private readonly OrderService.OrderServiceClient _orderGrpcClient;

        public OrderGrpcController(OrderService.OrderServiceClient orderGrpcClient)
        {
            _orderGrpcClient = orderGrpcClient;
        }

        [HttpGet("get")]
        public async Task<IActionResult> GetOrderAsync(int id)
        {
            var request = new OrderRequest { Id = id };
            var response = await _orderGrpcClient.GetOrderAsync(request);
            return Ok(response);
        }

        [HttpPost("place")]
        public async Task<IActionResult> PlaceOrderAsync([FromBody] OrderCreateRequest request)
        {
            var response = await _orderGrpcClient.PlaceOrderAsync(request);
            return Ok(response);
        }
    }
}