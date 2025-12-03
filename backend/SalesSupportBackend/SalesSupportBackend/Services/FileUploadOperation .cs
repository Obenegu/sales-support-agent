using Microsoft.OpenApi.Models;
using Swashbuckle.AspNetCore.SwaggerGen;

namespace SalesSupportBackend.Services
{
    public class FileUploadOperation : IOperationFilter
    {
        public void Apply(OpenApiOperation operation, OperationFilterContext context)
        {
            var fileParams = context.MethodInfo.GetParameters()
                .Where(p => p.ParameterType == typeof(IFormFile));

            foreach (var param in fileParams)
            {
                operation.RequestBody = new OpenApiRequestBody
                {
                    Content = {
                    ["multipart/form-data"] = new OpenApiMediaType
                    {
                        Schema = new OpenApiSchema
                        {
                            Type = "object",
                            Properties = {
                                ["title"] = new OpenApiSchema { Type = "string" },
                                ["documentType"] = new OpenApiSchema { Type = "string" },
                                //["description"] = new OpenApiSchema { Type = "string" },
                                //["newVideo"] = new OpenApiSchema
                                //{
                                //    Type = "string",
                                //    Format = "binary"
                                //}
                                ["file"] = new OpenApiSchema
								{
									Type = "string",
									Format = "binary"
								}
							},
                            //Required = new HashSet<string> { "title", "description", "newVideo" }
                            Required = new HashSet<string> { "file" }
                        }
                    }
                }
                };
            }
        }
    }
}
