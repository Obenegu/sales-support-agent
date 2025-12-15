namespace SalesSupportBackend.Models
{
	public class Business
	{
		public int Id { get; set; }
		public string Name { get; set; } = default!;
		public string? ApiKey { get; set; } = default!;
		public int? OwnerId { get; set; }
		public User? Owner { get; set; } = default!;

		public ICollection<Lead>? Leads { get; set; } = new List<Lead>();
		public ICollection<ChatLog>? ChatLogs { get; set; } = new List<ChatLog>();
	}
}
