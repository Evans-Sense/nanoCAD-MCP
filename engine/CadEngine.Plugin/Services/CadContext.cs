using System.Threading;
using HostMgd.ApplicationServices;
using App = HostMgd.ApplicationServices.Application;

namespace CadEngine
{
    /// <summary>
    /// Caches the active Document reference from the main (UI) thread
    /// during plugin initialization, so background HTTP threads can
    /// safely access document-level operations (Editor, SendStringToExecute, etc.).
    /// </summary>
    public static class CadContext
    {
        /// <summary>
        /// The active Document captured during plugin initialization (main thread).
        /// Use this from background threads instead of
        /// Application.DocumentManager.MdiActiveDocument (which returns null
        /// on background threads in some nanoCAD versions).
        /// </summary>
        public static Document? ActiveDocument { get; private set; }

        /// <summary>
        /// The SynchronizationContext from the main CAD thread.
        /// Use Send() to marshal calls that require the main thread
        /// (e.g. McTable.PlaceObject).
        /// </summary>
        public static SynchronizationContext? MainSyncContext { get; set; }

        /// <summary>
        /// Call once from PluginEntry.Initialize() (main thread).
        /// </summary>
        public static void Capture()
        {
            try
            {
                ActiveDocument = App.DocumentManager.MdiActiveDocument;
                PluginEntry.DebugLog($"CadContext.Capture: ActiveDocument={(ActiveDocument != null ? ActiveDocument.Name : "null")}");
            }
            catch (Exception ex)
            {
                PluginEntry.DebugLog($"CadContext.Capture error: {ex.Message}");
                ActiveDocument = null;
            }
        }

        /// <summary>
        /// Re-acquire the active document from the manager.
        /// Call after operations that destroy/recreate the document (e.g. NEW, QNEW).
        /// Only updates if MdiActiveDocument returns a non-null value (it may
        /// return null when called from background threads in some nanoCAD versions).
        /// </summary>
        public static void RefreshDocument()
        {
            try
            {
                var doc = App.DocumentManager.MdiActiveDocument;
                if (doc != null)
                    ActiveDocument = doc;
            }
            catch
            {
                // Keep existing ActiveDocument on error
            }
        }

        /// <summary>
        /// Attempts to execute a command string via the cached document's Editor.
        /// Returns true if the command was sent.
        /// </summary>
        public static bool SendCommand(string command)
        {
            var doc = ActiveDocument;
            if (doc == null) return false;
            try
            {
                doc.SendStringToExecute(command, true, false, true);
                return true;
            }
            catch
            {
                return false;
            }
        }
    }
}
