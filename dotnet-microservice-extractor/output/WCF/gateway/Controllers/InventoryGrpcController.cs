using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;
using Gateway.Presentation.Protos;

namespace Gateway.Controllers
{
    [ApiController]
    [Route("api/inventory")]
    public class InventoryGrpcController : ControllerBase
    {
        private readonly InventoryService.InventoryServiceClient _inventoryGrpcClient;

        public InventoryGrpcController(InventoryService.InventoryServiceClient inventoryGrpcClient)
        {
            _inventoryGrpcClient = inventoryGrpcClient;
        }

        [HttpGet("get")]
        public async Task<IActionResult> GetProductAsync(int id)
        {
            var request = new ProductRequest { Id = id };
            var response = await _inventoryGrpcClient.GetProductAsync(request);
            return Ok(response);
        }

        [HttpPut("update-stock")]
        public async Task<IActionResult> UpdateStockAsync(int productId, int quantity)
        {
            var request = new UpdateStockRequest { ProductId = productId, Quantity = quantity };
            var response = await _inventoryGrpcClient.UpdateStockAsync(request);
            return Ok(response);
        }
    }
}