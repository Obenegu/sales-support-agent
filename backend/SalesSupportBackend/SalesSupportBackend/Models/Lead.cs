namespace SalesSupportBackend.Models
{
	public class Lead
	{
		public int Id { get; set; }
		public int BusinessId { get; set; }
		public Business Business { get; set; } = default!;

		public string Name { get; set; } = default!;
		public string? Email { get; set; }
		public string? Phone { get; set; }

		public string Status { get; set; } = "new";  // new, warm, hot, closed
		public string Notes { get; set; } = string.Empty;

		public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
	}
}
