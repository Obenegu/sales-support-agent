
namespace SalesSupportBackend.Controllers
{
	using Microsoft.AspNetCore.Authorization;
	using Microsoft.AspNetCore.Mvc;
	using SalesSupportBackend.Data;
	using SalesSupportBackend.Models;

	[ApiController]
	[Route("api/[controller]")]
	public class LeadController : ControllerBase
	{
		private readonly AppDbContext _db;

		public LeadController(AppDbContext db)
		{
			_db = db;
		}

		[HttpPost]
		public async Task<IActionResult> AddLead([FromBody] LeadRequest request)
		{
			var userId = int.Parse(User.Claims.First(c => c.Type == "id").Value);

			var lead = new Lead
			{
				Name = request.Name,
				Email = request.Email,
				Phone = request.Phone,
				BusinessId = request.BusinessId,
				CreatedAt = DateTime.UtcNow
			};

			_db.Leads.Add(lead);
			await _db.SaveChangesAsync();

			return Ok(new { message = "Lead saved successfully", lead.Id });
		}
	}

	public class LeadRequest
	{
		public string Name { get; set; } = string.Empty;
		public string Email { get; set; } = string.Empty;
		public string Phone { get; set; } = string.Empty;
		public int BusinessId { get; set; }
	}

}
