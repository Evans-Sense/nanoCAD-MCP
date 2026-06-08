using System;
using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;
using Teigha.Geometry;

namespace CadEngine
{
    public class PrimitiveService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;

        // ── Polygon ──────────────────────────────────────────
        public EntityDetailResponse CreatePolygon(PolygonRequest req)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var center = new Point3d(req.CenterX, req.CenterY, 0);
            double angle = 2 * Math.PI / req.Sides;
            double radius = req.Radius;

            var poly = new Polyline();
            for (int i = 0; i < req.Sides; i++)
            {
                double a = angle * i - Math.PI / 2;
                if (!req.Inscribed)
                {
                    // Circumscribed: radius = apothem, so vertex radius = R / cos(pi/N)
                    double vr = radius / Math.Cos(Math.PI / req.Sides);
                    poly.AddVertexAt(i, new Point2d(center.X + vr * Math.Cos(a), center.Y + vr * Math.Sin(a)), 0, 0, 0);
                }
                else
                {
                    poly.AddVertexAt(i, new Point2d(center.X + radius * Math.Cos(a), center.Y + radius * Math.Sin(a)), 0, 0, 0);
                }
            }
            poly.Closed = true;
            if (req.Layer != null) poly.Layer = req.Layer;
            ms.AppendEntity(poly);
            tr.AddNewlyCreatedDBObject(poly, true);
            tr.Commit();
            return new EntityDetailResponse { Handle = poly.Handle.Value.ToString("X"), Type = "POLYGON" };
        }

        // ── Donut ────────────────────────────────────────────
        public EntityDetailResponse CreateDonut(DonutRequest req)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var center = new Point3d(req.CenterX, req.CenterY, 0);
            var outer = new Circle(center, Vector3d.ZAxis, req.OuterRadius);
            var inner = new Circle(center, Vector3d.ZAxis, req.InnerRadius);
            if (req.Layer != null) { outer.Layer = req.Layer; inner.Layer = req.Layer; }

            var region = new DBObjectCollection();
            region.Add(outer);
            region.Add(inner);
            var regions = Teigha.DatabaseServices.Region.CreateFromCurves(region);
            if (regions != null && regions.Count > 0)
            {
                var donut = (Teigha.DatabaseServices.Region)regions[0];
                ms.AppendEntity(donut);
                tr.AddNewlyCreatedDBObject(donut, true);
                tr.Commit();
                return new EntityDetailResponse { Handle = donut.Handle.Value.ToString("X"), Type = "DONUT" };
            }
            tr.Abort();
            return new EntityDetailResponse { Handle = "", Type = "DONUT" };
        }

        // ── XLine ────────────────────────────────────────────
        public EntityDetailResponse CreateXLine(XLineRequest req)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var p1 = new Point3d(req.P1X, req.P1Y, 0);
            var p2 = new Point3d(req.P2X, req.P2Y, 0);
            var xline = new Xline();
            xline.BasePoint = p1;
            xline.UnitDir = (p2 - Point3d.Origin).GetNormal();
            if (req.Layer != null) xline.Layer = req.Layer;

            ms.AppendEntity(xline);
            tr.AddNewlyCreatedDBObject(xline, true);
            tr.Commit();
            return new EntityDetailResponse { Handle = xline.Handle.Value.ToString("X"), Type = "XLINE" };
        }

        // ── Ray ──────────────────────────────────────────────
        public EntityDetailResponse CreateRay(RayRequest req)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            var p1 = new Point3d(req.P1X, req.P1Y, 0);
            var p2 = new Point3d(req.P2X, req.P2Y, 0);
            var ray = new Ray { BasePoint = p1, UnitDir = (p2 - p1).GetNormal() };
            if (req.Layer != null) ray.Layer = req.Layer;

            ms.AppendEntity(ray);
            tr.AddNewlyCreatedDBObject(ray, true);
            tr.Commit();
            return new EntityDetailResponse { Handle = ray.Handle.Value.ToString("X"), Type = "RAY" };
        }
    }
}
