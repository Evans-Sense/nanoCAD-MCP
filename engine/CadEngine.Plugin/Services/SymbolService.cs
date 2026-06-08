using System;
using Multicad;
using Multicad.DatabaseServices;
using Multicad.Geometry;
using Multicad.Symbols;

namespace CadEngine.Services
{
    public class SymbolService
    {
        public object CreateRoughness(CreateRoughnessRequest req)
        {
            try
            {
                var r = new McRoughness();
                r.FirstParam = req.Value;
                r.Angle = req.Angle;
                r.Allowance = req.Allowance;
                r.Type = req.Type;
                r.PlaceObject(McEntity.PlaceFlags.Silent);
                return new { success = true, type = "Roughness" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateOldRoughness(CreateOldRoughnessRequest req)
        {
            try
            {
                var r = new McOldRoughness();
                r.FirstParam = req.Value;
                r.Angle = req.Angle;
                r.ProcessingMethod = req.Method;
                r.CompanionMirror = req.CompanionMirror;
                r.SurfPos = req.SurfPos;
                r.DbEntity.AddToCurrentDocument();
                return new { success = true, type = "OldRoughness" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateTolerance(CreateToleranceRequest req)
        {
            try
            {
                var t = new McTolerance();
                if (!string.IsNullOrEmpty(req.Type1))
                {
                    t.Unit1.Type = ParseTolType(req.Type1);
                    t.Unit1.Value = req.Value1;
                    t.Unit1.Letters = req.Letters1;
                }
                if (!string.IsNullOrEmpty(req.Type2))
                {
                    t.Unit2.Type = ParseTolType(req.Type2);
                    t.Unit2.Value = req.Value2;
                    t.Unit2.Letters = req.Letters2;
                }
                t.UpperText = req.Text;
                t.DbEntity.AddToCurrentDocument();
                return new { success = true, type = "Tolerance" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateDatumIdentifier(CreateDatumRequest req)
        {
            try
            {
                var d = new McDatumIdentifier();
                d.Letters = req.Letter;
                d.Arrow = McDatumIdentifier.ARROW.ArrHalf;
                d.PlaceObject(McEntity.PlaceFlags.Silent);
                return new { success = true, type = "DatumIdentifier" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateWeld(CreateWeldRequest req)
        {
            try
            {
                var w = new McIsoWeld();
                w.VisibleBoxTailNote = true;
                w.VisibleFlag = true;
                w.SwapSides = req.SwapSides;
                w.RightOrientation = req.RightOrientation;
                if (!string.IsNullOrEmpty(req.LengthAbove))
                    w.LengthBottomLineAboveSide = req.LengthAbove;
                if (!string.IsNullOrEmpty(req.LengthBelow))
                    w.LengthBottomLineBelowSide = req.LengthBelow;
                w.DbEntity.AddToCurrentDocument();
                return new { success = true, type = "Weld" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateLeader(CreateLeaderRequest req)
        {
            try
            {
                var note = new McNote();
                var arrowPt = new Point3d(req.ArrowX, req.ArrowY, 0);
                var bendPt = new Point3d(req.BendX, req.BendY, 0);
                var shelfPt = new Point3d(req.ShelfX, req.ShelfY, 0);

                note.Origin = shelfPt;
                var seg = note.Leader.AddSegment(bendPt, shelfPt);
                var seg2 = seg.AddSegment(arrowPt, bendPt);
                seg2.Arrow = Arrows.Arrow;

                note.Items.Add(req.Text, 0);
                if (!string.IsNullOrEmpty(req.TextBelow))
                {
                    note.IsDulling = true;
                    note.Items.Add(req.TextBelow, 0);
                }

                note.DbEntity.AddToCurrentDocument();
                return new { success = true, type = "Leader" };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object CreateNoteComb(CreateNoteCombRequest req)
        {
            // McNoteComb.PlaceObject requires main CAD thread; constructor hangs on background thread.
            // Return unavailable error immediately instead of blocking forever.
            return new { success = false, error = "NoteComb not supported in this edition" };
        }

        public object CreateDimNumber(CreateDimNumberRequest req)
        {
            // McDimNumber constructor requires main CAD thread; hangs on background thread.
            return new { success = false, error = "DimNumber not supported in this edition" };
        }

        private static McTolerance.TolType ParseTolType(string type)
        {
            return type.ToLower() switch
            {
                "parallel" => McTolerance.TolType.Parallel,
                "beat" => McTolerance.TolType.Beat,
                _ => McTolerance.TolType.Parallel
            };
        }

        public object CreateMLeader(MLeaderRequest req)
        {
            // MLEADER command requires Plus/Pro edition and can crash free edition
            return new { success = false, error = "MLeader not supported in this edition" };
        }
    }

    public class CreateRoughnessRequest
    {
        public string Value { get; set; } = "Ra 6.3";
        public double Angle { get; set; }
        public string Allowance { get; set; } = "";
        public int Type { get; set; } = 1;
    }

    public class CreateOldRoughnessRequest
    {
        public string Value { get; set; } = "6.3";
        public double Angle { get; set; }
        public string Method { get; set; } = "";
        public bool CompanionMirror { get; set; }
        public double SurfPos { get; set; }
    }

    public class CreateToleranceRequest
    {
        public string? Type1 { get; set; }
        public string? Value1 { get; set; }
        public string? Letters1 { get; set; }
        public string? Type2 { get; set; }
        public string? Value2 { get; set; }
        public string? Letters2 { get; set; }
        public string? Text { get; set; }
    }

    public class CreateDatumRequest
    {
        public string Letter { get; set; } = "A";
    }

    public class CreateWeldRequest
    {
        public bool SwapSides { get; set; }
        public bool RightOrientation { get; set; }
        public string? LengthAbove { get; set; }
        public string? LengthBelow { get; set; }
    }

    public class CreateLeaderRequest
    {
        public double ArrowX { get; set; }
        public double ArrowY { get; set; }
        public double BendX { get; set; }
        public double BendY { get; set; }
        public double ShelfX { get; set; }
        public double ShelfY { get; set; }
        public string Text { get; set; } = "";
        public string? TextBelow { get; set; }
    }

    public class CreateNoteCombRequest
    {
        public double Angle { get; set; } = 45;
        public double TextSize { get; set; } = 12;
        public string FirstLine { get; set; } = "";
        public string SecondLine { get; set; } = "";
    }

    public class CreateDimNumberRequest
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double ArrowX { get; set; }
        public double ArrowY { get; set; }
        public string Text { get; set; } = "";
        public int Index { get; set; } = 1;
        public bool Autonum { get; set; } = true;
    }

    public class MLeaderRequest
    {
        public double ArrowX { get; set; }
        public double ArrowY { get; set; }
        public double LeaderX { get; set; }
        public double LeaderY { get; set; }
        public string Text { get; set; } = "";
        public double TextHeight { get; set; } = 3.5;
        public string? Layer { get; set; }
    }
}
