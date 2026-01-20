namespace SalesSupportBackend.Models
{
	public class CartItem
	{
		public Guid Id { get; set; }
		public string Name { get; set; }
		public string Quantity { get; set; }
		public string OrderId { get; set; }
		public decimal Price { get; set; }
		public string Color { get; set; }
	}
}
