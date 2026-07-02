using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SalesSupportBackend.Data;
using SalesSupportBackend.Models;
using System.Text;
using System.Text.Json;

namespace SalesSupportBackend.Controllers
{
	[ApiController]
	[Route("api/[controller]")]
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
			var userId = request.userId;

			// Ensure session exists — create if new
			var session = await _context.Sessions.FindAsync(request.SessionId);
			if (session == null)
			{
				session = new Session
				{
					Id = request.SessionId,
					UserId = userId,
					Title = "New Chat",
					CreatedAt = DateTime.UtcNow
				};
				_context.Sessions.Add(session);
			}

			// Auto-title from first user message (only if still default)
			if (session.Title == "New Chat")
			{
				session.Title = request.Message.Length > 40
					? request.Message[..40] + "..."
					: request.Message;
			}

			// --- Orchestrator call ---
			ChatResponse newResponse;
			try
			{
				var payload = new { userId, message = request.Message, role = "user", sessionId = request.SessionId, businessId = 1 };
				var content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
				var client = _httpClientFactory.CreateClient();
				var response = await client.PostAsync($"{_orchestratorUrl}/api/chat", content);
				var responseText = await response.Content.ReadAsStringAsync();
				var chatResponse = JsonSerializer.Deserialize<AgentResponse>(responseText, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

				newResponse = new ChatResponse
				{
					Response = chatResponse!.Response,
					Intent = chatResponse.Intent,
					ToolUsed = chatResponse.ToolUsed,
					role = Enum.TryParse<MessageRole>(chatResponse.role, ignoreCase: true, out var parsedRole) ? parsedRole : MessageRole.assistant
				};
			}
			catch (Exception ex)
			{
				// Fallback if orchestrator is unreachable
				// (old hardcoded maintenance response kept below for reference)
				// var newResponse = new ChatResponse
				// {
				// 	Response = "We are sorry, we are under maintenance at the moment",
				// 	Intent = "general",
				// 	ToolUsed = "",
				// 	role = MessageRole.assistant
				// };
				newResponse = new ChatResponse
				{
					Response = "We are sorry, we are under maintenance at the moment",
					Intent = "general",
					ToolUsed = "",
					role = MessageRole.assistant
				};
			}

			// Save user message
			_context.ChatLogs.Add(new ChatLog
			{
				BusinessId = 1,
				SessionId = request.SessionId,
				Role = MessageRole.user,
				Content = request.Message,
				userId = userId,
				CreatedAt = DateTime.UtcNow
			});

			// Save assistant response
			_context.ChatLogs.Add(new ChatLog
			{
				BusinessId = 1,
				SessionId = request.SessionId,
				Role = MessageRole.assistant,
				Content = newResponse.Response,
				userId = userId,
				CreatedAt = DateTime.UtcNow
			});

			await _context.SaveChangesAsync();

			return Ok(newResponse);
		}

		[HttpGet("{sessionId}")]
		public async Task<IActionResult> GetChatHistory(string sessionId, [FromQuery] string userId)
		{
			if (string.IsNullOrWhiteSpace(userId))
				return BadRequest("userId query param is required");

			var chatLogs = await _context.ChatLogs
				.Where(c => c.SessionId == sessionId && c.userId == userId)
				.OrderBy(c => c.CreatedAt)
				.Select(c => new ChatLogDto
				{
					Id = c.Id,
					SessionId = c.SessionId,
					Role = c.Role.ToString(),
					Content = c.Content,
					CreatedAt = c.CreatedAt
				})
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

	public class ChatLogDto
	{
		public int Id { get; set; }
		public string SessionId { get; set; } = string.Empty;
		public string Role { get; set; } = string.Empty;
		public string Content { get; set; } = string.Empty;
		public DateTime CreatedAt { get; set; }
	}
}
