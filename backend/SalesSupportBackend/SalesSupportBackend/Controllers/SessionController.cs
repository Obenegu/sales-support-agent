using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SalesSupportBackend.Data;
using SalesSupportBackend.Models;

namespace SalesSupportBackend.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class SessionController : ControllerBase
    {
        private readonly AppDbContext _context;

        public SessionController(AppDbContext context)
        {
            _context = context;
        }

        // GET /api/Session?userId=junior
        [HttpGet]
        public async Task<IActionResult> GetSessions([FromQuery] string userId)
        {
            if (string.IsNullOrWhiteSpace(userId))
                return BadRequest("userId is required");

            var sessions = await _context.Sessions
                .Where(s => s.UserId == userId)
                .OrderByDescending(s => s.CreatedAt)
                .Select(s => new SessionDto
                {
                    Id = s.Id,
                    UserId = s.UserId,
                    Title = s.Title,
                    CreatedAt = s.CreatedAt,
                    MessageCount = s.ChatLogs.Count
                })
                .ToListAsync();

            return Ok(sessions);
        }

        // POST /api/Session
        [HttpPost]
        public async Task<IActionResult> CreateSession([FromBody] CreateSessionRequest request)
        {
            if (string.IsNullOrWhiteSpace(request.UserId))
                return BadRequest("userId is required");

            var session = new Session
            {
                Id = Guid.NewGuid().ToString(),
                UserId = request.UserId,
                Title = request.Title ?? "New Chat",
                CreatedAt = DateTime.UtcNow
            };

            _context.Sessions.Add(session);
            await _context.SaveChangesAsync();

            return Ok(new SessionDto
            {
                Id = session.Id,
                UserId = session.UserId,
                Title = session.Title,
                CreatedAt = session.CreatedAt,
                MessageCount = 0
            });
        }

        // PUT /api/Session/{id}
        [HttpPut("{id}")]
        public async Task<IActionResult> UpdateSession(string id, [FromBody] UpdateSessionRequest request)
        {
            var session = await _context.Sessions.FindAsync(id);
            if (session == null) return NotFound();

            session.Title = request.Title;
            await _context.SaveChangesAsync();

            return Ok(new SessionDto
            {
                Id = session.Id,
                UserId = session.UserId,
                Title = session.Title,
                CreatedAt = session.CreatedAt
            });
        }

        // DELETE /api/Session/{id}
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteSession(string id)
        {
            var session = await _context.Sessions.FindAsync(id);
            if (session == null) return NotFound();

            var chatLogs = await _context.ChatLogs
                .Where(c => c.SessionId == id)
                .ToListAsync();

            _context.ChatLogs.RemoveRange(chatLogs);
            _context.Sessions.Remove(session);
            await _context.SaveChangesAsync();

            return Ok();
        }
    }

    public class CreateSessionRequest
    {
        public string UserId { get; set; } = string.Empty;
        public string? Title { get; set; }
    }

    public class UpdateSessionRequest
    {
        public string Title { get; set; } = string.Empty;
    }

    public class SessionDto
    {
        public string Id { get; set; } = string.Empty;
        public string UserId { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public int MessageCount { get; set; }
    }
}
