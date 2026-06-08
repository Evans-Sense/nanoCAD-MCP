using System;
using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;
using Teigha.Geometry;

namespace CadEngine.Services
{
    public class DimensionService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;

        public object CreateAlignedDimension(CreateAlignedDimRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var p1 = new Point3d(req.X1, req.Y1, 0);
                var p2 = new Point3d(req.X2, req.Y2, 0);
                var dimLinePt = new Point3d(req.DimX, req.DimY, 0);

                var dim = new AlignedDimension(p1, p2, dimLinePt, null, Db.Dimstyle);
                dim.SetDatabaseDefaults();
                ms.AppendEntity(dim);
                tr.AddNewlyCreatedDBObject(dim, true);
                tr.Commit();

                return new { success = true, handle = dim.Handle.Value.ToString("X"), type = "AlignedDimension" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateRotatedDimension(CreateRotatedDimRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var p1 = new Point3d(req.X1, req.Y1, 0);
                var p2 = new Point3d(req.X2, req.Y2, 0);
                var dimLinePt = new Point3d(req.DimX, req.DimY, 0);

                var dim = new RotatedDimension(req.Rotation * Math.PI / 180.0, p1, p2, dimLinePt, null, Db.Dimstyle);
                dim.SetDatabaseDefaults();
                ms.AppendEntity(dim);
                tr.AddNewlyCreatedDBObject(dim, true);
                tr.Commit();

                return new { success = true, handle = dim.Handle.Value.ToString("X"), type = "RotatedDimension" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateRadialDimension(CreateRadialDimRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var center = new Point3d(req.CenterX, req.CenterY, 0);
                var arcPt = new Point3d(req.ArcX, req.ArcY, 0);

                var dim = new RadialDimension(center, arcPt, 0, null, Db.Dimstyle);
                dim.SetDatabaseDefaults();
                ms.AppendEntity(dim);
                tr.AddNewlyCreatedDBObject(dim, true);
                tr.Commit();

                return new { success = true, handle = dim.Handle.Value.ToString("X"), type = "RadialDimension" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateDiametricDimension(CreateDiametricDimRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var center = new Point3d(req.CenterX, req.CenterY, 0);
                var arcPt = new Point3d(req.ArcX, req.ArcY, 0);

                var dim = new DiametricDimension(center, arcPt, 0, null, Db.Dimstyle);
                dim.SetDatabaseDefaults();
                ms.AppendEntity(dim);
                tr.AddNewlyCreatedDBObject(dim, true);
                tr.Commit();

                return new { success = true, handle = dim.Handle.Value.ToString("X"), type = "DiametricDimension" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateAngularDimension(CreateAngularDimRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var center = new Point3d(req.CenterX, req.CenterY, 0);
                var p1 = new Point3d(req.P1X, req.P1Y, 0);
                var p2 = new Point3d(req.P2X, req.P2Y, 0);

                var dim = new LineAngularDimension2(center, p1, p2, Point3d.Origin, Point3d.Origin, "ANSI", Db.Dimstyle);
                dim.SetDatabaseDefaults();
                ms.AppendEntity(dim);
                tr.AddNewlyCreatedDBObject(dim, true);
                tr.Commit();

                return new { success = true, handle = dim.Handle.Value.ToString("X"), type = "AngularDimension" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateOrdinateDimension(CreateOrdinateDimRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var definingPt = new Point3d(req.DefiningX, req.DefiningY, 0);
                var leaderEndPoint = new Point3d(req.LeaderX, req.LeaderY, 0);

                var dim = new OrdinateDimension(req.UseXAxis, definingPt, leaderEndPoint, null, Db.Dimstyle);
                dim.SetDatabaseDefaults();
                ms.AppendEntity(dim);
                tr.AddNewlyCreatedDBObject(dim, true);
                tr.Commit();

                return new { success = true, handle = dim.Handle.Value.ToString("X"), type = "OrdinateDimension" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateLinearDimension(LinearDimRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var p1 = new Point3d(req.X1, req.Y1, 0);
                var p2 = new Point3d(req.X2, req.Y2, 0);
                var dimLinePt = new Point3d(req.DimX, req.DimY, 0);

                double rotation = 0;
                if (req.Direction?.ToLower() == "vertical")
                    rotation = 90.0;

                var dim = new RotatedDimension(rotation * Math.PI / 180.0, p1, p2, dimLinePt, null, Db.Dimstyle);
                dim.SetDatabaseDefaults();
                ms.AppendEntity(dim);
                tr.AddNewlyCreatedDBObject(dim, true);
                tr.Commit();

                return new { success = true, handle = dim.Handle.Value.ToString("X"), type = "LinearDimension" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateArcLengthDimension(CreateArcLenDimRequest req)
        {
            try
            {
                using var tr = Db.TransactionManager.StartTransaction();
                var bt = (BlockTable)tr.GetObject(Db.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                // Arc length is not a native dimension type in this Teigha version.
                // Create an arc + text showing the computed arc length.
                double startRad = req.StartAngle * Math.PI / 180.0;
                double endRad = req.EndAngle * Math.PI / 180.0;
                double sweepRad = endRad - startRad;
                if (sweepRad < 0) sweepRad += 2 * Math.PI;
                double arcLength = req.Radius * sweepRad;

                var arc = new Arc(new Point3d(req.CenterX, req.CenterY, 0), req.Radius, startRad, endRad);
                arc.SetDatabaseDefaults();
                ms.AppendEntity(arc);
                tr.AddNewlyCreatedDBObject(arc, true);

                // Place text showing the arc length near the midpoint of the arc
                double midAngle = startRad + sweepRad / 2;
                double midX = req.CenterX + (req.Radius + 10) * Math.Cos(midAngle);
                double midY = req.CenterY + (req.Radius + 10) * Math.Sin(midAngle);
                var text = new DBText();
                text.Position = new Point3d(midX, midY, 0);
                text.TextString = $"\\U+21B7{arcLength:F2}";
                text.Height = 3.5;
                text.SetDatabaseDefaults();
                ms.AppendEntity(text);
                tr.AddNewlyCreatedDBObject(text, true);

                tr.Commit();
                return new
                {
                    success = true,
                    handle = text.Handle.Value.ToString("X"),
                    type = "ArcLengthDimension",
                    arc_length = Math.Round(arcLength, 4),
                };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }
    }

    public class CreateAlignedDimRequest
    {
        public double X1 { get; set; }
        public double Y1 { get; set; }
        public double X2 { get; set; }
        public double Y2 { get; set; }
        public double DimX { get; set; }
        public double DimY { get; set; }
    }

    public class CreateRotatedDimRequest
    {
        public double X1 { get; set; }
        public double Y1 { get; set; }
        public double X2 { get; set; }
        public double Y2 { get; set; }
        public double DimX { get; set; }
        public double DimY { get; set; }
        public double Rotation { get; set; }
    }

    public class CreateRadialDimRequest
    {
        public double CenterX { get; set; }
        public double CenterY { get; set; }
        public double ArcX { get; set; }
        public double ArcY { get; set; }
    }

    public class CreateDiametricDimRequest
    {
        public double CenterX { get; set; }
        public double CenterY { get; set; }
        public double ArcX { get; set; }
        public double ArcY { get; set; }
    }

    public class CreateAngularDimRequest
    {
        public double CenterX { get; set; }
        public double CenterY { get; set; }
        public double P1X { get; set; }
        public double P1Y { get; set; }
        public double P2X { get; set; }
        public double P2Y { get; set; }
    }

    public class CreateOrdinateDimRequest
    {
        public bool UseXAxis { get; set; }
        public double DefiningX { get; set; }
        public double DefiningY { get; set; }
        public double LeaderX { get; set; }
        public double LeaderY { get; set; }
    }

    // ── DIMLINEAR ──────────────────────────────────────────

    public class LinearDimRequest
    {
        public double X1 { get; set; }
        public double Y1 { get; set; }
        public double X2 { get; set; }
        public double Y2 { get; set; }
        public double DimX { get; set; }
        public double DimY { get; set; }
        public string? Direction { get; set; } // "horizontal" or "vertical"
    }
}
