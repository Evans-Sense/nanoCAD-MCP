using System;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;
using Timer = System.Windows.Forms.Timer;

namespace CadEngine
{
    /// <summary>
    /// Dispatches actions to the main CAD thread using a producer-consumer queue.
    /// Background threads enqueue work items; the main thread processes them
    /// via a Windows Forms timer or explicit polling.
    /// </summary>
    public static class MainThread
    {
        private static readonly BlockingCollection<WorkItem> _queue = new();
        private static Timer? _timer;

        /// <summary>
        /// Initializes the polling timer on the main thread.
        /// Call once from PluginEntry.Initialize().
        /// </summary>
        public static void Initialize()
        {
            if (_timer != null) return;
            _timer = new Timer();
            _timer.Tick += (s, e) => ProcessQueue(null);
            _timer.Interval = 100; // poll every 100ms
            _timer.Start();
        }

        /// <summary>
        /// Queues an action to run on the main thread and blocks until completion.
        /// Returns true if the action completed; false on timeout or error.
        /// </summary>
        public static bool Execute(Action action, int timeoutMs = 60000)
        {
            var item = new WorkItem(action, timeoutMs);
            _queue.Add(item);
            return item.Wait();
        }

        /// <summary>
        /// Queues a function to run on the main thread and blocks until completion.
        /// Returns the result, or default(T) on timeout/error.
        /// </summary>
        public static T? Execute<T>(Func<T> func, int timeoutMs = 60000) where T : class
        {
            var item = new WorkItem<T>(func, timeoutMs);
            _queue.Add(item);
            return item.Wait();
        }

        /// <summary>
        /// Called from the polling timer on the main CAD thread
        /// to process all queued work items.
        /// </summary>
        private static void ProcessQueue(object? state)
        {
            while (_queue.TryTake(out var item))
            {
                try
                {
                    item.Execute();
                }
                catch (Exception ex)
                {
                    PluginEntry.DebugLog($"MainThread.ProcessQueue error: {ex.Message}");
                    item.Fail(ex);
                }
            }
        }

        // ─── Work item types ───

        private class WorkItem
        {
            private readonly Action _action;
            private readonly ManualResetEventSlim _done = new(false);
            private Exception? _exception;
            private readonly int _timeoutMs;

            public WorkItem(Action action, int timeoutMs)
            {
                _action = action;
                _timeoutMs = timeoutMs;
            }

            public bool Wait()
            {
                if (!_done.Wait(_timeoutMs))
                    return false;
                if (_exception != null)
                    throw _exception;
                return true;
            }

            public virtual void Execute()
            {
                try { _action(); _done.Set(); }
                catch (Exception ex) { _exception = ex; _done.Set(); }
            }

            public void Fail(Exception ex) { _exception = ex; _done.Set(); }
        }

        private class WorkItem<T> : WorkItem where T : class
        {
            private readonly Func<T> _func;
            private T? _result;

            public WorkItem(Func<T> func, int timeoutMs) : base(() => { }, timeoutMs)
            {
                _func = func;
            }

            public new T? Wait()
            {
                base.Wait();
                return _result;
            }

            public override void Execute()
            {
                try { _result = _func(); }
                catch (Exception ex) { PluginEntry.DebugLog($"WorkItem<T> error: {ex.Message}"); }
            }
        }
    }
}
