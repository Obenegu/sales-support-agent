namespace SalesSupportBackend.MiddleWare
{
	using System.Text.RegularExpressions;
	using System.Threading.Tasks;
	using Microsoft.AspNetCore.Http;
	using Microsoft.Extensions.Logging;

	public class SanitizationMiddleware
	{
		private readonly RequestDelegate _next;
		private readonly ILogger<SanitizationMiddleware> _logger;
		private static Regex EmailRe = new Regex(@"[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-.]+", RegexOptions.Compiled);

		public SanitizationMiddleware(RequestDelegate next, ILogger<SanitizationMiddleware> logger)
		{
			_next = next;
			_logger = logger;
		}

		public async Task InvokeAsync(HttpContext context)
		{
			// Example: block requests with suspicious path or empty body
			if (context.Request.ContentLength == 0)
			{
				context.Response.StatusCode = 400;
				await context.Response.WriteAsync("Empty request not allowed.");
				return;
			}

			// We could also read body and detect PII; but reading body requires buffering.
			// For heavy checks use a specific ValidateModel attribute on controllers.

			await _next(context);
		}
	}

}
