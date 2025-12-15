using Microsoft.EntityFrameworkCore;
using SalesSupportBackend.Models;
using System.Reflection.Emit;

namespace SalesSupportBackend.Data
{
	public class AppDbContext : DbContext
	{
		public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

		public DbSet<User> Users { get; set; }
		public DbSet<Business> Businesses { get; set; }
		public DbSet<Lead> Leads { get; set; }
		public DbSet<ChatLog> ChatLogs { get; set; }
		public DbSet<Document> Documents { get; set; }

		protected override void OnModelCreating(ModelBuilder builder)
		{
			builder.Entity<ChatLog>().HasIndex(m => new { m.BusinessId, m.CreatedAt });
		
			base.OnModelCreating(builder);

			builder.Entity<Business>()
				.HasOne(b => b.Owner)
				.WithMany(u => u.Businesses)
				.HasForeignKey(b => b.OwnerId);

			builder.Entity<Lead>()
				.HasOne(l => l.Business)
				.WithMany(b => b.Leads)
				.HasForeignKey(l => l.BusinessId);

			builder.Entity<Document>()
				.HasOne(d => d.Business)
				.WithMany()
				.HasForeignKey(d => d.BusinessId);

			builder.Entity<ChatLog>()
				.HasOne(c => c.Business)
				.WithMany(b => b.ChatLogs)
				.HasForeignKey(c => c.BusinessId);
		}

	}
}
