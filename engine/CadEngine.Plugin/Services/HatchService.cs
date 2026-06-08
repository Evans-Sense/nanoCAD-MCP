using System;
using System.Collections.Generic;
using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;
using Teigha.Geometry;

namespace CadEngine.Services
{
    public class HatchService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;

        public object CreateHatch(CreateHatchRequest req)
        {
            try
            {
                return MainThreadExecutor.Execute(() =>
                {
                    using var tr = Db.TransactionManager.StartTransaction();
                    var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                    var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                    var hatch = new Hatch();
                    string pattern = req.Pattern ?? "SOLID";
                    try
                    {
                        hatch.SetHatchPattern(HatchPatternType.PreDefined, pattern);
                    }
                    catch
                    {
                        // Predefined patterns (ANSI31 etc.) may not be available
                        // in nanoCAD free edition (no acad.pat file).
                        // Fall back to SOLID pattern which is always built-in.
                        PluginEntry.DebugLog($"HatchService: pattern '{pattern}' not available, falling back to SOLID");
                        pattern = "SOLID";
                        hatch.SetHatchPattern(HatchPatternType.PreDefined, "SOLID");
                    }
                    hatch.PatternScale = req.Scale;

                    if (req.BoundaryHandles != null && req.BoundaryHandles.Count > 0)
                    {
                        var edgeLoops = new ObjectIdCollection();
                        foreach (var handle in req.BoundaryHandles)
                        {
                            if (!long.TryParse(handle, System.Globalization.NumberStyles.HexNumber, null, out var h))
                                continue;
                            var id = Db.GetObjectId(false, new Handle(h), 0);
                            if (!id.IsNull) edgeLoops.Add(id);
                        }
                        if (edgeLoops.Count > 0)
                            hatch.AppendLoop(HatchLoopTypes.Default, edgeLoops);
                    }
                    else if (req.BoundaryPoints != null && req.BoundaryPoints.Count >= 3)
                    {
                        var loops = new ObjectIdCollection();
                        var poly = new Polyline();
                        for (int i = 0; i < req.BoundaryPoints.Count; i++)
                        {
                            var pt = req.BoundaryPoints[i];
                            poly.AddVertexAt(i, new Point2d(pt.X, pt.Y), 0, 0, 0);
                        }
                        poly.Closed = true;
                        poly.SetDatabaseDefaults();
                        ms.AppendEntity(poly);
                        tr.AddNewlyCreatedDBObject(poly, true);
                        loops.Add(poly.ObjectId);
                        hatch.AppendLoop(HatchLoopTypes.Default, loops);
                    }

                    hatch.SetDatabaseDefaults();
                    ms.AppendEntity(hatch);
                    tr.AddNewlyCreatedDBObject(hatch, true);

                    hatch.EvaluateHatch(true);

                    tr.Commit();

                    return (object)new { success = true, handle = hatch.Handle.Value.ToString("X"), type = "Hatch" };
                }) ?? new ErrorResponse { Error = "MainThreadExecutor returned null (timeout?)" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object GetHatchInfo(string handle)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var id = GetId(handle);
                if (id == null) return new ErrorResponse { Error = "Invalid handle" };

                var hatch = (Hatch)tr.GetObject(id.Value, OpenMode.ForRead);
                return new
                {
                    handle,
                    pattern = hatch.PatternName,
                    patternType = hatch.PatternType.ToString(),
                    scale = hatch.PatternScale,
                    loops = hatch.NumberOfLoops
                };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object EditHatch(string handle, EditHatchRequest req)
        {
            try
            {
                return MainThreadExecutor.Execute(() =>
                {
                    using var tr = Db.TransactionManager.StartTransaction();
                    var id = GetId(handle);
                    if (id == null) return (object)new ErrorResponse { Error = "Invalid handle" };

                    var hatch = (Hatch)tr.GetObject(id.Value, OpenMode.ForWrite);
                    if (req.Scale.HasValue) hatch.PatternScale = req.Scale.Value;
                    if (!string.IsNullOrEmpty(req.Pattern))
                        hatch.SetHatchPattern(HatchPatternType.PreDefined, req.Pattern);

                    hatch.EvaluateHatch(true);
                    tr.Commit();
                    return (object)new { success = true, handle };
                }) ?? new ErrorResponse { Error = "MainThreadExecutor returned null (timeout?)" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateGradientHatch(CreateGradientHatchRequest req)
        {
            try
            {
                return MainThreadExecutor.Execute(() =>
                {
                    using var tr = Db.TransactionManager.StartTransaction();
                    var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                    var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                    var hatch = new Hatch();
                    hatch.SetGradient(GradientPatternType.PreDefinedGradient, "LINEAR");

                    // Add boundary loops
                    if (req.BoundaryHandles != null && req.BoundaryHandles.Count > 0)
                    {
                        var edgeLoops = new ObjectIdCollection();
                        foreach (var handle in req.BoundaryHandles)
                        {
                            if (!long.TryParse(handle, System.Globalization.NumberStyles.HexNumber, null, out var h))
                                continue;
                            var id = Db.GetObjectId(false, new Handle(h), 0);
                            if (!id.IsNull) edgeLoops.Add(id);
                        }
                        if (edgeLoops.Count > 0)
                            hatch.AppendLoop(HatchLoopTypes.Default, edgeLoops);
                    }
                    else if (req.PointXs != null && req.PointYs != null && req.PointXs.Count >= 3)
                    {
                        var loops = new ObjectIdCollection();
                        var poly = new Polyline();
                        for (int i = 0; i < req.PointXs.Count; i++)
                        {
                            poly.AddVertexAt(i, new Point2d(req.PointXs[i], req.PointYs[i]), 0, 0, 0);
                        }
                        poly.Closed = true;
                        poly.SetDatabaseDefaults();
                        ms.AppendEntity(poly);
                        tr.AddNewlyCreatedDBObject(poly, true);
                        loops.Add(poly.ObjectId);
                        hatch.AppendLoop(HatchLoopTypes.Default, loops);
                    }

                    hatch.SetDatabaseDefaults();
                    ms.AppendEntity(hatch);
                    tr.AddNewlyCreatedDBObject(hatch, true);

                    hatch.EvaluateHatch(true);

                    tr.Commit();

                    return (object)new { success = true, handle = hatch.Handle.Value.ToString("X"), type = "GradientHatch" };
                }) ?? new ErrorResponse { Error = "MainThreadExecutor returned null (timeout?)" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        private static ObjectId? GetId(string handle)
        {
            if (!long.TryParse(handle, System.Globalization.NumberStyles.HexNumber, null, out var h))
                return null;
            try
            {
                var id = Db.GetObjectId(false, new Handle(h), 0);
                return id.IsNull ? null : id;
            }
            catch { return null; }
        }
    }

    public class CreateHatchRequest
    {
        public string? Pattern { get; set; } = "ANSI31";
        public double Scale { get; set; } = 1.0;
        public List<string>? BoundaryHandles { get; set; }
        public List<PointData>? BoundaryPoints { get; set; }
    }

    public class EditHatchRequest
    {
        public string? Pattern { get; set; }
        public double? Scale { get; set; }
    }

    public class PointData
    {
        public double X { get; set; }
        public double Y { get; set; }
    }

    // ── Gradient ────────────────────────────────────────────
    public class CreateGradientHatchRequest
    {
        public string? Color1 { get; set; } = "1,1,1";
        public string? Color2 { get; set; } = "0,0,0";
        public double Scale { get; set; } = 1.0;
        public string? GradientType { get; set; } = "linear";
        public List<string>? BoundaryHandles { get; set; }
        public List<double>? PointXs { get; set; }
        public List<double>? PointYs { get; set; }
    }
}
