using System.ComponentModel.DataAnnotations;

namespace SalesSupportBackend.Models
{
	public enum MessageRole
	{
		assistant,
		user
	}
	public class ChatLog
	{
		public int Id { get; set; }

		public int BusinessId { get; set; }
		public string SessionId { get; set; }
		public Business Business { get; set; } = default!;
		public string userId { get; set; }
		public MessageRole Role { get; set; }
		public string Content { get; set; }
		public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
	}
}
