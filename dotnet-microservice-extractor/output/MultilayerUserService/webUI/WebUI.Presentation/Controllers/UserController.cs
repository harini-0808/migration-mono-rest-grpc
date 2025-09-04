using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;
using webUI.Presentation.Protos;

namespace webUI.Presentation.Controllers
{
    [ApiController]
    [Route("api/user")]
    public class UserGrpcController : ControllerBase
    {
        private readonly UserService.UserServiceClient _userGrpcClient;

        public UserGrpcController(UserService.UserServiceClient userGrpcClient)
        {
            _userGrpcClient = userGrpcClient;
        }

        [HttpGet("get")]
        public async Task<IActionResult> GetUserAsync(int id)
        {
            var request = new UserRequest { Id = id };
            var response = await _userGrpcClient.GetUserAsync(request);
            return Ok(response);
        }

        [HttpGet("getall")]
        public async Task<IActionResult> GetAllUsersAsync()
        {
            var response = await _userGrpcClient.GetAllUsersAsync(new GetAllUsersRequest());
            return Ok(response);
        }

        [HttpPost("create")]
        public async Task<IActionResult> CreateUserAsync([FromBody] UserCreateRequest request)
        {
            var response = await _userGrpcClient.CreateUserAsync(request);
            return Ok(response);
        }

        [HttpPut("update")]
        public async Task<IActionResult> UpdateUserAsync([FromBody] UserUpdateRequest request)
        {
            var response = await _userGrpcClient.UpdateUserAsync(request);
            return Ok(response);
        }

        [HttpDelete("delete")]
        public async Task<IActionResult> DeleteUserAsync(int id)
        {
            var request = new UserDeleteRequest { Id = id };
            var response = await _userGrpcClient.DeleteUserAsync(request);
            return Ok(response);
        }
    }
}