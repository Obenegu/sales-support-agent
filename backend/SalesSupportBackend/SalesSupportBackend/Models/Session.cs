using System.ComponentModel.DataAnnotations;

namespace SalesSupportBackend.Models
{
    public class Session
    {
        [Key]
        public string Id { get; set; } = Guid.NewGuid().ToString();

        [Required]
        public string UserId { get; set; } = string.Empty;

        [Required]
        public string Title { get; set; } = "New Chat";

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        // Navigation
        public User User { get; set; } = default!;
        public ICollection<ChatLog> ChatLogs { get; set; } = new List<ChatLog>();
    }
}
