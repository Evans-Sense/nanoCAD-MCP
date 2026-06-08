using System;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;
using Timer = System.Windows.Forms.Timer;

namespace CadEngine
{
    /// <summary>
    /// Executes delegates on the main CAD thread via a polling timer.
    /// Required for MultiCAD API calls (McTable.PlaceObject, etc.) that
    /// cannot run on background threads even with LockDocument().
    /// 
    /// Note: nanoCAD's Application.Idle event does NOT fire reliably from
    /// background threads. Instead, we use a System.Windows.Forms.Timer
    /// that polls the queue every 100ms on the main thread.
    /// </summary>
    public static class MainThreadExecutor
    {
        private static readonly ConcurrentQueue<(Func<object?> Action, TaskCompletionSource<object?> Tcs)> _queue = new();
        private static Timer? _timer;
        private static readonly object _lock = new();

        /// <summary>
        /// Start the polling timer on the main CAD thread.
        /// Called once during plugin startup from PluginEntry.Initialize().
        /// </summary>
        public static void Initialize()
        {
            if (_timer != null) return;
            lock (_lock)
            {
                if (_timer != null) return;
                _timer = new Timer();
                _timer.Tick += (s, e) => ProcessQueue();
                _timer.Interval = 100; // poll every 100ms
                _timer.Start();
                PluginEntry.DebugLog("MainThreadExecutor initialized via polling timer (100ms)");
            }
        }

        /// <summary>
        /// Queue a delegate to execute on the main CAD thread.
        /// Blocks the calling thread until completion, with a timeout.
        /// </summary>
        /// <param name="action">Delegate to execute on main thread.</param>
        /// <param name="timeoutMs">Timeout in milliseconds (default 30000).</param>
        /// <returns>The result of the delegate, or null on timeout/error.</returns>
        public static object? Execute(Func<object?> action, int timeoutMs = 30000)
        {
            var tcs = new TaskCompletionSource<object?>();
            _queue.Enqueue((action, tcs));

            // Wake up the main thread by sending a no-op command
            try
            {
                var doc = CadContext.ActiveDocument;
                doc?.SendStringToExecute(" ", false, false, false);
            }
            catch { /* best effort */ }

            try
            {
                tcs.Task.Wait(timeoutMs);
                if (tcs.Task.IsCompletedSuccessfully)
                    return tcs.Task.Result;
                return null;
            }
            catch
            {
                return null;
            }
        }

        /// <summary>
        /// Async version — queue and await the result without blocking.
        /// </summary>
        public static Task<object?> ExecuteAsync(Func<object?> action, int timeoutMs = 30000)
        {
            var tcs = new TaskCompletionSource<object?>();
            _queue.Enqueue((action, tcs));
            try
            {
                var doc = CadContext.ActiveDocument;
                doc?.SendStringToExecute(" ", false, false, false);
            }
            catch { }
            return tcs.Task.WaitAsync(TimeSpan.FromMilliseconds(timeoutMs));
        }

        /// <summary>
        /// Process all queued items. Called by the polling timer on the main thread.
        /// Exceptions from actions are caught and returned to the waiting thread
        /// via the TaskCompletionSource.
        /// </summary>
        private static void ProcessQueue()
        {
            while (_queue.TryDequeue(out var item))
            {
                try
                {
                    var result = item.Action();
                    item.Tcs.TrySetResult(result);
                }
                catch (Exception ex)
                {
                    // The exception will be re-thrown on the waiting thread
                    // when it awaits the task.
                    item.Tcs.TrySetException(ex);
                }
            }
        }
    }
}
