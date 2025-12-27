using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using SalesSupportBackend.Data;
using SalesSupportBackend.MiddleWare;
using SalesSupportBackend.Services;
using System.Text;


AppContext.SetSwitch("Npgsql.EnableLegacyTimestampBehavior", true);

var builder = WebApplication.CreateBuilder(args);

builder.WebHost.UseUrls($"http://0.0.0.0:{Environment.GetEnvironmentVariable("PORT") ?? "8080"}");

// Add services to the container.

//Database
var connectionString =
	builder.Configuration.GetConnectionString("DefaultConnection")
	?? Environment.GetEnvironmentVariable("DATABASE_URL");

if (string.IsNullOrWhiteSpace(connectionString))
{
	throw new InvalidOperationException("Database connection string is missing.");
}

// Remove channel_binding entirely (safest for Npgsql)
	connectionString = System.Text.RegularExpressions.Regex.Replace(
		connectionString,
		@"[?&]channel_binding=[^&]*",
		string.Empty
	);

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
				.WithOrigins("http://localhost:5173", "http://localhost:3000")
				.AllowAnyHeader()
				.AllowAnyMethod()
				.AllowCredentials(); // If using cookies or authorization headers
		});
});


//builder.Services.AddScoped<JwtService>();


var app = builder.Build();

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

app.UseHttpsRedirection();

app.UseCors("AllowFrontend");

app.UseAuthentication();

app.UseAuthorization();

app.MapControllers();

app.Run();
