using BlazorRobot.Components;
using Dapper;
using MySqlConnector;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

builder.Services.AddHttpClient();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    app.UseHsts();
}

//app.UseHttpsRedirection();
app.UseAntiforgery();

app.MapStaticAssets();

// API endpoint
app.MapGet("/api/mine-data/latest", async (IConfiguration cfg, int limit = 200) =>
{
    var cs = cfg.GetConnectionString("JetbotDb");

    await using var conn = new MySqlConnection(cs);

    const string sql = @"
        SELECT id, mq_135, mq_4, x_coordinate, y_coordinate
        FROM mine_data
        ORDER BY id DESC
        LIMIT @limit;";

    var rows = await conn.QueryAsync<MineDataRow>(sql, new { limit });
    return rows.Reverse();
});

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();

record MineDataRow(int id, float mq_135, float mq_4, int x_coordinate, int y_coordinate);