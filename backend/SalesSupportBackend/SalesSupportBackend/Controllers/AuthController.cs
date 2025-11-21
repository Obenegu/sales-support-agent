using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SalesSupportBackend.Data;
using SalesSupportBackend.Models;
using SalesSupportBackend.Models.Auth;
using SalesSupportBackend.Services;

namespace SalesSupportBackend.Controllers
{
	[ApiController]
	[Route("api/auth")]
	public class AuthController : ControllerBase
	{
		private readonly AppDbContext _db;
		private readonly JwtService _jwt;

		public AuthController(AppDbContext db, JwtService jwt)
		{
			_db = db;
			_jwt = jwt;
		}

		[HttpPost("register")]
		public async Task<IActionResult> Register(RegisterRequest request)
		{
			if (await _db.Users.AnyAsync(u => u.Email == request.Email))
				return BadRequest("Email already registered.");

			var user = new User
			{
				Email = request.Email,
				Password = request.Password
			};

			_db.Users.Add(user);
			await _db.SaveChangesAsync();

			// Create default business
			var business = new Business
			{
				Name = request.BusinessName,
				OwnerId = user.Id,
				ApiKey = Guid.NewGuid().ToString("N")
			};

			_db.Businesses.Add(business);
			await _db.SaveChangesAsync();

			return Ok(new { message = "Registered successfully." });
		}

		
		[HttpPost("login")]
		public async Task<IActionResult> Login(LoginRequest request)
		{
			var user = await _db.Users
				.Include(u => u.Businesses)
				.FirstOrDefaultAsync(u => u.Email == request.Email);

			if (user == null || user.Password != request.Password)
				return Unauthorized("Invalid email or password.");

			// NOTE: if you want multi-business support later, handle selection
			var business = user.Businesses.FirstOrDefault();

			var token = _jwt.GenerateToken(user.Id, user.Email);

			return Ok(new AuthResponse
			{
				Token = token,
				BusinessId = business?.Id ?? 0,
				RefreshToken = ""
			});
		}
	}
}
