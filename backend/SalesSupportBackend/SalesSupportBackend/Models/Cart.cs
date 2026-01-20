namespace SalesSupportBackend.Models
{
	public class Cart
	{
		public Guid id { get; set; }
		public string userId { get; set; }
		public string OrderId { get; set; }
		public List<CartItem> items { get; set; }
		public DateTime createdAt { get; set; }
		public string? status { get; set; } = "Not Paid";
	}
}
