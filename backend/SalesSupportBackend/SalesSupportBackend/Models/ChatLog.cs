namespace SalesSupportBackend.Models
{
	public class ChatLog
	{
		public int Id { get; set; }

		public int BusinessId { get; set; }
		public Business Business { get; set; } = default!;

		public string UserMessage { get; set; } = default!;
		public string AgentResponse { get; set; } = default!;

		public DateTime Timestamp { get; set; } = DateTime.UtcNow;
	}
}
