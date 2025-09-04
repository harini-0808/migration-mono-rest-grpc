using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;
using webUI.Presentation.Protos;

namespace WebUI.Presentation.Controllers
{
    [ApiController]
    [Route("api/customer")]
    public class CustomerGrpcController : ControllerBase
    {
        private readonly CustomerService.CustomerServiceClient _customerGrpcClient;

        public CustomerGrpcController(CustomerService.CustomerServiceClient customerGrpcClient)
        {
            _customerGrpcClient = customerGrpcClient;
        }

        [HttpGet("get")]
        public async Task<IActionResult> GetCustomerAsync(int id)
        {
            var request = new CustomerRequest { Id = id };
            var response = await _customerGrpcClient.GetCustomerAsync(request);
            return Ok(response);
        }

        [HttpPost("create")]
        public async Task<IActionResult> CreateCustomerAsync([FromBody] CustomerCreateRequest request)
        {
            var response = await _customerGrpcClient.CreateCustomerAsync(request);
            return Ok(response);
        }
    }
}