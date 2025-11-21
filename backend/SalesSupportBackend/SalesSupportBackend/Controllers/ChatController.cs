
namespace SalesSupportBackend.Controllers
{
	using Microsoft.AspNetCore.Authorization;
	using Microsoft.AspNetCore.Mvc;
	using SalesSupportBackend.Models;
	using System.Net.Http;
	using System.Text;
	using System.Text.Json;

	[ApiController]
	[Route("api/[controller]")]
	//[Authorize]
	public class ChatController : ControllerBase
	{
		private readonly IHttpClientFactory _httpClientFactory;

		public ChatController(IHttpClientFactory httpClientFactory)
		{
			_httpClientFactory = httpClientFactory;
		}

		[HttpPost]
		public async Task<IActionResult> PostChat([FromBody] ChatRequest request)
		{
			//var userId = User.Claims.FirstOrDefault(c => c.Type == "id")?.Value ?? "unknown_user";
			var userId = request.userId;

			var payload = new
			{
				userId = userId,
				message = request.Message,
			};

			var content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

			// Call Python orchestrator microservice
			var client = _httpClientFactory.CreateClient();
			var response = await client.PostAsync("http://127.0.0.1:8000/api/chat", content);
			var responseText = await response.Content.ReadAsStringAsync();

			var chatResponse = JsonSerializer.Deserialize<ChatResponse>(
				responseText,
				new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
			);


			return Ok(chatResponse);
		}
	}

	public class ChatRequest
	{
		public string Message { get; set; } = string.Empty;
		public string userId { get; set; } = string.Empty;
	}

	public class ChatResponse
	{
		public string Response { get; set; } = string.Empty;
		public string Intent { get; set; } = string.Empty;
		public string ToolUsed { get; set; } = string.Empty;
	}


}
