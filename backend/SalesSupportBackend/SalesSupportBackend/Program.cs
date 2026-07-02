using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using SalesSupportBackend.Data;
using SalesSupportBackend.MiddleWare;
using SalesSupportBackend.Services;
using System.Text;

// AppContext.SetSwitch("System.Globalization.Invariant", true);  // <-- ADD THIS FIRST

AppContext.SetSwitch("Npgsql.EnableLegacyTimestampBehavior", true);

var builder = WebApplication.CreateBuilder(args);
var port = Environment.GetEnvironmentVariable("PORT") ?? "5132";
builder.WebHost.UseUrls($"http://0.0.0.0:{port}");

// Add services to the container.

//Database

// Hardcoded direct connection to Neon (bypasses channel_binding issue)
//var connectionString = "Host=ep-withered-cake-ahzv21ck.us-east-1.aws.neon.tech;" +
//                       "Port=5432;" +  // optional, default anyway
//                       "Database=neondb;" +
//                       "Username=neondb_owner;" +
//                       "Password=npg_Cp5WHyA3OQTJ;" +
//                       "Ssl Mode=Require;" +
//                       "Trust Server Certificate=true;";

var connectionString =
builder.Configuration.GetConnectionString("DefaultConnection")
?? Environment.GetEnvironmentVariable("DATABASE_URL");

//if (string.IsNullOrWhiteSpace(connectionString))
//{
//	throw new InvalidOperationException("Database connection string is missing.");
//}

// Remove channel_binding entirely (safest for Npgsql)
//connectionString = System.Text.RegularExpressions.Regex.Replace(
//connectionString,
//@"[?&]channel_binding=[^&]*",
//string.Empty
//);

builder.Services.AddDbContext<AppDbContext>(options =>
{
	options.UseNpgsql(connectionString);
});

//Authentication
// JWT Settings
//var key = Encoding.ASCII.GetBytes(builder.Configuration["Jwt:Key"]!);
//var key = Encoding.ASCII.GetBytes("YOUR_VERY_SECRET_KEY_HERE");

//var jwtKeyBase64 = builder.Configuration["Jwt:Key"]
//    ?? throw new InvalidOperationException("JWT key is missing. Set Jwt:Key in configuration (as Base64 string).");

//if (string.IsNullOrWhiteSpace(jwtKeyBase64))
//    throw new InvalidOperationException("JWT key is empty.");

//// THIS IS THE ONLY CORRECT WAY
//byte[] keyBytes = Convert.FromBase64String(jwtKeyBase64);

//if (keyBytes.Length < 32)
//    throw new InvalidOperationException($"JWT key too weak: only {keyBytes.Length} bytes (need ≥32).");

//builder.Services.AddAuthentication(options =>
//{
//	options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
//	options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
//})
//.AddJwtBearer(options =>
//{
//	options.RequireHttpsMetadata = false; // set true in production
//	options.SaveToken = true;
//	options.TokenValidationParameters = new TokenValidationParameters
//	{
//		ValidateIssuerSigningKey = true,
//		IssuerSigningKey = new SymmetricSecurityKey(keyBytes),
//		ValidateIssuer = false,
//		ValidateAudience = false
//	};
//});

builder.Services.AddControllers();
builder.Services.AddHttpClient();
//builder.Services.AddAuthorization();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(option =>
{
	option.SwaggerDoc("v1", new OpenApiInfo { Title = "Auth API", Version = "v1" });
	option.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
	{
		In = ParameterLocation.Header,
		Description = "Please enter a valid token",
		Name = "Authorization",
		Type = SecuritySchemeType.Http,
		BearerFormat = "JWT",
		Scheme = "Bearer"
	});
	option.AddSecurityRequirement(new OpenApiSecurityRequirement
	{
		{
			new OpenApiSecurityScheme
			{
				Reference = new OpenApiReference
				{
					Type=ReferenceType.SecurityScheme,
					Id="Bearer"
				}
			},
			new string[]{}
		}
	});

	//File upload operation
	option.OperationFilter<FileUploadOperation>();

});

// Add CORS policy
builder.Services.AddCors(options =>
{
	options.AddPolicy("AllowFrontend",
		builder =>
		{
			builder
				.WithOrigins("http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:8000", "http://host.docker.internal", "http://frontend", "http://frontend:3000")
                .AllowAnyHeader()
				.AllowAnyMethod()
				.AllowCredentials(); // If using cookies or authorization headers
		});
});


//builder.Services.AddScoped<JwtService>();


var app = builder.Build();

// Auto-apply EF Core migrations and seed default data on startup
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.Migrate();

    // Seed default business (BusinessId=1 used by all controllers)
    if (!db.Businesses.Any(b => b.Id == 1))
    {
        db.Businesses.Add(new SalesSupportBackend.Models.Business
        {
            Id = 1,
            Name = "Default Business",
            ApiKey = null
        });
        db.SaveChanges();
    }

    // Seed default user (used by frontend as userId="junior")
    if (!db.Users.Any(u => u.Email == "junior"))
    {
        db.Users.Add(new SalesSupportBackend.Models.User
        {
            Email = "junior",
            Name = "Junior",
            Password = "changeme123",
            CreatedAt = DateTime.UtcNow
        });
        db.SaveChanges();
    }

    // Seed default products (so search_product tool returns results out of the box)
    if (!db.Products.Any())
    {
        db.Products.AddRange(
            new SalesSupportBackend.Models.Product { Id = Guid.NewGuid(), Name = "Ballpoint Pen", Description = "Smooth-writing blue ink pen, pack of 10", Price = 500m },
            new SalesSupportBackend.Models.Product { Id = Guid.NewGuid(), Name = "Notebook A4", Description = "200-page ruled notebook, hard cover", Price = 1500m },
            new SalesSupportBackend.Models.Product { Id = Guid.NewGuid(), Name = "Desk Lamp LED", Description = "USB rechargeable LED desk lamp with 3 brightness levels", Price = 8000m },
            new SalesSupportBackend.Models.Product { Id = Guid.NewGuid(), Name = "Wireless Mouse", Description = "2.4GHz wireless mouse, ergonomic design", Price = 5000m },
            new SalesSupportBackend.Models.Product { Id = Guid.NewGuid(), Name = "USB-C Hub", Description = "7-in-1 USB-C hub with HDMI, SD card, 3x USB 3.0", Price = 12000m },
            new SalesSupportBackend.Models.Product { Id = Guid.NewGuid(), Name = "Water Bottle 1L", Description = "Stainless steel insulated water bottle, keeps drinks cold 24h", Price = 4500m },
            new SalesSupportBackend.Models.Product { Id = Guid.NewGuid(), Name = "Backpack", Description = "Water-resistant laptop backpack, 15.6 inch compartment", Price = 18000m },
            new SalesSupportBackend.Models.Product { Id = Guid.NewGuid(), Name = "Phone Stand", Description = "Adjustable aluminum phone stand for desk", Price = 3000m }
        );
        db.SaveChanges();
    }
}

// Use Railway's PORT
//var port = Environment.GetEnvironmentVariable("PORT") ?? "8080";
//app.Urls.Add($"http://*:{port}");

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
	app.UseSwagger();
	app.UseSwaggerUI();
}

app.UseMiddleware<SanitizationMiddleware>();

//app.UseHttpsRedirection();
if (!app.Environment.IsDevelopment())
{
    app.UseHttpsRedirection();
}

app.UseCors("AllowFrontend");

app.UseAuthentication();

app.UseAuthorization();

app.MapControllers();

app.Run();
