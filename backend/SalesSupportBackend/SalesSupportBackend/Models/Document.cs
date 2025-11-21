namespace SalesSupportBackend.Models
{
	public class Document
	{
		public int Id { get; set; }
		public int BusinessId { get; set; }
		public Business Business { get; set; } = default!;

		public string FileName { get; set; } = default!;
		public string FilePath { get; set; } = default!;
		public DateTime UploadedAt { get; set; } = DateTime.UtcNow;
	}
}
