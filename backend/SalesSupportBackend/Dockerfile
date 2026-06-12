# Build Stage
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy solution and project files
COPY SalesSupportBackend.sln .
COPY SalesSupportBackend/SalesSupportBackend.csproj SalesSupportBackend/
COPY UnitTest/UnitTest.csproj UnitTest/

# Restore dependencies
RUN dotnet restore SalesSupportBackend/SalesSupportBackend.csproj

# Copy everything else and build
COPY . .
WORKDIR "/src/SalesSupportBackend"
RUN dotnet build "SalesSupportBackend.csproj" -c Release -o /app/build

# Publish Stage
FROM build AS publish
RUN dotnet publish "SalesSupportBackend.csproj" -c Release -o /app/publish --no-restore

# Final Runtime Stage
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=publish /app/publish .

# Set environment
ENV PORT=5132

EXPOSE 5132

ENTRYPOINT ["dotnet", "SalesSupportBackend.dll"]
