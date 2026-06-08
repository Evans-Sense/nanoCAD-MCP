using System;
using System.Linq;
using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;
using Teigha.Geometry;
using App = HostMgd.ApplicationServices.Application;

namespace CadEngine
{
    public class DocumentService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;

        public DocumentInfoResponse GetInfo()
        {
            var db = Db;
            if (db == null) throw new Exception("WorkingDatabase is null");

            var fileName = db.Filename;
            var info = new DocumentInfoResponse
            {
                Name = System.IO.Path.GetFileName(fileName),
                Path = fileName,
                IsSaved = !string.IsNullOrEmpty(fileName),
            };

            using var tr = db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(db.CurrentSpaceId, OpenMode.ForRead);

            var entityCount = 0;
            foreach (ObjectId id in ms) entityCount++;
            info.EntitiesCount = entityCount;

            var lt = (LayerTable)tr.GetObject(db.LayerTableId, OpenMode.ForRead);
            info.LayersCount = lt.Cast<ObjectId>().Count();

            var blockCount = 0;
            foreach (ObjectId id in bt)
            {
                var btr = (BlockTableRecord)tr.GetObject(id, OpenMode.ForRead);
                if (!btr.IsLayout && !btr.IsAnonymous) blockCount++;
            }
            info.BlocksCount = blockCount;

            return info;
        }

        public SuccessResponse Save(string? path)
        {
            // Normalize backslashes to forward slashes for JSON safety
            var normalizedPath = path?.Replace("\\", "/");

            try
            {
                var doc = CadContext.ActiveDocument;
                if (doc == null)
                {
                    // Cannot save without a cached document reference.
                    // Avoid _QSAVE / _SAVEAS via SendCommand as they can open dialogs or crash.
                    PluginEntry.DebugLog("Save failed: no active document reference");
                    return new SuccessResponse { Success = false, Error = "No active document reference for save" };
                }

                if (!string.IsNullOrEmpty(normalizedPath))
                {
                    // Use synchronous Database.SaveAs — must run on main thread.
                    var result = MainThreadExecutor.Execute(() =>
                    {
                        try
                        {
                            // Ensure directory exists
                            var dir = System.IO.Path.GetDirectoryName(normalizedPath);
                            if (!string.IsNullOrEmpty(dir) && !System.IO.Directory.Exists(dir))
                                System.IO.Directory.CreateDirectory(dir);

                            // SaveAs(format, fileName) — format 2024 = DWG 2024 (default for nanoCAD)
                            doc.Database.SaveAs(normalizedPath, true, DwgVersion.Current, null);
                            return (object)new SuccessResponse { Success = true };
                        }
                        catch (Exception ex)
                        {
                            PluginEntry.DebugLog($"Save As error: {ex.Message}");
                            return (object)new SuccessResponse { Success = false, Error = ex.Message };
                        }
                    });
                    return result as SuccessResponse ?? new SuccessResponse { Success = false, Error = "Main thread executor returned null" };
                }
                else
                {
                    // Save to current file path via MainThreadExecutor (avoid _QSAVE dialog)
                    var currentPath = doc.Name;
                    if (string.IsNullOrEmpty(currentPath) || currentPath.EndsWith(".dwt"))
                    {
                        PluginEntry.DebugLog("Save failed: document has no file path");
                        return new SuccessResponse { Success = false, Error = "Document has no file path; provide a path" };
                    }
                    var result = MainThreadExecutor.Execute(() =>
                    {
                        try
                        {
                            doc.Database.SaveAs(currentPath, true, DwgVersion.Current, null);
                            return (object?)new SuccessResponse { Success = true };
                        }
                        catch (Exception ex)
                        {
                            PluginEntry.DebugLog($"Save (existing path) error: {ex.Message}");
                            return (object?)new SuccessResponse { Success = false, Error = ex.Message };
                        }
                    });
                    return result as SuccessResponse ?? new SuccessResponse { Success = false, Error = "Main thread executor returned null" };
                }
            }
            catch (Exception ex)
            {
                PluginEntry.DebugLog($"Save error: {ex.Message}");
                return new SuccessResponse { Success = false, Error = ex.Message };
            }
        }

        public SuccessResponse ExportPdf(string path)
        {
            // Try COM-based export first. Avoid _PLOT command as it opens
            // a modal dialog and blocks/crashes the background thread.
            try
            {
                var acad = App.AcadApplication;
                if (acad != null)
                {
                    var comDoc = acad.GetType().InvokeMember("ActiveDocument",
                        System.Reflection.BindingFlags.GetProperty, null, acad, null);
                    if (comDoc != null)
                    {
                        comDoc.GetType().InvokeMember("ExportAs",
                            System.Reflection.BindingFlags.InvokeMethod, null, comDoc,
                            new object[] { path, 102 });
                        return new SuccessResponse { Success = true };
                    }
                }
            }
            catch { }
            // _PLOT opens modal dialog — DO NOT USE from background thread
            return new SuccessResponse { Success = false, Error = "PDF export requires COM access (not available in free edition)" };
        }

        public SuccessResponse ExportDwg(string path)
        {
            // Reuse Save method which handles MainThreadExecutor + edge cases safely
            return Save(path);
        }

        public SuccessResponse ExportDxf(string path)
        {
            // Use MainThreadExecutor for Database.DxfOut (requires database lock)
            var result = MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var db = HostApplicationServices.WorkingDatabase;
                    if (db == null) return (object?)new SuccessResponse { Success = false, Error = "No working database" };
                    db.DxfOut(path, 16, false);
                    return (object?)new SuccessResponse { Success = true };
                }
                catch (Exception ex)
                {
                    PluginEntry.DebugLog($"ExportDxf failed: {ex.Message}");
                    return (object?)new SuccessResponse { Success = false, Error = ex.Message };
                }
            });
            return result as SuccessResponse ?? new SuccessResponse { Success = false, Error = "Main thread executor returned null" };
        }

        public SuccessResponse ZoomExtents()
        {
            try
            {
                var doc = CadContext.ActiveDocument;
                if (doc == null)
                    return new SuccessResponse { Success = false, Error = "No active document" };
                var result = MainThreadExecutor.Execute(() =>
                {
                    try
                    {
                        var ed = doc.Editor;
                        // Zoom to extents via ViewTableRecord
                        var db = HostApplicationServices.WorkingDatabase;
                        if (db == null)
                            return (object?)new SuccessResponse { Success = false, Error = "No database" };
                        using var tr = db.TransactionManager.StartTransaction();
                        double minX = double.MaxValue, minY = double.MaxValue, maxX = double.MinValue, maxY = double.MinValue;
                        bool hasEntities = false;
                        var bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
                        var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForRead);
                        foreach (ObjectId id in ms)
                        {
                            var ent = (Entity)tr.GetObject(id, OpenMode.ForRead);
                            try
                            {
                                var ext = ent.GeometricExtents;
                                if (ext.MinPoint.X < minX) minX = ext.MinPoint.X;
                                if (ext.MinPoint.Y < minY) minY = ext.MinPoint.Y;
                                if (ext.MaxPoint.X > maxX) maxX = ext.MaxPoint.X;
                                if (ext.MaxPoint.Y > maxY) maxY = ext.MaxPoint.Y;
                                hasEntities = true;
                            }
                            catch { }
                        }
                        tr.Commit();
                        // Create ViewTableRecord with computed extents and apply via SetCurrentView
                        var vtr = new ViewTableRecord();
                        if (hasEntities)
                        {
                            double marginX = (maxX - minX) * 0.1;
                            double marginY = (maxY - minY) * 0.1;
                            if (marginX < 1) marginX = 1;
                            if (marginY < 1) marginY = 1;
                            vtr.Target = new Point3d((minX + maxX) / 2, (minY + maxY) / 2, 0);
                            vtr.Height = (maxY - minY) + 2 * marginY;
                            vtr.Width = (maxX - minX) + 2 * marginX;
                        }
                        else
                        {
                            vtr.Target = new Point3d(0, 0, 0);
                            vtr.Height = 100;
                            vtr.Width = 100;
                        }
                        vtr.ViewDirection = new Vector3d(0, 0, 1);
                        ed.SetCurrentView(vtr);
                        return (object?)new SuccessResponse { Success = true };
                    }
                    catch (Exception ex)
                    {
                        PluginEntry.DebugLog($"ZoomExtents (editor) failed: {ex.Message}");
                        return (object?)new SuccessResponse { Success = false, Error = ex.Message };
                    }
                });
                return result as SuccessResponse ?? new SuccessResponse { Success = false, Error = "Main thread executor returned null" };
            }
            catch (System.Exception ex)
            {
                PluginEntry.DebugLog($"ZoomExtents failed: {ex.Message}");
                return new SuccessResponse { Success = false, Error = ex.Message };
            }
        }

        public SuccessResponse NewDocument(string? template = null, string? savePath = null)
        {
            // Use MainThreadExecutor to create a new document via DocumentManager.Add(),
            // avoiding _QNEW which destroys the current document (and with it, the plugin).
            var result = MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var dm = App.DocumentManager;
                    string tpl = !string.IsNullOrEmpty(template) ? template : "acadiso.dwt";
                    var doc = dm.Add(tpl);
                    dm.MdiActiveDocument = doc;
                    return (object?)new { success = true };
                }
                catch (Exception ex)
                {
                    // DO NOT fallback to _QNEW — it destroys the document AND the plugin
                    PluginEntry.DebugLog($"DocumentManager.Add failed: {ex.Message}");
                    return (object?)new { success = false, error = $"New document failed: {ex.Message}" };
                }
            });

            // Refresh CadContext after document was created on main thread
            CadContext.RefreshDocument();

            // If savePath provided, save the new document to that path.
            if (!string.IsNullOrEmpty(savePath))
            {
                return Save(savePath);
            }
            return new SuccessResponse { Success = true };
        }

        public SuccessResponse Undo()
        {
            // Use MainThreadExecutor to run synchronous Editor.Command on main thread
            var result = MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var doc = CadContext.ActiveDocument;
                    if (doc == null)
                        return (object?)new SuccessResponse { Success = false, Error = "No active document" };
                    // Editor.Command is synchronous — exceptions are caught by this try block
                    doc.Editor.Command("_UNDO", "1");
                    return (object?)new SuccessResponse { Success = true };
                }
                catch (Exception ex)
                {
                    PluginEntry.DebugLog($"Undo failed: {ex.Message}");
                    return (object?)new SuccessResponse { Success = false, Error = ex.Message };
                }
            });
            return result as SuccessResponse ?? new SuccessResponse { Success = false, Error = "Main thread executor returned null" };
        }

        public SuccessResponse Redo()
        {
            var result = MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var doc = CadContext.ActiveDocument;
                    if (doc == null)
                        return (object?)new SuccessResponse { Success = false, Error = "No active document" };
                    doc.Editor.Command("_REDO");
                    return (object?)new SuccessResponse { Success = true };
                }
                catch (Exception ex)
                {
                    PluginEntry.DebugLog($"Redo failed: {ex.Message}");
                    return (object?)new SuccessResponse { Success = false, Error = ex.Message };
                }
            });
            return result as SuccessResponse ?? new SuccessResponse { Success = false, Error = "Main thread executor returned null" };
        }

        public SuccessResponse Open(string path)
        {
            if (string.IsNullOrEmpty(path))
                return new SuccessResponse { Success = false, Error = "Path is required" };
            // Validate path exists
            if (!System.IO.File.Exists(path))
            {
                PluginEntry.DebugLog($"Open failed: file not found '{path}'");
                return new SuccessResponse { Success = false, Error = "File not found" };
            }
            // Use MainThreadExecutor to open via DocumentManager.Open (avoids _OPEN SendCommand crash)
            var result = MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var dm = App.DocumentManager;
                    dm.Open(path);
                    CadContext.RefreshDocument();
                    return (object?)new SuccessResponse { Success = true };
                }
                catch (Exception ex)
                {
                    PluginEntry.DebugLog($"Open failed: {ex.Message}");
                    return (object?)new SuccessResponse { Success = false, Error = ex.Message };
                }
            });
            return result as SuccessResponse ?? new SuccessResponse { Success = false, Error = "Main thread executor returned null" };
        }

        public SuccessResponse Close()
        {
            // Use MainThreadExecutor to close via Document.CloseAndDiscard (avoids _CLOSE SendCommand crash)
            var result = MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var doc = CadContext.ActiveDocument;
                    if (doc == null)
                        return (object?)new SuccessResponse { Success = false, Error = "No active document to close" };
                    doc.CloseAndDiscard();
                    CadContext.RefreshDocument();
                    return (object?)new SuccessResponse { Success = true };
                }
                catch (Exception ex)
                {
                    PluginEntry.DebugLog($"Close failed: {ex.Message}");
                    return (object?)new SuccessResponse { Success = false, Error = ex.Message };
                }
            });
            return result as SuccessResponse ?? new SuccessResponse { Success = false, Error = "Main thread executor returned null" };
        }

        public SuccessResponse Purge()
        {
            var result = MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var doc = CadContext.ActiveDocument;
                    if (doc == null)
                        return (object?)new SuccessResponse { Success = false, Error = "No active document" };
                    // Editor.Command is synchronous — exceptions are caught here
                    doc.Editor.Command("_PURGE", "A", "*", "N");
                    return (object?)new SuccessResponse { Success = true };
                }
                catch (Exception ex)
                {
                    PluginEntry.DebugLog($"Purge failed: {ex.Message}");
                    return (object?)new SuccessResponse { Success = false, Error = ex.Message };
                }
            });
            return result as SuccessResponse ?? new SuccessResponse { Success = false, Error = "Main thread executor returned null" };
        }

        public SuccessResponse ImportStep(string path)
        {
            // IMPORTSTEP is not available in nanoCAD free edition
            // Avoid SendCommand as it may trigger dialogs and crash the plugin
            PluginEntry.DebugLog($"ImportStep not available in this edition");
            return new SuccessResponse { Success = false, Error = "STEP import not supported in this edition" };
        }

        public SuccessResponse ExportStep(string path)
        {
            // EXPORTSTEP is not available in nanoCAD free edition
            PluginEntry.DebugLog($"ExportStep not available in this edition");
            return new SuccessResponse { Success = false, Error = "STEP export not supported in this edition" };
        }

        public SuccessResponse ExportIfc(string path)
        {
            // IFC export requires Plus/Pro edition
            PluginEntry.DebugLog($"ExportIfc not available in this edition");
            return new SuccessResponse { Success = false, Error = "IFC export not supported in this edition" };
        }

        public object ImportIfc(string path)
        {
            // IFC import requires Plus/Pro edition — _MCIMPORTIFC may crash free edition
            if (string.IsNullOrEmpty(path))
                return new { success = false, error = "Path is required" };
            PluginEntry.DebugLog($"ImportIfc not available in this edition");
            return new { success = false, error = "IFC import not supported in this edition" };
        }

        public object GetIfcEntities()
        {
            try
            {
                var db = Db;
                if (db == null) return new { success = false, error = "No active document" };

                using var tr = db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForRead);

                var result = new List<object>();
                foreach (var id in ms)
                {
                    var ent = tr.GetObject(id, OpenMode.ForRead) as Entity;
                    if (ent == null) continue;
                    var typeName = ent.GetType().Name;
                    // Detect IFC-related custom objects by type name pattern
                    bool isIfc = typeName.Contains("Ifc", StringComparison.OrdinalIgnoreCase) ||
                                 typeName.Contains("MechPart", StringComparison.OrdinalIgnoreCase) ||
                                 typeName.Contains("McBuilding", StringComparison.OrdinalIgnoreCase) ||
                                 typeName.Contains("McStory", StringComparison.OrdinalIgnoreCase) ||
                                 typeName.Contains("McSpace", StringComparison.OrdinalIgnoreCase) ||
                                 typeName.Contains("McWall", StringComparison.OrdinalIgnoreCase) ||
                                 typeName.Contains("McSlab", StringComparison.OrdinalIgnoreCase) ||
                                 typeName.Contains("McBeam", StringComparison.OrdinalIgnoreCase) ||
                                 typeName.Contains("McColumn", StringComparison.OrdinalIgnoreCase) ||
                                 typeName.Contains("McOpening", StringComparison.OrdinalIgnoreCase);
                    if (isIfc)
                    {
                        result.Add(new
                        {
                            handle = ent.Handle.Value.ToString("X"),
                            type = typeName,
                            layer = ent.Layer,
                            visible = ent.Visible
                        });
                    }
                }
                tr.Commit();
                return new { success = true, entities = result, count = result.Count };
            }
            catch (Exception ex)
            {
                return new { success = false, error = ex.Message };
            }
        }

        // ── Get Angle ──────────────────────────────────────
        public object GetAngle(double x1, double y1, double z1,
                               double x2, double y2, double z2,
                               double x3, double y3, double z3)
        {
            try
            {
                var p1 = new Point3d(x1, y1, z1);
                var p2 = new Point3d(x2, y2, z2);
                var p3 = new Point3d(x3, y3, z3);
                var v1 = new Vector3d(p1.X - p2.X, p1.Y - p2.Y, p1.Z - p2.Z);
                var v2 = new Vector3d(p3.X - p2.X, p3.Y - p2.Y, p3.Z - p2.Z);
                double angle = v1.GetAngleTo(v2);
                double angleDeg = angle * 180.0 / Math.PI;
                return new { success = true, angleRad = angle, angleDeg = angleDeg };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        // ── Get System Fonts ────────────────────────────────
        public object GetSystemFonts()
        {
            try
            {
                var fonts = new System.Drawing.Text.InstalledFontCollection();
                var names = new List<string>();
                foreach (var f in fonts.Families)
                    names.Add(f.Name);
                return new { success = true, fonts = names, count = names.Count };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        // ── Get Linetypes ───────────────────────────────────
        public object GetLinetypes()
        {
            try
            {
                var db = Db;
                if (db == null) return new { success = false, error = "No active document" };
                using var tr = db.TransactionManager.StartTransaction();
                var lt = (LinetypeTable)tr.GetObject(db.LinetypeTableId, OpenMode.ForRead);
                var result = new List<object>();
                foreach (var id in lt)
                {
                    var entry = tr.GetObject(id, OpenMode.ForRead) as LinetypeTableRecord;
                    if (entry == null) continue;
                    result.Add(new
                    {
                        name = entry.Name,
                        description = entry.Comments ?? ""
                    });
                }
                tr.Commit();
                return new { success = true, linetypes = result, count = result.Count };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        // ── Open Document ───────────────────────────────────
        public object OpenDocument(string path)
        {
            try
            {
                if (!System.IO.File.Exists(path))
                    return new { success = false, error = "File not found: " + path };
                var dm = App.DocumentManager;
                dm.Open(path);
                return new { success = true };
            }
            catch (Exception ex)
            {
                return new { success = false, error = ex.Message };
            }
        }

        // ── Close Document ──────────────────────────────────
        public object CloseDocument()
        {
            try
            {
                var dm = App.DocumentManager;
                var doc = dm.MdiActiveDocument;
                if (doc == null)
                    return new { success = false, error = "No active document" };
                doc.CloseAndDiscard();
                return new { success = true };
            }
            catch (Exception ex)
            {
                return new { success = false, error = ex.Message };
            }
        }

        public SuccessResponse ExportStl(string path, bool binary = true)
        {
            // STL export via _STLOUT command may trigger dialogs — use MainThreadExecutor
            // to safely execute on the main thread.
            PluginEntry.DebugLog($"ExportStl not available in free edition");
            return new SuccessResponse { Success = false, Error = "STL export not available in free edition" };
        }
    }
}
