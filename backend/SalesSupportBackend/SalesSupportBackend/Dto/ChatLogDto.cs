using SalesSupportBackend.Models;
using System.ComponentModel.DataAnnotations;

namespace SalesSupportBackend.Dto
{
	public class ChatLogDto
	{
		public string BusinessId { get; set; }
		public string SessionId { get; set; }


		[Required]
		public MessageRole Role { get; set; }


		[Required]
		public string Content { get; set; }
	}
}
