
namespace SalesSupportBackend.Controllers
{
	using Microsoft.AspNetCore.Authorization;
	using Microsoft.AspNetCore.Mvc;
	using Microsoft.AspNetCore.SignalR;
	using Microsoft.EntityFrameworkCore;
	using SalesSupportBackend.Data;
	using SalesSupportBackend.Models;
	using System.Net;
	using System.Net.Http;
	using System.Text;
	using System.Text.Json;

	[ApiController]
	[Route("api/[controller]")]
	//[Authorize]
	public class ChatController : ControllerBase
	{
		private readonly IHttpClientFactory _httpClientFactory;
		private readonly AppDbContext _context;
		private readonly string _orchestratorUrl;

		public ChatController(IHttpClientFactory httpClientFactory, AppDbContext context, IConfiguration configuration)
		{
			_httpClientFactory = httpClientFactory;
			_context = context;
			_orchestratorUrl = configuration["Orchestrator:BaseUrl"] ?? "http://orchestrator:8000";
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
				role = "user",
                sessionId =	request.SessionId
            };

			var content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

			// Call Python orchestrator microservice
			var client = _httpClientFactory.CreateClient();
			var response = await client.PostAsync($"{_orchestratorUrl}/api/chat", content);
			var responseText = await response.Content.ReadAsStringAsync();

			var chatResponse = JsonSerializer.Deserialize<AgentResponse>(
				responseText,
				new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
			);


			//return Ok(chatResponse);

			var UserChat = new ChatLog
			{
				BusinessId = 1, // For simplicity, assuming BusinessId is 1
				SessionId = request.SessionId,
				Role = MessageRole.user,
				Content = request.Message,
				userId = userId,
				CreatedAt = DateTime.UtcNow
			};

			_context.ChatLogs.Add(UserChat);

			var newResponse = new ChatResponse
			{
				Response = chatResponse!.Response,
				Intent = chatResponse.Intent,
				ToolUsed = chatResponse.ToolUsed,
				role = MessageRole.assistant
			};

			var AgentChat = new ChatLog
			{
				BusinessId = 1, // For simplicity, assuming BusinessId is 1
				SessionId = request.SessionId,
				Role = MessageRole.assistant,
				Content = chatResponse!.Response,
				userId = userId,
				CreatedAt = DateTime.UtcNow
			};

			_context.ChatLogs.Add(AgentChat);

			await _context.SaveChangesAsync();


			return Ok(newResponse);
		}

		[HttpGet("{sessionId}")]
		public async Task<IActionResult> GetChatHistory(string sessionId)
		{
			// Fetch chat history for the user from the database
			// For simplicity, assuming userId maps directly to BusinessId

			var userId = "junior";

			var chatLogs = await _context.ChatLogs
				.Where(c => c.userId == userId)
				.Where(c => c.SessionId == sessionId)
				.OrderBy(c => c.CreatedAt)
				.ToListAsync();

			return Ok(chatLogs);
		}
	}

	public class ChatRequest
	{
		public string Message { get; set; } = string.Empty;
		public string userId { get; set; } = string.Empty;
		public string SessionId { get; set; } = string.Empty;
		public MessageRole role { get; set; } = MessageRole.user;
	}													  

	public class AgentResponse
	{
		public string Response { get; set; } = string.Empty;
		public string Intent { get; set; } = string.Empty;
		public string ToolUsed { get; set; } = string.Empty;
		public string role { get; set; } = string.Empty;
	}
	public class ChatResponse
	{
		public string Response { get; set; } = string.Empty;
		public string Intent { get; set; } = string.Empty;
		public string ToolUsed { get; set; } = string.Empty;
		public MessageRole role { get; set; } = MessageRole.assistant;
	}


}
