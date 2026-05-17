# Build Stage
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj and restore dependencies
COPY ["SalesSupportBackend/SalesSupportBackend.csproj", "SalesSupportBackend/SalesSupportBackend/"]
RUN dotnet restore "SalesSupportBackend/SalesSupportBackend.csproj"

# Copy everything else and build
COPY . .
WORKDIR "/src/SalesSupportBackend"
RUN dotnet build "SalesSupportBackend.csproj" -c Release -o /app/build

# Publish Stage
FROM build AS publish
RUN dotnet publish "SalesSupportBackend.csproj" -c Release -o /app/publish

# Final Runtime Stage
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "SalesSupportBackend.dll"]