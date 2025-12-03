using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Moq;
using Moq.Protected;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Xunit;

namespace SalesSupportBackend.Tests.Controllers
{
	public class DocumentsControllerTests
	{
		[Fact]
		public async Task Upload_ValidFile_ReturnsOk()
		{
			// Arrange
			var envMock = new Mock<IWebHostEnvironment>();
			envMock.Setup(e => e.ContentRootPath).Returns(Path.GetTempPath());

			var loggerMock = new Mock<ILogger<SalesSupportBackend.Controllers.DocumentsController>>();

			var handler = new Mock<HttpMessageHandler>();
			handler
				.Protected()
				.Setup<Task<HttpResponseMessage>>(
					"SendAsync",
					ItExpr.IsAny<HttpRequestMessage>(),
					ItExpr.IsAny<CancellationToken>())
				.ReturnsAsync(new HttpResponseMessage(HttpStatusCode.OK)
				{
					Content = new StringContent("success", Encoding.UTF8, "application/json")
				});

			var client = new HttpClient(handler.Object);
			var factoryMock = new Mock<IHttpClientFactory>();
			factoryMock.Setup(f => f.CreateClient(It.IsAny<string>())).Returns(client);

			var controller = new SalesSupportBackend.Controllers.DocumentsController(
				envMock.Object,
				factoryMock.Object,
				loggerMock.Object
			);

			// Create a fake file
			var content = "Hello world";
			var bytes = Encoding.UTF8.GetBytes(content);
			var stream = new MemoryStream(bytes);
			IFormFile formFile = new FormFile(stream, 0, bytes.Length, "file", "test.txt");

			// Act
			var result = await controller.Upload(formFile, 123);

			// Assert
			var okResult = Assert.IsType<OkObjectResult>(result);
			Assert.Equal(200, okResult.StatusCode);
			Assert.Contains("Uploaded", okResult.Value.ToString());
		}

		[Fact]
		public async Task Upload_TooLargeFile_ReturnsBadRequest()
		{
			// Arrange
			var envMock = new Mock<IWebHostEnvironment>();
			envMock.Setup(e => e.ContentRootPath).Returns(Path.GetTempPath());

			var loggerMock = new Mock<ILogger<SalesSupportBackend.Controllers.DocumentsController>>();
			var factoryMock = new Mock<IHttpClientFactory>();

			var controller = new SalesSupportBackend.Controllers.DocumentsController(
				envMock.Object,
				factoryMock.Object,
				loggerMock.Object
			);

			// Create a fake oversized file (21MB)
			var stream = new MemoryStream(new byte[21 * 1024 * 1024]);
			IFormFile formFile = new FormFile(stream, 0, stream.Length, "file", "big.pdf");

			// Act
			var result = await controller.Upload(formFile, 123);

			// Assert
			var badRequest = Assert.IsType<BadRequestObjectResult>(result);
			Assert.Equal("File too large (max 20MB).", badRequest.Value);
		}
	}
}