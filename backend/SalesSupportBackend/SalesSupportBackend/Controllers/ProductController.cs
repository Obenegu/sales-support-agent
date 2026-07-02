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

			var term = name.ToLower().Trim();

			// ── Step 1: Direct substring match ────────────────────────────
			var results = await _context.Products
				.Where(p => p.Name.ToLower().Contains(term))
				.ToListAsync();

			if (results.Any())
				return Ok(results);

			// ── Step 2: Try each word individually (for "ballpoint pen") ──
			var words = term.Split(' ', StringSplitOptions.RemoveEmptyEntries);
			if (words.Length > 1)
			{
				results = await _context.Products.ToListAsync();
				results = results
					.Where(p => words.Any(w => p.Name.ToLower().Contains(w)))
					.ToList();

				if (results.Any())
					return Ok(results);
			}

			// ── Step 3: Singularize plural (pens→pen, shoes→shoe, etc.) ──
			var singularTerm = TrySingularize(term);
			if (singularTerm != term)
			{
				results = await _context.Products
					.Where(p => p.Name.ToLower().Contains(singularTerm))
					.ToListAsync();

				if (results.Any())
					return Ok(results);
			}

			// ── Step 4: Return empty list (NOT 404) so the AI agent can retry ──
			return Ok(new List<Product>());
		}

		/// <summary>
		/// Simple English plural→singular conversion.
		/// Covers the most common patterns; not exhaustive but catches "pens", "phones", etc.
		/// </summary>
		private static string TrySingularize(string word)
		{
			if (string.IsNullOrEmpty(word))
				return word;

			// -ies → -y  (ladies→lady, companies→company)
			if (word.EndsWith("ies") && word.Length > 4)
				return word[..^3] + "y";

			// -ves → -f / -fe (knives→knife)
			if (word.EndsWith("ves") && word.Length > 4)
				return word[..^3] + "f";

			// -es → remove es (boxes→box, watches→watch, classes→class)
			if (word.EndsWith("ses") || word.EndsWith("xes") || word.EndsWith("zes") ||
			    word.EndsWith("ches") || word.EndsWith("shes"))
				return word[..^2];

			// -s → remove s (pens→pen, phones→phone)
			if (word.EndsWith("s") && !word.EndsWith("ss") && word.Length > 2)
				return word[..^1];

			return word;
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
