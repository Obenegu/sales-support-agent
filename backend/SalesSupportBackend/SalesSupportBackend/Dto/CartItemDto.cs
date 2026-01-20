namespace SalesSupportBackend.Dto
{
	public class CartItemDto
	{
		public string Name { get; set; }
		public string Quantity { get; set; }
		public decimal Price { get; set; }
		public string Color { get; set; } = "black";
	}
}
