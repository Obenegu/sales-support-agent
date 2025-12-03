
namespace SalesSupportBackend.Controllers
{
	using Microsoft.AspNetCore.Authorization;
	using Microsoft.AspNetCore.Mvc;
	using System.IO;

	[Route("api/[controller]")]
	[ApiController]
	public class DocumentsController : ControllerBase
	{
		private readonly IWebHostEnvironment _env;
		private readonly IHttpClientFactory _httpFactory;
		private readonly ILogger<DocumentsController> _logger;

		public DocumentsController(IWebHostEnvironment env, IHttpClientFactory httpFactory, ILogger<DocumentsController> logger)
		{
			_env = env;
			_httpFactory = httpFactory;
			_logger = logger;
		}

		[HttpPost("upload")]
		//[Authorize] // require JWT
		public async Task<IActionResult> Upload([FromForm] IFormFile file, [FromForm] int businessId)
		{
			if (file == null || file.Length == 0) return BadRequest("No file uploaded.");
			if (file.Length > 20 * 1024 * 1024) return BadRequest("File too large (max 20MB).");

			var allowed = new[] { ".pdf", ".html", ".htm", ".txt" };
			var ext = Path.GetExtension(file.FileName).ToLowerInvariant();
			if (!allowed.Contains(ext)) return BadRequest("Unsupported file type.");

			// Save locally (or upload to blob storage here)
			// for now (test) save locally but in prod use Blob storage (S3/Azure Blob)
			var uploads = Path.Combine(_env.ContentRootPath, "uploads");
			Directory.CreateDirectory(uploads);
			var fileName = $"{Guid.NewGuid()}{ext}";
			var filePath = Path.Combine(uploads, fileName);

			using (var stream = System.IO.File.Create(filePath))
			{
				await file.CopyToAsync(stream);
			}

			// Call orchestrator ingestion endpoint
			var client = _httpFactory.CreateClient();
			// Forward Authorization header to orchestrator
			//if (Request.Headers.TryGetValue("Authorization", out var authHeader))
			//{
			//	client.DefaultRequestHeaders.Add("Authorization", (string)authHeader);
			//}

			var orchestratorUrl = Environment.GetEnvironmentVariable("ORCHESTRATOR_URL") ?? "http://127.0.0.1:8000/api/ingest";
			using var ms = new MemoryStream();
			using (var fs = System.IO.File.OpenRead(filePath))
			{
				await fs.CopyToAsync(ms);
			}
			ms.Seek(0, SeekOrigin.Begin);

			var content = new MultipartFormDataContent();
			content.Add(new StreamContent(ms), "file", fileName);
			content.Add(new StringContent(businessId.ToString()), "businessId");

			var res = await client.PostAsync(orchestratorUrl, content);
			if (!res.IsSuccessStatusCode)
			{
				_logger.LogError("Orchestrator ingest failed: {Status} {Body}", res.StatusCode, await res.Content.ReadAsStringAsync());
				return StatusCode(500, "Ingestion failed.");
			}

			return Ok(new { message = "Uploaded and queued for ingestion." });
		}
	}


	public class DocumentUploadRequest
	{
		public IFormFile File { get; set; } = default!;
		public int BusinessId { get; set; }
	}

}
