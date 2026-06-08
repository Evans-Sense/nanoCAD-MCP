using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Teigha.Runtime;

namespace CadEngine
{
    public class PluginEntry : IExtensionApplication
    {
        private static readonly string LogPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "Temp", "ncad-mcp-engine-.log"
        );

        private HttpServer? _httpServer;
        private CancellationTokenSource? _cts;

        public void Initialize()
        {
            DebugLog("Plugin initializing...");

            try
            {
                _cts = new CancellationTokenSource();

                // Read port from environment or use default
                int port = 5080;
                var portStr = Environment.GetEnvironmentVariable("NANOCAD_MCP_PORT");
                if (!string.IsNullOrEmpty(portStr) && int.TryParse(portStr, out int customPort))
                {
                    port = customPort;
                }

                // Start HTTP server
                _httpServer = new HttpServer(port, _cts.Token);
                Task.Run(() => _httpServer.Start(), _cts.Token);

                // Capture the active document for background thread access
                CadContext.Capture();

                // Capture main thread synchronization context
                CadContext.MainSyncContext = SynchronizationContext.Current;
                DebugLog($"MainSyncContext={(CadContext.MainSyncContext != null ? CadContext.MainSyncContext.GetType().Name : "null")}");

                // Initialize MainThreadExecutor for MultiCAD API calls
                // Uses a polling timer (100ms) because Application.Idle doesn't
                // fire reliably from background threads in nanoCAD.
                MainThreadExecutor.Initialize();



                // Write port to temp file for auto-discovery
                var portFile = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "Temp", "ncad-mcp-port.txt"
                );
                File.WriteAllText(portFile, port.ToString());

                DebugLog($"Plugin initialized. HTTP server starting on port {port}");
            }
            catch (System.Exception ex)
            {
                DebugLog($"Plugin init error: {ex}");
                throw;
            }
        }

        public void Terminate()
        {
            DebugLog("Plugin terminating...");

            _cts?.Cancel();
            _cts?.Dispose();

            _httpServer?.Dispose();

            // Clear port file
            var portFile = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "Temp", "ncad-mcp-port.txt"
            );
            try { File.Delete(portFile); } catch { }

            DebugLog("Plugin terminated.");
        }

        public static void DebugLog(string message)
        {
            var line = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}] {message}";
            Debug.WriteLine(line);
            try
            {
                File.AppendAllText(LogPath, line + Environment.NewLine);
            }
            catch { }
        }
    }
}
