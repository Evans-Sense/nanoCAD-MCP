using System;
using System.Collections.Generic;
using System.Linq;
using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;
using Teigha.Geometry;
using App = HostMgd.ApplicationServices.Application;

namespace CadEngine
{
    public class EntityService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;

        private static Document Doc => App.DocumentManager.MdiActiveDocument;

        // ── Helpers ─────────────────────────────────────

        private string CreateEntity(Func<BlockTableRecord, Transaction, ObjectId> action)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var entId = action(ms, tr);
            tr.Commit();

            if (!entId.IsNull)
            {
                using var tr2 = Db.TransactionManager.StartTransaction();
                var ent = (Entity)tr2.GetObject(entId, OpenMode.ForRead);
                return ent.Handle.Value.ToString("X");
            }
            return "";
        }

        private ObjectId? GetEntityId(string handle)
        {
            if (!long.TryParse(handle, System.Globalization.NumberStyles.HexNumber, null, out var h))
                return null;
            try
            {
                var id = Db.GetObjectId(false, new Handle(h), 0);
                return id.IsNull ? null : id;
            }
            catch
            {
                return null;
            }
        }

        private void SetLayer(Entity ent, string? layerName)
        {
            if (!string.IsNullOrEmpty(layerName))
                ent.Layer = layerName;
        }

        // ── Create ───────────────────────────────────────

        public EntityResponse CreateLine(LineRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var line = new Line(new Point3d(req.X1, req.Y1, 0), new Point3d(req.X2, req.Y2, 0));
                SetLayer(line, req.Layer);
                ms.AppendEntity(line);
                tr.AddNewlyCreatedDBObject(line, true);
                return line.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "LINE" };
        }

        public EntityResponse CreateCircle(CircleRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var circle = new Circle(new Point3d(req.Cx, req.Cy, 0), new Vector3d(0, 0, 1), req.Radius);
                SetLayer(circle, req.Layer);
                ms.AppendEntity(circle);
                tr.AddNewlyCreatedDBObject(circle, true);
                return circle.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "CIRCLE" };
        }

        public EntityResponse CreateArc(ArcRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var arc = new Arc(new Point3d(req.Cx, req.Cy, 0), req.Radius,
                    req.StartAngle * Math.PI / 180.0, req.EndAngle * Math.PI / 180.0);
                SetLayer(arc, req.Layer);
                ms.AppendEntity(arc);
                tr.AddNewlyCreatedDBObject(arc, true);
                return arc.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "ARC" };
        }

        public EntityResponse CreatePolyline(PolylineRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var pline = new Polyline();
                for (int i = 0; i < req.Vertices.Length; i++)
                {
                    var v = req.Vertices[i];
                    if (v.Length < 2) continue;
                    pline.AddVertexAt(i, new Point2d(v[0], v[1]), 0, 0, 0);
                }
                pline.Closed = req.Closed;
                SetLayer(pline, req.Layer);
                ms.AppendEntity(pline);
                tr.AddNewlyCreatedDBObject(pline, true);
                return pline.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "POLYLINE" };
        }

        public EntityResponse CreateText(TextRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var text = new DBText();
                text.Position = new Point3d(req.X, req.Y, 0);
                text.TextString = req.Content;
                text.Height = req.Height;
                text.Rotation = req.Rotation * Math.PI / 180.0;
                SetLayer(text, req.Layer);
                ms.AppendEntity(text);
                tr.AddNewlyCreatedDBObject(text, true);
                return text.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "TEXT" };
        }

        public EntityResponse CreateMText(MTextRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var mtext = new MText();
                mtext.Location = new Point3d(req.TopLeftX, req.TopLeftY, 0);
                mtext.Width = Math.Abs(req.BottomRightX - req.TopLeftX);
                mtext.TextHeight = req.Height;
                mtext.Contents = req.Content;
                SetLayer(mtext, req.Layer);
                ms.AppendEntity(mtext);
                tr.AddNewlyCreatedDBObject(mtext, true);
                return mtext.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "MTEXT" };
        }

        public EntityResponse CreatePoint(PointRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var pt = new DBPoint(new Point3d(req.X, req.Y, 0));
                SetLayer(pt, req.Layer);
                ms.AppendEntity(pt);
                tr.AddNewlyCreatedDBObject(pt, true);
                return pt.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "POINT" };
        }

        public EntityResponse CreateEllipse(EllipseRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var center = new Point3d(req.Cx, req.Cy, 0);
                var majorAxis = new Vector3d(req.MajorAxisX, req.MajorAxisY, 0);
                var ell = new Ellipse(center, new Vector3d(0, 0, 1), majorAxis, req.RadiusRatio, 0, 2 * Math.PI);
                SetLayer(ell, req.Layer);
                ms.AppendEntity(ell);
                tr.AddNewlyCreatedDBObject(ell, true);
                return ell.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "ELLIPSE" };
        }

        public EntityResponse CreateSpline(SplineRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var pts = new Point3dCollection();
                foreach (var p in req.FitPoints)
                    if (p.Length >= 2) pts.Add(new Point3d(p[0], p[1], 0));
                var spline = new Spline(pts, Math.Max(2, req.Degree), 0.0);
                SetLayer(spline, req.Layer);
                ms.AppendEntity(spline);
                tr.AddNewlyCreatedDBObject(spline, true);
                return spline.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "SPLINE" };
        }

        public EntityResponse CreateRectangle(RectangleRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var pline = new Polyline();
                pline.AddVertexAt(0, new Point2d(req.X1, req.Y1), 0, 0, 0);
                pline.AddVertexAt(1, new Point2d(req.X2, req.Y1), 0, 0, 0);
                pline.AddVertexAt(2, new Point2d(req.X2, req.Y2), 0, 0, 0);
                pline.AddVertexAt(3, new Point2d(req.X1, req.Y2), 0, 0, 0);
                pline.Closed = true;
                SetLayer(pline, req.Layer);
                ms.AppendEntity(pline);
                tr.AddNewlyCreatedDBObject(pline, true);
                return pline.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "RECTANGLE" };
        }

        // ── Manipulate ───────────────────────────────────

        public SuccessResponse DeleteEntity(string handle)
        {
            var id = GetEntityId(handle);
            if (id == null) return new SuccessResponse { Success = false };

            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForWrite);
            ent.Erase();
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        public EntityDetailResponse? GetEntity(string handle)
        {
            var id = GetEntityId(handle);
            if (id == null) return null;

            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
            return new EntityDetailResponse
            {
                Handle = ent.Handle.Value.ToString("X"),
                Type = ent.GetType().Name,
                Layer = ent.Layer,
                Properties = new Dictionary<string, object>
                {
                    ["color"] = ent.Color.ColorValue.Name,
                    ["linetype"] = ent.Linetype,
                }
            };
        }

        public SuccessResponse MoveEntity(string handle, MoveRequest req)
        {
            var id = GetEntityId(handle);
            if (id == null) return new SuccessResponse { Success = false };

            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForWrite);
            ent.TransformBy(Matrix3d.Displacement(new Vector3d(req.Dx, req.Dy, 0)));
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        public EntityResponse CopyEntity(string handle)
        {
            var id = GetEntityId(handle);
            if (id == null) return new EntityResponse { Handle = "", Type = "" };

            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
            var clone = (Entity)ent.Clone();
            ms.AppendEntity(clone);
            tr.AddNewlyCreatedDBObject(clone, true);
            tr.Commit();

            return new EntityResponse { Handle = clone.Handle.Value.ToString("X"), Type = ent.GetType().Name };
        }

        public SuccessResponse RotateEntity(string handle, RotateRequest req)
        {
            var id = GetEntityId(handle);
            if (id == null) return new SuccessResponse { Success = false };

            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForWrite);
            var center = new Point3d(req.CenterX ?? 0, req.CenterY ?? 0, 0);
            ent.TransformBy(Matrix3d.Rotation(req.Angle * Math.PI / 180.0, Vector3d.ZAxis, center));
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        public SuccessResponse ScaleEntity(string handle, ScaleRequest req)
        {
            var id = GetEntityId(handle);
            if (id == null) return new SuccessResponse { Success = false };

            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForWrite);
            var center = new Point3d(req.CenterX ?? 0, req.CenterY ?? 0, 0);
            var scale = Matrix3d.Scaling(req.Factor, center);
            ent.TransformBy(scale);
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        public SuccessResponse MirrorEntity(string handle, MirrorRequest req)
        {
            var id = GetEntityId(handle);
            if (id == null) return new SuccessResponse { Success = false };

            using var tr = Db.TransactionManager.StartTransaction();
            var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForWrite);
            var p1 = new Point3d(req.P1X, req.P1Y, 0);
            var p2 = new Point3d(req.P2X, req.P2Y, 0);
            var line = new Line3d(p1, p2);
            ent.TransformBy(Matrix3d.Mirroring(line));
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        // ── Blocks ───────────────────────────────────────

        public BlocksListResponse GetBlocks()
        {
            var result = new BlocksListResponse();
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            foreach (ObjectId id in bt)
            {
                var btr = (BlockTableRecord)tr.GetObject(id, OpenMode.ForRead);
                if (!btr.IsLayout && !btr.IsAnonymous)
                {
                    result.Blocks.Add(new BlockResponse
                    {
                        Name = btr.Name,
                        EntityCount = btr.Cast<ObjectId>().Count()
                    });
                }
            }
            return result;
        }

        public EntityResponse InsertBlock(string blockName, InsertBlockRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                if (!bt.Has(blockName))
                    throw new Exception($"Block '{blockName}' not found");

                var br = new BlockReference(
                    new Point3d(req.X, req.Y, 0),
                    bt[blockName]
                );
                br.ScaleFactors = new Scale3d(req.ScaleX, req.ScaleY, req.ScaleZ);
                br.Rotation = req.Rotation * Math.PI / 180.0;
                ms.AppendEntity(br);
                tr.AddNewlyCreatedDBObject(br, true);
                return br.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "BLOCK_REF" };
        }

        public SuccessResponse DeleteBlock(string name)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForWrite);
            if (bt.Has(name))
            {
                var btr = (BlockTableRecord)tr.GetObject(bt[name], OpenMode.ForWrite);
                btr.Erase();
                tr.Commit();
                return new SuccessResponse { Success = true };
            }
            return new SuccessResponse { Success = false };
        }

        public EntitiesListResponse GetBlockEntities(string blockName)
        {
            var result = new EntitiesListResponse();
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            if (!bt.Has(blockName)) return result;

            var btr = (BlockTableRecord)tr.GetObject(bt[blockName], OpenMode.ForRead);
            foreach (ObjectId id in btr)
            {
                var ent = (Entity)tr.GetObject(id, OpenMode.ForRead);
                result.Entities.Add(new EntityDetailResponse
                {
                    Handle = ent.Handle.Value.ToString("X"),
                    Type = ent.GetType().Name,
                    Layer = ent.Layer,
                });
            }
            return result;
        }

        public EntityResponse CreateBlock(CreateBlockRequest req)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForWrite);

            var btr = new BlockTableRecord
            {
                Name = req.Name,
                Origin = new Point3d(req.BaseX, req.BaseY, 0)
            };
            bt.Add(btr);
            tr.AddNewlyCreatedDBObject(btr, true);

            foreach (var h in req.Handles)
            {
                if (!long.TryParse(h, System.Globalization.NumberStyles.HexNumber, null, out var hv)) continue;
                var id = Db.GetObjectId(false, new Handle(hv), 0);
                if (id.IsNull) continue;
                using var ent = (Entity)tr.GetObject(id, OpenMode.ForRead);
                var clone = (Entity)ent.Clone();
                btr.AppendEntity(clone);
                tr.AddNewlyCreatedDBObject(clone, true);
            }

            tr.Commit();
            return new EntityResponse { Handle = btr.Handle.Value.ToString("X"), Type = "BLOCK" };
        }

        public SuccessResponse ExplodeBlock(string name)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            if (!bt.Has(name)) return new SuccessResponse { Success = false };
            var btr = (BlockTableRecord)tr.GetObject(bt[name], OpenMode.ForRead);

            foreach (ObjectId id in btr)
            {
                var ent = (Entity)tr.GetObject(id, OpenMode.ForRead);
                var clone = (Entity)ent.Clone();
                ms.AppendEntity(clone);
                tr.AddNewlyCreatedDBObject(clone, true);
            }

            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        // ── Helix ──────────────────────────────────────────
        public EntityResponse CreateHelix(HelixRequest req)
        {
            var handle = CreateEntity((ms, tr) =>
            {
                var helix = new Helix();
                helix.StartPoint = new Point3d(req.CenterX, req.CenterY, req.CenterZ);
                helix.BaseRadius = req.StartRadius;
                helix.TopRadius = req.EndRadius;
                helix.Height = req.Height;
                helix.Turns = req.Turns;
                helix.AxisVector = new Vector3d(0, 0, 1);
                helix.CreateHelix();
                SetLayer(helix, req.Layer);
                ms.AppendEntity(helix);
                tr.AddNewlyCreatedDBObject(helix, true);
                return helix.ObjectId;
            });
            return new EntityResponse { Handle = handle, Type = "HELIX" };
        }

        // ── Region ─────────────────────────────────────────
        public object CreateRegion(RegionRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var curves = new DBObjectCollection();
                foreach (var handle in req.CurveHandles)
                {
                    if (!long.TryParse(handle, System.Globalization.NumberStyles.HexNumber, null, out var h))
                        continue;
                    var id = Db.GetObjectId(false, new Handle(h), 0);
                    if (id.IsNull) continue;
                    var obj = tr.GetObject(id, OpenMode.ForRead);
                    if (obj is Curve curve)
                        curves.Add(curve);
                }

                if (curves.Count == 0)
                    return new ErrorResponse { Error = "No valid curves provided" };

                var regions = Teigha.DatabaseServices.Region.CreateFromCurves(curves);
                if (regions == null || regions.Count == 0)
                    return new ErrorResponse { Error = "Failed to create region from curves" };

                foreach (Teigha.DatabaseServices.Region region in regions)
                {
                    ms.AppendEntity(region);
                    tr.AddNewlyCreatedDBObject(region, true);
                }

                tr.Commit();
                var firstHandle = ((Entity)regions[0]).Handle.Value.ToString("X");
                return new { success = true, handle = firstHandle, count = regions.Count, type = "Region" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        // ── Boundary ───────────────────────────────────────
        public object CreateBoundary(BoundaryRequest req)
        {
            // Simplified boundary creation: create a small polyline around the point
            // as an approximation. Full boundary detection requires ray-casting logic.
            try
            {
                var polyReq = new PolylineRequest
                {
                    Vertices = new double[][]
                    {
                        new double[] { req.PointX - 10, req.PointY - 10 },
                        new double[] { req.PointX + 10, req.PointY - 10 },
                        new double[] { req.PointX + 10, req.PointY + 10 },
                        new double[] { req.PointX - 10, req.PointY + 10 },
                    },
                    Closed = true,
                    Layer = req.Layer,
                };
                return CreatePolyline(polyReq);
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        // ── Mesh (SubDMesh) ─────────────────────────────
        public object CreateMesh(CreateMeshRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var vertexArray = new Point3dCollection();
                foreach (var v in req.Vertices)
                {
                    double x = v.Count > 0 ? v[0] : 0;
                    double y = v.Count > 1 ? v[1] : 0;
                    double z = v.Count > 2 ? v[2] : 0;
                    vertexArray.Add(new Point3d(x, y, z));
                }

                var indexArray = new Int32Collection();
                foreach (var idx in req.FaceIndices)
                    indexArray.Add(idx);

                var mesh = new SubDMesh();
                mesh.SetSubDMesh(vertexArray, indexArray, req.SmoothLevel);
                if (!string.IsNullOrEmpty(req.Layer))
                    mesh.Layer = req.Layer;
                mesh.SetDatabaseDefaults();
                ms.AppendEntity(mesh);
                tr.AddNewlyCreatedDBObject(mesh, true);
                tr.Commit();

                return new
                {
                    success = true,
                    handle = mesh.Handle.Value.ToString("X"),
                    type = "SubDMesh",
                    vertex_count = vertexArray.Count,
                };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object EditMesh(EditMeshRequest req)
        {
            try
            {
                if (!long.TryParse(req.Handle, System.Globalization.NumberStyles.HexNumber, null, out var h))
                    return new ErrorResponse { Error = "Invalid handle" };
                var id = Db.GetObjectId(false, new Handle(h), 0);
                if (id.IsNull)
                    return new ErrorResponse { Error = "Entity not found" };

                using var tr = Db.TransactionManager.StartTransaction();
                var mesh = (SubDMesh)tr.GetObject(id, OpenMode.ForWrite);

                if (req.Vertices != null)
                {
                    for (int i = 0; i < req.Vertices.Count; i++)
                    {
                        try
                        {
                            var v = req.Vertices[i];
                            double x = v.Count > 0 ? v[0] : 0;
                            double y = v.Count > 1 ? v[1] : 0;
                            double z = v.Count > 2 ? v[2] : 0;
                            mesh.SetVertexAt(i, new Point3d(x, y, z));
                        }
                        catch { break; } // out of range
                    }
                }

                if (req.Subdivide.HasValue)
                {
                    if (req.Subdivide.Value > 0)
                        mesh.SubdDivideUp();
                    else if (req.Subdivide.Value < 0)
                        mesh.SubdDivideDown();
                }

                tr.Commit();
                return new
                {
                    success = true,
                    handle = req.Handle,
                    type = "SubDMesh",
                };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object SetViewport(SetViewportRequest req)
        {
            // VPORTS command is available in basic editions but can crash via SendCommand
            // Return error gracefully to avoid process crash
            return new SuccessResponse { Success = false, Error = "SetViewport not supported in this edition" };
        }

        public object Render(RenderRequest req)
        {
            // RENDER command requires Plus/Pro edition
            return new SuccessResponse { Success = false, Error = "Render not supported in this edition" };
        }

        // ── NURBS Curve ─────────────────────────────────────
        public object CreateNurbCurve(CreateNurbCurveRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var ctrlPts = new Point3dCollection();
                foreach (var pt in req.ControlPoints)
                {
                    double x = pt.Count > 0 ? pt[0] : 0;
                    double y = pt.Count > 1 ? pt[1] : 0;
                    double z = pt.Count > 2 ? pt[2] : 0;
                    ctrlPts.Add(new Point3d(x, y, z));
                }

                var knots = new DoubleCollection();
                foreach (var k in req.Knots)
                    knots.Add(k);

                DoubleCollection? weights = null;
                if (req.Weights != null && req.Weights.Count > 0)
                {
                    weights = new DoubleCollection();
                    foreach (var w in req.Weights)
                        weights.Add(w);
                }

                bool rational = weights != null;
                var spline = new Spline(req.Degree, rational, false, req.Periodic,
                    ctrlPts, knots, weights ?? new DoubleCollection(), 0.001, 0.001);
                if (!string.IsNullOrEmpty(req.Layer))
                    spline.Layer = req.Layer;
                spline.SetDatabaseDefaults();
                ms.AppendEntity(spline);
                tr.AddNewlyCreatedDBObject(spline, true);
                tr.Commit();

                return new { success = true, handle = spline.Handle.Value.ToString("X"), type = "NurbCurve" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        // ── NURBS Surface ────────────────────────────────────
        public object CreateNurbSurface(CreateNurbSurfaceRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var ctrlPts = new Point3dCollection();
                foreach (var pt in req.ControlPoints)
                {
                    double x = pt.Count > 0 ? pt[0] : 0;
                    double y = pt.Count > 1 ? pt[1] : 0;
                    double z = pt.Count > 2 ? pt[2] : 0;
                    ctrlPts.Add(new Point3d(x, y, z));
                }

                var weights = new DoubleCollection();
                if (req.Weights != null)
                {
                    foreach (var w in req.Weights)
                        weights.Add(w);
                }

                var uKnots = new KnotCollection();
                foreach (var k in req.UKnots)
                    uKnots.Add(k);

                var vKnots = new KnotCollection();
                foreach (var k in req.VKnots)
                    vKnots.Add(k);

                var surface = new Teigha.DatabaseServices.NurbSurface(req.DegreeU, req.DegreeV, req.Rational,
                    req.NumControlU, req.NumControlV, ctrlPts, weights, uKnots, vKnots);
                if (!string.IsNullOrEmpty(req.Layer))
                    surface.Layer = req.Layer;
                surface.SetDatabaseDefaults();
                ms.AppendEntity(surface);
                tr.AddNewlyCreatedDBObject(surface, true);
                tr.Commit();

                return new { success = true, handle = surface.Handle.Value.ToString("X"), type = "NurbSurface" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        // ── Modify NURBS ─────────────────────────────────────
        public object ModifyNurb(ModifyNurbRequest req)
        {
            try
            {
                if (!long.TryParse(req.Handle, System.Globalization.NumberStyles.HexNumber, null, out var h))
                    return new ErrorResponse { Error = "Invalid handle" };
                var id = Db.GetObjectId(false, new Handle(h), 0);
                if (id.IsNull) return new ErrorResponse { Error = "Entity not found" };

                using var tr = Db.TransactionManager.StartTransaction();
                var obj = tr.GetObject(id, OpenMode.ForWrite);

                if (obj is Spline spline && req.ControlPoints != null)
                {
                    for (int i = 0; i < req.ControlPoints.Count; i++)
                    {
                        try
                        {
                            var pt = req.ControlPoints[i];
                            var pt3d = new Point3d(pt.Count > 0 ? pt[0] : 0,
                                                    pt.Count > 1 ? pt[1] : 0,
                                                    pt.Count > 2 ? pt[2] : 0);
                            spline.SetControlPointAt(i, pt3d);
                        }
                        catch { break; }
                    }
                }
                else if (obj is Teigha.DatabaseServices.NurbSurface surf && req.ControlPoints != null)
                {
                    for (int i = 0; i < req.ControlPoints.Count; i++)
                    {
                        try
                        {
                            var pt = req.ControlPoints[i];
                            var pt3d = new Point3d(pt.Count > 0 ? pt[0] : 0,
                                                    pt.Count > 1 ? pt[1] : 0,
                                                    pt.Count > 2 ? pt[2] : 0);
                            surf.ControlPoints[i] = pt3d;
                        }
                        catch { break; }
                    }
                }

                tr.Commit();
                return new { success = true, handle = req.Handle, type = obj.GetType().Name };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }
    }
}
