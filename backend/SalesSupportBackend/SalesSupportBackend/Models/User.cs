
namespace SalesSupportBackend.Models
{
	public class User
	{
		public int Id { get; set; }
		public string Email { get; set; } = default!;
		public string Password { get; set; } = default!;
		public string Name { get; set; } = default!;
		public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

		public ICollection<Business> Businesses { get; set; } = new List<Business>();
	}
}
