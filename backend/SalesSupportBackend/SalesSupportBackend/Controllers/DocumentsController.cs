
namespace SalesSupportBackend.Controllers
{
	using Microsoft.AspNetCore.Authorization;
	using Microsoft.AspNetCore.Mvc;
	using SalesSupportBackend.Data;
	using SalesSupportBackend.Models;

	[ApiController]
	[Route("api/[controller]")]
	[Authorize]
	public class DocumentsController : ControllerBase
	{
		private readonly AppDbContext _db;
		private readonly IWebHostEnvironment _env;

		public DocumentsController(AppDbContext db, IWebHostEnvironment env)
		{
			_db = db;
			_env = env;
		}

		[HttpPost("upload")]
		public async Task<IActionResult> UploadDocument([FromForm] DocumentUploadRequest request)
		{
			if (request.File.Length == 0)
				return BadRequest("Empty file");

			var filePath = Path.Combine(_env.ContentRootPath, "Uploads", request.File.FileName);

			using (var stream = new FileStream(filePath, FileMode.Create))
			{
				await request.File.CopyToAsync(stream);
			}

			var doc = new Document
			{
				FileName = request.File.FileName,
				FilePath = filePath,
				BusinessId = request.BusinessId,
				UploadedAt = DateTime.UtcNow
			};

			_db.Documents.Add(doc);
			await _db.SaveChangesAsync();

			return Ok(new { message = "Document uploaded", doc.Id });
		}
	}

	public class DocumentUploadRequest
	{
		public IFormFile File { get; set; } = default!;
		public int BusinessId { get; set; }
	}

}
