using SalesSupportBackend.Models;

namespace SalesSupportBackend.Dto
{
	public class CartDto
	{
		public string userId { get; set; }
		public string OrderId { get; set; }
		public List<CartItemDto> items { get; set; } = new List<CartItemDto>();
		public string? status { get; set; } = "Not Delivered";
	}
}
