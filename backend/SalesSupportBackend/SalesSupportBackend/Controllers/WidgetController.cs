
namespace SalesSupportBackend.Controllers
{
	using Microsoft.AspNetCore.Authorization;
	using Microsoft.AspNetCore.Mvc;

	[ApiController]
	[Route("api/[controller]")]
	public class WidgetController : ControllerBase
	{
		[HttpGet("config")]
		public IActionResult GetWidgetConfig()
		{
			var config = new
			{
				apiUrl = "/api/chat",
				token = HttpContext.Request.Headers["Authorization"].ToString(),
				options = new { theme = "light" }
			};

			return Ok(config);
		}
	}

}
