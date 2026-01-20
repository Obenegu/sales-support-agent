using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SalesSupportBackend.Data;
using SalesSupportBackend.Dto;
using SalesSupportBackend.Models;

namespace SalesSupportBackend.Controllers
{
	[Route("api/[controller]")]
	[ApiController]
	public class OrderController : ControllerBase
	{
		private readonly AppDbContext _context;

		public OrderController(AppDbContext context)
		{
			_context = context;
		}

		[HttpGet("{orderId}")]
		public async Task<IActionResult> GetOrderbyOrderId(string orderId, string userId)
		{
			var order = await _context.Order
				.Include(o => o.items)
				.Where(o => o.userId == userId && o.OrderId == orderId)
				.ToListAsync();

			return Ok(order);
		}

		[HttpGet]
		public async Task<IActionResult> GetAllOrders()
		{
			var orders = await _context.Order
				.Include(o => o.items)
				.ToListAsync();
			return Ok(orders);
		}

		[HttpPost("create-cart")]
		public async Task<IActionResult> CreateCart([FromBody] CartDto order)
		{
			var cartItem = new List<CartItem>();

			foreach (var item in order.items)
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
				status = "Not Paid"
			};

			if (order != null)
			{
				_context.Order.Add(newOrder);
				await _context.SaveChangesAsync();

				return Ok("Product Added to Cart");
			}

			return BadRequest("Add to Cart Failed");
		}
		
		[HttpPost("add-to-cart")]
		public async Task<IActionResult> AddToCart(string orderId, List<CartItemDto> items)
		{
			// 1. Get existing order with items
			var existingOrder = await _context.Order
				.Include(o => o.items)
				.FirstOrDefaultAsync(o => o.OrderId == orderId && o.status == "Not Paid");

			if (existingOrder == null)
			{
				return NotFound("Order not found");
			}

			// 2. Add new items to existing cart
			foreach (var item in items)
			{
				try
				{
					existingOrder.items.Add(new CartItem
					{
						Id = Guid.NewGuid(),
						Quantity = item.Quantity,
						Name = item.Name,
						Price = item.Price,
						Color = item.Color,
					});

				} catch (Exception ex)
				{
					return BadRequest($"Error adding item {item.Name}: {ex.Message}");
				};
				
			}

			// Prevent EF from updating the parent row

			_context.Entry(existingOrder).Collection(o => o.items).IsModified = true; // Only mark collection as changed
																					  // Or just mark individual added items if needed
																					  // Or: _context.Entry(existingOrder).State = EntityState.Modified; then set all properties to unmodified if needed

			// 3. Save changes
			await _context.SaveChangesAsync();

			return Ok(existingOrder);
		}
	}
}
