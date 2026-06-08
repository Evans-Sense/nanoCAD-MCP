using System;
using System.Collections.Generic;
using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;
using Teigha.Geometry;
using App = HostMgd.ApplicationServices.Application;

namespace CadEngine
{
    public class SolidService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;
        private static Document? GetDoc()
        {
            var db = HostApplicationServices.WorkingDatabase;
            if (db == null) return null;
            try { return App.DocumentManager.GetDocument(db); }
            catch { return null; }
        }
        private ObjectId? GetId(string h)
        {
            if (!long.TryParse(h, System.Globalization.NumberStyles.HexNumber, null, out var v)) return null;
            try { var id = Db.GetObjectId(false, new Handle(v), 0); return id.IsNull ? null : id; }
            catch { return null; }
        }
        private string MkSolid(Action<Solid3d> act)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
            var s = new Solid3d(); act(s);
            ms.AppendEntity(s); tr.AddNewlyCreatedDBObject(s, true); tr.Commit();
            using var tr2 = Db.TransactionManager.StartTransaction();
            return ((Entity)tr2.GetObject(s.ObjectId, OpenMode.ForRead)).Handle.Value.ToString("X");
        }
        public EntityResponse CreateBox(BoxRequest r) => new() { Handle = MkSolid(s => s.CreateBox(r.X, r.Y, r.Z)), Type = "SOLID3D" };
        public EntityResponse CreateSphere(SphereRequest r) => new() { Handle = MkSolid(s => s.CreateSphere(r.Radius)), Type = "SOLID3D" };
        public EntityResponse CreateCylinder(CylinderRequest r) => new() { Handle = MkSolid(s => s.CreateFrustum(r.Height, r.Radius, r.Radius, r.Radius)), Type = "SOLID3D" };
        public EntityResponse CreateCone(ConeRequest r) => new() { Handle = MkSolid(s => s.CreateFrustum(r.Height, r.RadiusBottom, r.RadiusBottom, 0)), Type = "SOLID3D" };
        public EntityResponse CreateTorus(TorusRequest r) => new() { Handle = MkSolid(s => s.CreateTorus(r.MajorRadius, r.MinorRadius)), Type = "SOLID3D" };
        public EntityResponse CreateWedge(WedgeRequest r) => new() { Handle = MkSolid(s => s.CreateWedge(r.X, r.Y, r.Z)), Type = "SOLID3D" };
        public EntityResponse CreatePyramid(PyramidRequest r) => new() { Handle = MkSolid(s => s.CreatePyramid(r.Height, r.Sides, r.Radius, 0)), Type = "SOLID3D" };
        private EntityResponse BoolOp(string h1, string h2, BooleanOperationType op)
        {
            var id1 = GetId(h1); var id2 = GetId(h2);
            if (id1 == null || id2 == null) return new EntityResponse { Handle = "", Type = "" };
            using var tr = Db.TransactionManager.StartTransaction();
            var s1 = (Solid3d)tr.GetObject(id1.Value, OpenMode.ForWrite);
            var s2 = (Solid3d)tr.GetObject(id2.Value, OpenMode.ForWrite);
            s1.BooleanOperation(op, s2); s2.Erase(); tr.Commit();
            using var tr2 = Db.TransactionManager.StartTransaction();
            var e = (Entity)tr2.GetObject(id1.Value, OpenMode.ForRead);
            return new EntityResponse { Handle = e.Handle.Value.ToString("X"), Type = "SOLID3D" };
        }
        public EntityResponse BooleanUnion(string h1, string h2) => BoolOp(h1, h2, BooleanOperationType.BoolUnite);
        public EntityResponse BooleanSubtract(string h1, string h2) => BoolOp(h1, h2, BooleanOperationType.BoolSubtract);
        public EntityResponse BooleanIntersect(string h1, string h2) => BoolOp(h1, h2, BooleanOperationType.BoolIntersect);
        public EntityResponse Extrude(ExtrudeRequest req)
        {
            var id = GetId(req.Handle);
            if (id == null) return new EntityResponse { Handle = "", Type = "" };
            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
            var crv = new DBObjectCollection();
            if (ent is Curve c) crv.Add(c);
            var reg = Teigha.DatabaseServices.Region.CreateFromCurves(crv);
            if (reg.Count == 0) throw new System.InvalidOperationException("No region");
            var s = new Solid3d(); s.Extrude((Teigha.DatabaseServices.Region)reg[0], req.Height, req.TaperAngle * Math.PI / 180.0);
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
            ms.AppendEntity(s); tr.AddNewlyCreatedDBObject(s, true); tr.Commit();
            using var tr2 = Db.TransactionManager.StartTransaction();
            return new EntityResponse { Handle = ((Entity)tr2.GetObject(s.ObjectId, OpenMode.ForRead)).Handle.Value.ToString("X"), Type = "SOLID3D" };
        }
        public EntityResponse Revolve(RevolveRequest req)
        {
            var id = GetId(req.Handle);
            if (id == null) return new EntityResponse { Handle = "", Type = "" };
            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
            var crv = new DBObjectCollection();
            if (ent is Curve c) crv.Add(c);
            var reg = Teigha.DatabaseServices.Region.CreateFromCurves(crv);
            if (reg.Count == 0) throw new System.InvalidOperationException("No region");
            var s = new Solid3d(); s.Revolve((Teigha.DatabaseServices.Region)reg[0], new Point3d(req.AxisX, req.AxisY, req.AxisZ), new Vector3d(req.DirX, req.DirY, req.DirZ), req.Angle * Math.PI / 180.0);
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
            ms.AppendEntity(s); tr.AddNewlyCreatedDBObject(s, true); tr.Commit();
            using var tr2 = Db.TransactionManager.StartTransaction();
            return new EntityResponse { Handle = ((Entity)tr2.GetObject(s.ObjectId, OpenMode.ForRead)).Handle.Value.ToString("X"), Type = "SOLID3D" };
        }
        public SuccessResponse MoveSolid(string h, double dx, double dy, double dz)
        {
            var id = GetId(h);
            if (id == null) return new SuccessResponse { Success = false };
            using var tr = Db.TransactionManager.StartTransaction();
            ((Entity)tr.GetObject(id.Value, OpenMode.ForWrite)).TransformBy(Matrix3d.Displacement(new Vector3d(dx, dy, dz)));
            tr.Commit(); return new SuccessResponse { Success = true };
        }
        public SuccessResponse RotateSolid(string h, double a, double cx, double cy, double cz, double ax, double ay, double az)
        {
            var id = GetId(h);
            if (id == null) return new SuccessResponse { Success = false };
            using var tr = Db.TransactionManager.StartTransaction();
            ((Entity)tr.GetObject(id.Value, OpenMode.ForWrite)).TransformBy(Matrix3d.Rotation(a * Math.PI / 180.0, new Vector3d(ax, ay, az), new Point3d(cx, cy, cz)));
            tr.Commit(); return new SuccessResponse { Success = true };
        }
        public SuccessResponse Set3dView(string dir, string rm)
        {
            // Use ViewTableRecord to change the view without SendCommand (which can crash).
            // This runs on the background thread but ViewTableRecord is safe from any thread.
            try
            {
                var db = HostApplicationServices.WorkingDatabase;
                if (db == null)
                    return new SuccessResponse { Success = false, Error = "No database" };
                var vtr = new ViewTableRecord();
                switch (dir.ToLowerInvariant())
                {
                    case "top": vtr.ViewDirection = new Vector3d(0, 0, 1); break;
                    case "bottom": vtr.ViewDirection = new Vector3d(0, 0, -1); break;
                    case "left": vtr.ViewDirection = new Vector3d(-1, 0, 0); break;
                    case "right": vtr.ViewDirection = new Vector3d(1, 0, 0); break;
                    case "front": vtr.ViewDirection = new Vector3d(0, 1, 0); break;
                    case "back": vtr.ViewDirection = new Vector3d(0, -1, 0); break;
                    case "sw": vtr.ViewDirection = new Vector3d(-1, -1, 1); break;
                    case "se": vtr.ViewDirection = new Vector3d(1, -1, 1); break;
                    case "nw": vtr.ViewDirection = new Vector3d(-1, 1, 1); break;
                    case "ne": vtr.ViewDirection = new Vector3d(1, 1, 1); break;
                    default: vtr.ViewDirection = new Vector3d(0, 0, 1); break;
                }
                vtr.Target = new Point3d(0, 0, 0);
                vtr.Height = 100;
                vtr.Width = 100;
                
                var doc = CadContext.ActiveDocument;
                if (doc != null)
                {
                    using var tr = db.TransactionManager.StartTransaction();
                    var vtm = (ViewTable)tr.GetObject(db.ViewTableId, OpenMode.ForRead);
                    foreach (ObjectId id in vtm)
                    {
                        var vt = (ViewTableRecord)tr.GetObject(id, OpenMode.ForWrite);
                        if (vt.Name == "*Active" || string.IsNullOrEmpty(vt.Name))
                        {
                            // Apply to the active (model space) view
                        }
                    }
                    tr.Commit();
                }
                
                // Also set via editor (main thread required for SetCurrentView)
                var result = MainThreadExecutor.Execute(() =>
                {
                    try
                    {
                        var ed = doc?.Editor;
                        if (ed != null)
                        {
                            ed.SetCurrentView(vtr);
                            return new SuccessResponse { Success = true };
                        }
                        return new SuccessResponse { Success = false, Error = "No editor" };
                    }
                    catch (Exception ex)
                    {
                        PluginEntry.DebugLog($"Set3dView (editor) failed: {ex.Message}");
                        return new SuccessResponse { Success = false, Error = ex.Message };
                    }
                });
                return result as SuccessResponse ?? new SuccessResponse { Success = false, Error = "Main thread executor returned null" };
            }
            catch (System.Exception ex)
            {
                PluginEntry.DebugLog($"Set3dView failed: {ex.Message}");
                return new SuccessResponse { Success = false, Error = ex.Message };
            }
        }
        public SuccessResponse ZoomExt()
        {
            // Use DocumentService.ZoomExtents which has safe SendCommand with try-catch
            return new DocumentService().ZoomExtents();
        }
        public SolidPropertiesResponse GetSolidProps(string h)
        {
            var id = GetId(h);
            if (id == null) return new SolidPropertiesResponse { Handle = h };
            using var tr = Db.TransactionManager.StartTransaction();
            var e = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
            if (e is Solid3d sol)
            {
                var mp = sol.MassProperties;
                return new SolidPropertiesResponse
                {
                    Handle = h,
                    Volume = mp.Volume,
                    Area = sol.Area,
                    CentroidX = mp.Centroid.X,
                    CentroidY = mp.Centroid.Y,
                    CentroidZ = mp.Centroid.Z,
                };
            }
            return new SolidPropertiesResponse { Handle = h };
        }

        // ── SWEEP / LOFT / FILLETEDGE / CHAMFEREDGE (command-based) ──
        // These commands require Plus/Pro edition and crash free edition via SendCommand.
        // Return graceful error instead.

        public SuccessResponse SweepSolid(string profileHandle, string pathHandle)
            => new SuccessResponse { Success = false, Error = "Sweep not supported in this edition" };

        public SuccessResponse LoftSolid(string[] sectionHandles)
            => new SuccessResponse { Success = false, Error = "Loft not supported in this edition" };

        public SuccessResponse FilletEdgeSolid(string solidHandle, double radius)
            => new SuccessResponse { Success = false, Error = "FilletEdge not supported in this edition" };

        public SuccessResponse ChamferEdgeSolid(string solidHandle, double dist1, double dist2)
            => new SuccessResponse { Success = false, Error = "ChamferEdge not supported in this edition" };

        // ── Assembly / Constraints (command-based) ──
        // These require Plus/Pro edition.

        public SuccessResponse InsertPart(string blockName, double x, double y, double z)
            => new SuccessResponse { Success = false, Error = "InsertPart not supported in this edition" };

        public SuccessResponse AssemblyMate(string handle1, string handle2)
            => new SuccessResponse { Success = false, Error = "Assembly mate not supported in this edition" };

        public SuccessResponse AssemblyAngle(string handle1, string handle2, double angle)
            => new SuccessResponse { Success = false, Error = "Assembly angle not supported in this edition" };

        public SuccessResponse AssemblyTangent(string handle1, string handle2)
            => new SuccessResponse { Success = false, Error = "Assembly tangent not supported in this edition" };

        public SuccessResponse AssemblySymmetry(string handle1, string handle2, string planeHandle)
            => new SuccessResponse { Success = false, Error = "Assembly symmetry not supported in this edition" };
    }
}