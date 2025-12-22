using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;

namespace SalesSupportBackend.Controllers
{
	[Route("api/[controller]")]
	[ApiController]
	public class HealthController : ControllerBase
	{
		[HttpGet]
		public IActionResult GetHealth()
		{
			return Ok("Your Backend Site is live");
		}
	}
}
