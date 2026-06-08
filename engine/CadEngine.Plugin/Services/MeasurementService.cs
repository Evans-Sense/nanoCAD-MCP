using System;
using System.Collections.Generic;
using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;
using Teigha.Geometry;

namespace CadEngine.Services
{
    public class MeasurementService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;

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

        public object GetDistance(DistanceRequest req)
        {
            try
            {
                var p1 = new Point3d(req.X1, req.Y1, req.Z1);
                var p2 = new Point3d(req.X2, req.Y2, req.Z2);
                return new
                {
                    distance = p1.DistanceTo(p2),
                    dx = p2.X - p1.X,
                    dy = p2.Y - p1.Y,
                    dz = p2.Z - p1.Z
                };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object GetArea(string handle)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var id = GetId(handle);
                if (id == null) return new ErrorResponse { Error = "Invalid handle" };

                var obj = tr.GetObject(id.Value, OpenMode.ForRead);
                double area = obj switch
                {
                    Polyline pl => pl.Area,
                    Circle c => Math.PI * c.Radius * c.Radius,
                    Ellipse e => e.Area,
                    Hatch h => h.Area,
                    _ => throw new ArgumentException("Cannot calculate area for this entity type")
                };
                return new { handle, area };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object GetEntityInfo(string handle)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var id = GetId(handle);
                if (id == null) return new ErrorResponse { Error = "Invalid handle" };

                var ent = (Entity)tr.GetObject(id.Value, OpenMode.ForRead);
                var result = new Dictionary<string, object>
                {
                    ["handle"] = handle,
                    ["type"] = ent.GetType().Name,
                    ["layer"] = ent.Layer,
                    ["color"] = ent.Color.ToString(),
                    ["linetype"] = ent.Linetype
                };

                try
                {
                    var bounds = ent.GeometricExtents;
                    result["minX"] = bounds.MinPoint.X;
                    result["minY"] = bounds.MinPoint.Y;
                    result["maxX"] = bounds.MaxPoint.X;
                    result["maxY"] = bounds.MaxPoint.Y;
                }
                catch { }

                return result;
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object GetAllEntities()
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var btr = (BlockTableRecord)tr.GetObject(Db.CurrentSpaceId, OpenMode.ForRead);

                var entities = new List<object>();
                foreach (var id in btr)
                {
                    var obj = tr.GetObject(id, OpenMode.ForRead);
                    if (obj is Entity ent)
                    {
                        entities.Add(new
                        {
                            handle = ent.Handle.Value.ToString("X"),
                            type = ent.GetType().Name,
                            layer = ent.Layer
                        });
                    }
                }
                return new { count = entities.Count, entities };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object GetAngle(AngleRequest req)
        {
            try
            {
                var p1 = new Point3d(req.X1, req.Y1, req.Z1);
                var p2 = new Point3d(req.X2, req.Y2, req.Z2);
                var p3 = new Point3d(req.X3, req.Y3, req.Z3);

                var v1 = p1 - p2;
                var v2 = p3 - p2;
                var dot = v1.DotProduct(v2);
                var mag = v1.Length * v2.Length;
                if (Math.Abs(mag) < 1e-12)
                    return new ErrorResponse { Error = "Zero-length vectors" };

                double angleRad = Math.Acos(dot / mag);
                double angleDeg = angleRad * 180.0 / Math.PI;

                return new
                {
                    angle_radians = Math.Round(angleRad, 6),
                    angle_degrees = Math.Round(angleDeg, 4),
                    vertex = new { x = req.X2, y = req.Y2, z = req.Z2 },
                };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }
    }

    public class DistanceRequest
    {
        public double X1 { get; set; }
        public double Y1 { get; set; }
        public double Z1 { get; set; }
        public double X2 { get; set; }
        public double Y2 { get; set; }
        public double Z2 { get; set; }
    }

    public class AngleRequest
    {
        public double X1 { get; set; }
        public double Y1 { get; set; }
        public double Z1 { get; set; }
        public double X2 { get; set; }
        public double Y2 { get; set; }
        public double Z2 { get; set; }
        public double X3 { get; set; }
        public double Y3 { get; set; }
        public double Z3 { get; set; }
    }
}
