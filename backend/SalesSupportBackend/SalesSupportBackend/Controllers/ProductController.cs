using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using SalesSupportBackend.Data;
using Microsoft.EntityFrameworkCore;
using SalesSupportBackend.Models;
using SalesSupportBackend.Dto;


namespace SalesSupportBackend.Controllers
{
	[Route("api/[controller]")]
	[ApiController]
	public class ProductController : ControllerBase
	{
		private readonly AppDbContext _context;

		public ProductController(AppDbContext context)
		{
			_context = context;
		}
		[HttpPost]
		public async Task<IActionResult> AddProduct([FromBody] ProductDto product)
		{
			if (product == null || string.IsNullOrWhiteSpace(product.Name))
			{
				return BadRequest("Invalid product data.");
			}

			var newProduct = new Product
			{
				Id= Guid.NewGuid(),
				Name = product.Name,
				Description = product.Description,
			};

			_context.Products.Add(newProduct);
			await _context.SaveChangesAsync();

			return Ok(new { message = "Product added successfully", newProduct.Name });
		}

		[HttpGet("search")]
		public async Task<IActionResult> SearchByName([FromQuery] string name)
		{
			if (string.IsNullOrWhiteSpace(name))
			{
				return BadRequest("Search term cannot be empty.");
			}

			var results = await _context.Products
				.Where(p => p.Name.ToLower().Contains(name.ToLower()))
				.ToListAsync();

			if (!results.Any())
			{
				return NotFound("No products found.");
			}

			return Ok(results);
		}

		[HttpGet("{id}")]
		public async Task<IActionResult> GetProductById(Guid id)
		{
			var product = await _context.Products.FindAsync(id);
			if (product == null)
			{
				return NotFound("Product not found.");
			}

			return Ok(product.Price);
		}

		[HttpPut]
		public async Task<IActionResult> UpdateProduct([FromBody] ProductDto product, Guid Id)
		{
			var existingProduct = await _context.Products.FindAsync(Id);
			if (existingProduct == null)
			{
				return NotFound("Product not found.");
			}

			existingProduct.Name = product.Name;
			existingProduct.Description = product.Description;
			existingProduct.Price = product.Price;


			_context.Products.Update(existingProduct);
			await _context.SaveChangesAsync();

			return Ok(new { message = "Product updated successfully", existingProduct.Name });
		}
	}

}
