using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using SalesSupportBackend.Data;
using SalesSupportBackend.Dto;
using SalesSupportBackend.Models;

namespace SalesSupportBackend.Controllers
{
	[Route("api/[controller]")]
	[ApiController]
	public class PaymentController : ControllerBase
	{
		private readonly AppDbContext _context;

		public PaymentController(AppDbContext context)
		{
			_context = context;
		}

		[HttpPost("process-payment")]
		public async Task<IActionResult> ProcessPayment([FromBody] CartDto order, [FromQuery] decimal amount)
		{
			var cartItem = new List<CartItem>();

			foreach(var item in order.items)
			{
				cartItem.Add(new CartItem
				{
					Id = Guid.NewGuid(),
					Quantity = item.Quantity,
					Name = item.Name,
					Price = item.Price,
					Color = item.Color,
				});
			}


			var newOrder = new Cart
			{
				id = Guid.NewGuid(),
				userId = order.userId,
				OrderId = order.OrderId,
				items = cartItem,
				createdAt = DateTime.UtcNow,
				status = "Paid"
			};

			if(order != null && amount > 0)
			{
				_context.Order.Add(newOrder);
				await _context.SaveChangesAsync();

				return Ok("Payment Successful");
			}

			return BadRequest("Payment Failed");

		}
	}
}
