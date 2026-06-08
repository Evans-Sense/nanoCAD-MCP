using System;
using System.Collections.Generic;
using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;
using Teigha.Geometry;

namespace CadEngine
{
    public class TransformationService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;

        private ObjectId? GetId(string h)
        {
            if (!long.TryParse(h, System.Globalization.NumberStyles.HexNumber, null, out var v)) return null;
            try { var id = Db.GetObjectId(false, new Handle(v), 0); return id.IsNull ? null : id; }
            catch { return null; }
        }

            // ── Trim ─────────────────────────────────────────────
        public EntitiesListResponse TrimEntity(TrimRequest req)
        {
            var result = new EntitiesListResponse();
            var id = GetId(req.Handle);
            if (id == null) return result;

            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
            if (ent is Curve curve)
            {
                var cutPt = new Point3d(req.CutX, req.CutY, 0);
                var closePt = curve.GetClosestPointTo(cutPt, false);
                var splitPts = new Point3dCollection { closePt };
                var splits = curve.GetSplitCurves(splitPts);

                if (splits.Count >= 1)
                {
                    int keepIdx = 0;
                    if (!req.KeepStart && splits.Count >= 2) keepIdx = 1;

                    for (int i = 0; i < splits.Count; i++)
                    {
                        if (splits[i] is Entity e)
                        {
                            if (i == keepIdx)
                            {
                                ms.AppendEntity(e);
                                tr.AddNewlyCreatedDBObject(e, true);
                                result.Entities.Add(new EntityDetailResponse
                                {
                                    Handle = e.Handle.Value.ToString("X"),
                                    Type = e.GetType().Name,
                                });
                            }
                            else e.Dispose();
                        }
                    }
                    ent.UpgradeOpen();
                    ent.Erase();
                }
                else
                {
                    foreach (DBObject obj in splits) obj.Dispose();
                }
            }
            tr.Commit();
            return result;
        }

        // ── Extend ────────────────────────────────────────────
        public SuccessResponse ExtendEntity(ExtendRequest req)
        {
            var id = GetId(req.Handle);
            if (id == null) return new SuccessResponse { Success = false };

            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForWrite);

            if (ent is Curve curve)
            {
                var endPt = new Point3d(req.EndX, req.EndY, 0);
                curve.Extend(false, endPt);
            }
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        // ── Offset ────────────────────────────────────────────
        public EntitiesListResponse OffsetEntity(OffsetRequest req)
        {
            var result = new EntitiesListResponse();
            var id = GetId(req.Handle);
            if (id == null) return result;

            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
            if (ent is Curve curve)
            {
                var geCurve = curve.GetGeCurve();
                var normal = Vector3d.ZAxis;
                var geOffset = geCurve.GetTrimmedOffset(
                    Math.Abs(req.Distance),
                    normal,
                    OffsetCurveExtensionType.Fillet);
                foreach (var geCrv in geOffset)
                {
                    var dbCurve = Curve.CreateFromGeCurve(geCrv);
                    if (dbCurve != null)
                    {
                        if (req.Distance < 0)
                        {
                            dbCurve.TransformBy(Matrix3d.Mirroring(new Point3d(0, 0, 0)));
                        }
                        ms.AppendEntity(dbCurve);
                        tr.AddNewlyCreatedDBObject(dbCurve, true);
                        result.Entities.Add(new EntityDetailResponse
                        {
                            Handle = dbCurve.Handle.Value.ToString("X"),
                            Type = dbCurve.GetType().Name,
                        });
                    }
                }
            }
            tr.Commit();
            return result;
        }

    // ── Stretch ──────────────────────────────────────────
        public SuccessResponse StretchEntity(StretchRequest req)
        {
            var id = GetId(req.Handle);
            if (id == null) return new SuccessResponse { Success = false };
            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForWrite);
            var indices = new IntegerCollection();
            var stretchPts = new Point3dCollection();
            ent.GetStretchPoints(stretchPts);
            // Move all stretch points
            for (int i = 0; i < stretchPts.Count; i++)
                indices.Add(i);
            ent.MoveStretchPointsAt(indices, new Vector3d(req.Dx, req.Dy, 0));
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        // ── Explode ──────────────────────────────────────────
        public EntitiesListResponse ExplodeEntity(string handle)
        {
            var result = new EntitiesListResponse();
            var id = GetId(handle);
            if (id == null) return result;

            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
            var exploded = new DBObjectCollection();
            ent.Explode(exploded);

            foreach (DBObject obj in exploded)
            {
                if (obj is Entity e)
                {
                    ms.AppendEntity(e);
                    tr.AddNewlyCreatedDBObject(e, true);
                    result.Entities.Add(new EntityDetailResponse
                    {
                        Handle = e.Handle.Value.ToString("X"),
                        Type = e.GetType().Name,
                        Layer = e.Layer,
                    });
                }
                else obj.Dispose();
            }

            ent.Erase();
            tr.Commit();
            return result;
        }

        // ── Divide ───────────────────────────────────────────
        public EntitiesListResponse DivideEntity(string handle, int segments)
        {
            var result = new EntitiesListResponse();
            var id = GetId(handle);
            if (id == null || segments < 2) return result;

            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
            if (ent is Curve curve)
            {
                for (int i = 1; i < segments; i++)
                {
                    double param = (double)i / segments;
                    var pt = new DBPoint(curve.GetPointAtParameter(curve.GetParameterAtDistance(curve.GetDistanceAtParameter(curve.StartParam) + param * curve.GetDistanceAtParameter(curve.EndParam))));
                    ms.AppendEntity(pt);
                    tr.AddNewlyCreatedDBObject(pt, true);
                    result.Entities.Add(new EntityDetailResponse
                    {
                        Handle = pt.Handle.Value.ToString("X"),
                        Type = "POINT",
                    });
                }
            }
            tr.Commit();
            return result;
        }

        // ── Measure ──────────────────────────────────────────
        public SuccessResponse MeasureEntity(string handle, double distance)
        {
            var id = GetId(handle);
            if (id == null) return new SuccessResponse { Success = false };

            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
            if (ent is Curve curve)
            {
                double totalLen = curve.GetDistanceAtParameter(curve.EndParam);
                double d = distance;
                while (d < totalLen)
                {
                    var pt = new DBPoint(curve.GetPointAtParameter(curve.GetParameterAtDistance(d)));
                    ms.AppendEntity(pt);
                    tr.AddNewlyCreatedDBObject(pt, true);
                    d += distance;
                }
            }
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        // ── Array3D (rectangular) ────────────────────────────
        public EntitiesListResponse Array3D(Array3DRequest req)
        {
            var result = new EntitiesListResponse();
            var id = GetId(req.Handle);
            if (id == null) return result;

            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var src = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);

            for (int i = 0; i < req.CountX; i++)
            {
                for (int j = 0; j < req.CountY; j++)
                {
                    for (int k = 0; k < req.CountZ; k++)
                    {
                        if (i == 0 && j == 0 && k == 0) continue;
                        var clone = (Entity)src.Clone();
                        clone.TransformBy(Matrix3d.Displacement(new Vector3d(i * req.SpacingX, j * req.SpacingY, k * req.SpacingZ)));
                        ms.AppendEntity(clone);
                        tr.AddNewlyCreatedDBObject(clone, true);
                        result.Entities.Add(new EntityDetailResponse
                        {
                            Handle = clone.Handle.Value.ToString("X"),
                            Type = clone.GetType().Name,
                        });
                    }
                }
            }
            tr.Commit();
            return result;
        }

        // ── Align3D ──────────────────────────────────────────
        public SuccessResponse Align3D(Align3DRequest req)
        {
            var id = GetId(req.Handle);
            if (id == null) return new SuccessResponse { Success = false };

            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForWrite);

            var srcP1 = new Point3d(req.SrcP1X, req.SrcP1Y, req.SrcP1Z);
            var srcP2 = new Point3d(req.SrcP2X, req.SrcP2Y, req.SrcP2Z);
            var srcP3 = new Point3d(req.SrcP3X, req.SrcP3Y, req.SrcP3Z);
            var dstP1 = new Point3d(req.DstP1X, req.DstP1Y, req.DstP1Z);
            var dstP2 = new Point3d(req.DstP2X, req.DstP2Y, req.DstP2Z);
            var dstP3 = new Point3d(req.DstP3X, req.DstP3Y, req.DstP3Z);

            var srcVx = new Vector3d(srcP2.X - srcP1.X, srcP2.Y - srcP1.Y, srcP2.Z - srcP1.Z);
            var srcVy = new Vector3d(srcP3.X - srcP1.X, srcP3.Y - srcP1.Y, srcP3.Z - srcP1.Z);
            var srcVz = srcVx.CrossProduct(srcVy);
            var dstVx = new Vector3d(dstP2.X - dstP1.X, dstP2.Y - dstP1.Y, dstP2.Z - dstP1.Z);
            var dstVy = new Vector3d(dstP3.X - dstP1.X, dstP3.Y - dstP1.Y, dstP3.Z - dstP1.Z);
            var dstVz = dstVx.CrossProduct(dstVy);

            var mat = Matrix3d.AlignCoordinateSystem(
                srcP1, srcVx, srcVy, srcVz,
                dstP1, dstVx, dstVy, dstVz);
            ent.TransformBy(mat);
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        // ── Mirror3D ─────────────────────────────────────────
        public SuccessResponse Mirror3D(Mirror3DRequest req)
        {
            var id = GetId(req.Handle);
            if (id == null) return new SuccessResponse { Success = false };

            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForWrite);

            var p1 = new Point3d(req.P1X, req.P1Y, req.P1Z);
            var p2 = new Point3d(req.P2X, req.P2Y, req.P2Z);
            var p3 = new Point3d(req.P3X, req.P3Y, req.P3Z);
            var plane = new Plane(p1, p2, p3);
            ent.TransformBy(Matrix3d.Mirroring(plane));
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        // ── 2D Constraints (command-based, not available in free edition) ──
        // All constraint methods return error gracefully instead of using
        // CadContext.SendCommand which would crash nanoCAD free edition
        // (GEOMCONSTRAINT is not supported, and SendStringToExecute exceptions
        //  are uncaught on the main thread).

        private SuccessResponse ConstraintNotAvailable()
        {
            return new SuccessResponse { Success = false, Error = "Geometric constraints not supported in this edition" };
        }

        public SuccessResponse ConstraintParallel(string handle1, string handle2) => ConstraintNotAvailable();
        public SuccessResponse ConstraintCoincident(string handle1, string handle2) => ConstraintNotAvailable();
        public SuccessResponse ConstraintFix(string handle) => ConstraintNotAvailable();
        public SuccessResponse ConstraintHorizontal(string handle) => ConstraintNotAvailable();
        public SuccessResponse ConstraintVertical(string handle) => ConstraintNotAvailable();
        public SuccessResponse ConstraintTangent(string handleLine, string handleCurve) => ConstraintNotAvailable();
        public SuccessResponse ConstraintPerpendicular(string handle1, string handle2) => ConstraintNotAvailable();
        public SuccessResponse ConstraintCollinear(string handle1, string handle2) => ConstraintNotAvailable();
        public SuccessResponse ConstraintConcentric(string handle1, string handle2) => ConstraintNotAvailable();
        public SuccessResponse ConstraintEqual(string handle1, string handle2) => ConstraintNotAvailable();
        public SuccessResponse ConstraintSymmetric(string handle1, string handle2, string handleLine) => ConstraintNotAvailable();
        public SuccessResponse ConstraintDistance(string handle1, string handle2, double distance) => ConstraintNotAvailable();
    }
}
