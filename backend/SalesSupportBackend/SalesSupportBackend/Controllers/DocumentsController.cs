namespace SalesSupportBackend.Controllers
{
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
		public async Task<IActionResult> Upload([FromForm] IFormFile file, [FromForm] int businessId)
		{
			if (file == null || file.Length == 0) return BadRequest("No file uploaded.");
			if (file.Length > 20 * 1024 * 1024) return BadRequest("File too large (max 20MB).");

			var allowed = new[] { ".pdf", ".html", ".htm", ".txt" };
			var ext = Path.GetExtension(file.FileName).ToLowerInvariant();
			if (!allowed.Contains(ext)) return BadRequest("Unsupported file type.");

			// Save locally
			var uploads = Path.Combine(_env.ContentRootPath, "uploads");
			Directory.CreateDirectory(uploads);
			var fileName = $"{Guid.NewGuid()}{ext}";
			var filePath = Path.Combine(uploads, fileName);

			await using (var stream = System.IO.File.Create(filePath))
			{
				await file.CopyToAsync(stream);
			}

			// Forward to orchestrator for ingestion (chunk → embed → pgvector)
			var orchestratorUrl = Environment.GetEnvironmentVariable("ORCHESTRATOR_URL")
				?? "http://host.docker.internal:8000/api/ingest";

			var client = _httpFactory.CreateClient();
			string errorBody = "";

			try
			{
				await using var ms = new MemoryStream();
				await using (var fs = System.IO.File.OpenRead(filePath))
				{
					await fs.CopyToAsync(ms);
				}
				ms.Seek(0, SeekOrigin.Begin);

				var content = new MultipartFormDataContent();
				content.Add(new StreamContent(ms), "file", file.FileName);
				content.Add(new StringContent(businessId.ToString()), "businessId");

				var res = await client.PostAsync(orchestratorUrl, content);
				if (!res.IsSuccessStatusCode)
				{
					errorBody = await res.Content.ReadAsStringAsync();
					_logger.LogError("Orchestrator ingest failed ({Status}): {Body}", res.StatusCode, errorBody);
					return StatusCode(500, new { error = "File saved but ingestion failed.", details = errorBody });
				}
			}
			catch (HttpRequestException ex)
			{
				_logger.LogError(ex, "Orchestrator unreachable at {Url}", orchestratorUrl);
				return StatusCode(500, new { error = "File saved but orchestrator is unreachable — ingestion skipped.", details = ex.Message });
			}

			return Ok(new
			{
				message = "Uploaded and ingested successfully.",
				fileName = file.FileName,
				savedAs = fileName
			});
		}
	}
}
