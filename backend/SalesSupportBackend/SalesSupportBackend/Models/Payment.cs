namespace SalesSupportBackend.Models
{
	public class Payment
	{
		public Guid Id { get; set; }
		public string UserId { get; set; }
		public decimal Amount { get; set; }
		public string PaymentMethod { get; set; } = "Cash";
		public DateTime PaymentDate { get; set; }
	}
}
