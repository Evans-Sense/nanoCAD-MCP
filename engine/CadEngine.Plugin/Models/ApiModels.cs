using System.Text.Json;
using System.Text.Json.Serialization;

namespace CadEngine
{
    public class SnakeCaseNamingPolicy : JsonNamingPolicy
    {
        public override string ConvertName(string name)
        {
            if (string.IsNullOrEmpty(name)) return name;
            return string.Concat(name.Select((c, i) =>
                i > 0 && char.IsUpper(c) ? "_" + char.ToLowerInvariant(c) : char.ToLowerInvariant(c).ToString()));
        }
    }
    // ── Health & System ─────────────────────────────────

    public class HealthResponse
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = "ok";
        [JsonPropertyName("version")]
        public string Version { get; set; } = "26.0";
        [JsonPropertyName("is_com_available")]
        public bool IsComAvailable { get; set; } = true;
        [JsonPropertyName("is_engine_available")]
        public bool IsEngineAvailable { get; set; } = true;
        [JsonPropertyName("active_documents")]
        public int ActiveDocuments { get; set; }
    }

    public class SystemInfoResponse
    {
        public string Version { get; set; } = "";
        public string Product { get; set; } = "";
        public string LicenseType { get; set; } = "";
    }

    public class FontInfoResponse
    {
        public string Name { get; set; } = "";
        public string Type { get; set; } = ""; // "truetype", "shx"
    }

    public class FontsListResponse
    {
        public List<FontInfoResponse> Fonts { get; set; } = new();
    }

    public class CommandRequest
    {
        [JsonPropertyName("command")]
        public string Command { get; set; } = "";

        [JsonPropertyName("args")]
        public System.Collections.Generic.List<string>? Args { get; set; }

        /// <summary>Build the full command string: "COMMAND arg1 arg2"</summary>
        public string FullCommand
        {
            get
            {
                if (Args == null || Args.Count == 0)
                    return Command;
                return Command + " " + string.Join(" ", Args);
            }
        }
    }

    public class CommandResponse
    {
        public string Command { get; set; } = "";
        public string? Output { get; set; }
    }

    public class SetVariableRequest
    {
        [JsonPropertyName("value")]
        public string Value { get; set; } = "";
    }

    public class VariableResponse
    {
        public string Name { get; set; } = "";
        public string? Value { get; set; }
    }

    // ── Entity Creation Requests ────────────────────────

    public class LineRequest
    {
        public double X1 { get; set; }
        public double Y1 { get; set; }
        public double X2 { get; set; }
        public double Y2 { get; set; }
        public string? Layer { get; set; }
    }

    public class CircleRequest
    {
        public double Cx { get; set; }
        public double Cy { get; set; }
        public double Radius { get; set; }
        public string? Layer { get; set; }
    }

    public class ArcRequest
    {
        public double Cx { get; set; }
        public double Cy { get; set; }
        public double Radius { get; set; }
        [JsonPropertyName("start_angle")]
        public double StartAngle { get; set; }
        [JsonPropertyName("end_angle")]
        public double EndAngle { get; set; }
        public string? Layer { get; set; }
    }

    public class PolylineRequest
    {
        public double[][] Vertices { get; set; } = Array.Empty<double[]>();
        public bool Closed { get; set; }
        public string? Layer { get; set; }
    }

    public class TextRequest
    {
        public double X { get; set; }
        public double Y { get; set; }
        public string Content { get; set; } = "";
        public double Height { get; set; }
        public double Rotation { get; set; }
        public string? Layer { get; set; }
    }

    public class MTextRequest
    {
        [JsonPropertyName("top_left_x")]
        public double TopLeftX { get; set; }
        [JsonPropertyName("top_left_y")]
        public double TopLeftY { get; set; }
        [JsonPropertyName("bottom_right_x")]
        public double BottomRightX { get; set; }
        [JsonPropertyName("bottom_right_y")]
        public double BottomRightY { get; set; }
        public string Content { get; set; } = "";
        public double Height { get; set; }
        public string? Layer { get; set; }
    }

    public class PointRequest
    {
        public double X { get; set; }
        public double Y { get; set; }
        public string? Layer { get; set; }
    }

    public class EllipseRequest
    {
        public double Cx { get; set; }
        public double Cy { get; set; }
        [JsonPropertyName("major_axis_x")]
        public double MajorAxisX { get; set; }
        [JsonPropertyName("major_axis_y")]
        public double MajorAxisY { get; set; }
        [JsonPropertyName("radius_ratio")]
        public double RadiusRatio { get; set; } = 0.5;
        public string? Layer { get; set; }
    }

    public class SplineRequest
    {
        [JsonPropertyName("fit_points")]
        public double[][] FitPoints { get; set; } = Array.Empty<double[]>();
        public int Degree { get; set; } = 3;
        public bool Closed { get; set; }
        public string? Layer { get; set; }
    }

    public class RectangleRequest
    {
        public double X1 { get; set; }
        public double Y1 { get; set; }
        public double X2 { get; set; }
        public double Y2 { get; set; }
        public string? Layer { get; set; }
    }

    // ── Entity Manipulation Requests ────────────────────

    public class MoveRequest
    {
        public double Dx { get; set; }
        public double Dy { get; set; }
        public double Dz { get; set; }
    }

    public class RotateRequest
    {
        public double Angle { get; set; }
        public double? CenterX { get; set; }
        public double? CenterY { get; set; }
    }

    public class ScaleRequest
    {
        public double Factor { get; set; }
        public double? CenterX { get; set; }
        public double? CenterY { get; set; }
    }

    public class MirrorRequest
    {
        [JsonPropertyName("p1_x")]
        public double P1X { get; set; }
        [JsonPropertyName("p1_y")]
        public double P1Y { get; set; }
        [JsonPropertyName("p2_x")]
        public double P2X { get; set; }
        [JsonPropertyName("p2_y")]
        public double P2Y { get; set; }
    }

    // ── Layer Requests ──────────────────────────────────

    public class CreateLayerRequest
    {
        public string Name { get; set; } = "";
        public string? Color { get; set; }
    }

    public class LayerStateRequest
    {
        public bool? On { get; set; }
        public bool? Frozen { get; set; }
        public bool? Locked { get; set; }
    }

    // ── Block Requests ──────────────────────────────────

    public class InsertBlockRequest
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double ScaleX { get; set; } = 1.0;
        public double ScaleY { get; set; } = 1.0;
        public double ScaleZ { get; set; } = 1.0;
        public double Rotation { get; set; }
    }

    // ── Document Requests ───────────────────────────────

    public class SaveRequest
    {
        public string? Path { get; set; }
    }

    public class ExportRequest
    {
        public string Path { get; set; } = "";
    }

    public class NewDocumentRequest
    {
        public string? Template { get; set; }
        /// <summary>Immediately save the new document to this path (.dwg).</summary>
        public string? SavePath { get; set; }
    }

    public class OpenDocumentRequest
    {
        public string Path { get; set; } = "";
    }

    // ── Response Models ─────────────────────────────────

    public class EntityResponse
    {
        public string Handle { get; set; } = "";
        public string Type { get; set; } = "";
    }

    public class EntityDetailResponse
    {
        public string Handle { get; set; } = "";
        public string Type { get; set; } = "";
        public string Layer { get; set; } = "";
        public Dictionary<string, object>? Properties { get; set; }
    }

    public class LayerResponse
    {
        public string Name { get; set; } = "";
        public string Color { get; set; } = "";
        public bool IsOn { get; set; } = true;
        public bool IsFrozen { get; set; }
        public bool IsLocked { get; set; }
        public string Linetype { get; set; } = "Continuous";
    }

    public class BlockResponse
    {
        public string Name { get; set; } = "";
        public int EntityCount { get; set; }
    }

    public class DocumentInfoResponse
    {
        public string Name { get; set; } = "";
        public string Path { get; set; } = "";
        public bool IsSaved { get; set; }
        public int EntitiesCount { get; set; }
        public int LayersCount { get; set; }
        public int BlocksCount { get; set; }
    }

    public class SuccessResponse
    {
        public bool Success { get; set; } = true;
        public string? Error { get; set; }
        public string? Handle { get; set; }
    }

    public class ErrorResponse
    {
        public string Error { get; set; } = "";
        public string? Details { get; set; }
    }

    public class LinetypeResponse
    {
        public string Name { get; set; } = "";
        public string Description { get; set; } = "";
    }

    public class LinetypesListResponse
    {
        public List<LinetypeResponse> Linetypes { get; set; } = new();
    }

    public class LayersListResponse
    {
        public List<LayerResponse> Layers { get; set; } = new();
    }

    public class BlocksListResponse
    {
        public List<BlockResponse> Blocks { get; set; } = new();
    }

    public class EntitiesListResponse
    {
        public bool Success { get; set; } = true;
        public List<EntityDetailResponse> Entities { get; set; } = new();
    }
    // -- 3D Request/Response Models --

    public class BoxRequest
    {
        public double X { get; set; } = 100;
        public double Y { get; set; } = 100;
        public double Z { get; set; } = 100;
    }

    public class SphereRequest
    {
        public double Radius { get; set; } = 50;
    }

    public class CylinderRequest
    {
        public double Radius { get; set; } = 50;
        public double Height { get; set; } = 100;
    }

    public class ConeRequest
    {
        public double RadiusBottom { get; set; } = 50;
        public double Height { get; set; } = 100;
    }

    public class TorusRequest
    {
        public double MajorRadius { get; set; } = 50;
        public double MinorRadius { get; set; } = 15;
    }

    public class WedgeRequest
    {
        public double X { get; set; } = 100;
        public double Y { get; set; } = 100;
        public double Z { get; set; } = 100;
    }

    public class PyramidRequest
    {
        public double Height { get; set; } = 100;
        public int Sides { get; set; } = 6;
        public double Radius { get; set; } = 50;
    }

    public class ExtrudeRequest
    {
        public string Handle { get; set; } = "";
        public double Height { get; set; } = 100;
        public double TaperAngle { get; set; } = 0;
    }

    public class RevolveRequest
    {
        public string Handle { get; set; } = "";
        public double AxisX { get; set; } = 0;
        public double AxisY { get; set; } = 0;
        public double AxisZ { get; set; } = 0;
        public double DirX { get; set; } = 0;
        public double DirY { get; set; } = 0;
        public double DirZ { get; set; } = 1;
        public double Angle { get; set; } = 360;
    }

    public class SolidPropertiesResponse
    {
        public string Handle { get; set; } = "";
        public double Volume { get; set; }
        public double Area { get; set; }
        public double CentroidX { get; set; }
        public double CentroidY { get; set; }
        public double CentroidZ { get; set; }
        public double MomentsOfInertiaX { get; set; }
        public double MomentsOfInertiaY { get; set; }
        public double MomentsOfInertiaZ { get; set; }
    }

    public class ViewRequest
    {
        public string Direction { get; set; } = "top";
        public string RenderMode { get; set; } = "wireframe";
    }

    // ── Trim / Extend / Offset Models ─────────────────────

    public class TrimRequest
    {
        public string Handle { get; set; } = "";
        public double CutX { get; set; }
        public double CutY { get; set; }
        public bool KeepStart { get; set; } = true; // true=keep start->cut, false=keep cut->end
    }

    public class ExtendRequest
    {
        public string Handle { get; set; } = "";
        public double EndX { get; set; }
        public double EndY { get; set; }
    }

    public class OffsetRequest
    {
        public string Handle { get; set; } = "";
        public double Distance { get; set; } = 10;  // positive=left, negative=right
    }

    // ── Transformation Models ─────────────────────────────

    public class StretchRequest
    {
        public string Handle { get; set; } = "";
        public double[][] Points { get; set; } = Array.Empty<double[]>();
        public double Dx { get; set; }
        public double Dy { get; set; }
    }

    public class DivideRequest
    {
        public string Handle { get; set; } = "";
        public int Segments { get; set; } = 2;
    }

    public class MeasureRequest
    {
        public string Handle { get; set; } = "";
        public double Distance { get; set; } = 10;
    }

    public class Array3DRequest
    {
        public string Handle { get; set; } = "";
        public int CountX { get; set; } = 2;
        public int CountY { get; set; } = 1;
        public int CountZ { get; set; } = 1;
        public double SpacingX { get; set; } = 10;
        public double SpacingY { get; set; } = 10;
        public double SpacingZ { get; set; } = 10;
    }

    public class Align3DRequest
    {
        public string Handle { get; set; } = "";
        public double SrcP1X { get; set; }
        public double SrcP1Y { get; set; }
        public double SrcP1Z { get; set; }
        public double SrcP2X { get; set; }
        public double SrcP2Y { get; set; }
        public double SrcP2Z { get; set; }
        public double SrcP3X { get; set; }
        public double SrcP3Y { get; set; }
        public double SrcP3Z { get; set; }
        public double DstP1X { get; set; }
        public double DstP1Y { get; set; }
        public double DstP1Z { get; set; }
        public double DstP2X { get; set; }
        public double DstP2Y { get; set; }
        public double DstP2Z { get; set; }
        public double DstP3X { get; set; }
        public double DstP3Y { get; set; }
        public double DstP3Z { get; set; }
    }

    public class Mirror3DRequest
    {
        public string Handle { get; set; } = "";
        public double P1X { get; set; }
        public double P1Y { get; set; }
        public double P1Z { get; set; }
        public double P2X { get; set; }
        public double P2Y { get; set; }
        public double P2Z { get; set; }
        public double P3X { get; set; }
        public double P3Y { get; set; }
        public double P3Z { get; set; }
    }

    // ── Primitive Models ──────────────────────────────────

    public class PolygonRequest
    {
        public double CenterX { get; set; }
        public double CenterY { get; set; }
        public double Radius { get; set; }
        public int Sides { get; set; } = 6;
        public bool Inscribed { get; set; } = true;
        public string? Layer { get; set; }
    }

    public class DonutRequest
    {
        public double CenterX { get; set; }
        public double CenterY { get; set; }
        public double InnerRadius { get; set; } = 5;
        public double OuterRadius { get; set; } = 10;
        public string? Layer { get; set; }
    }

    public class XLineRequest
    {
        public double P1X { get; set; }
        public double P1Y { get; set; }
        public double P2X { get; set; }
        public double P2Y { get; set; }
        public string? Layer { get; set; }
    }

    public class RayRequest
    {
        public double P1X { get; set; }
        public double P1Y { get; set; }
        public double P2X { get; set; }
        public double P2Y { get; set; }
        public string? Layer { get; set; }
    }

    // ── Drawing Management ─────────────────────────────────

    public class ImportExportRequest
    {
        public string Path { get; set; } = "";
    }

    public class CreateBlockRequest
    {
        public string Name { get; set; } = "";
        public string[] Handles { get; set; } = Array.Empty<string>();
        public double BaseX { get; set; }
        public double BaseY { get; set; }
    }

    // ── SWEEP / LOFT / FILLETEDGE / CHAMFEREDGE ──────────────

    public class SweepRequest
    {
        public string ProfileHandle { get; set; } = "";
        public string PathHandle { get; set; } = "";
    }

    public class LoftRequest
    {
        public string[] SectionHandles { get; set; } = Array.Empty<string>();
    }

    public class FilletEdgeRequest
    {
        public string Handle { get; set; } = "";
        public double Radius { get; set; } = 5.0;
    }

    public class ChamferEdgeRequest
    {
        public string Handle { get; set; } = "";
        public double Dist1 { get; set; } = 5.0;
        public double Dist2 { get; set; } = 5.0;
    }

    // ── Assembly ──────────────────────────────────────────────

    public class InsertPartRequest
    {
        public string BlockName { get; set; } = "";
        public double X { get; set; }
        public double Y { get; set; }
        public double Z { get; set; }
    }

    public class MateRequest
    {
        public string Handle1 { get; set; } = "";
        public string Handle2 { get; set; } = "";
    }

    public class AngleConstraintRequest
    {
        public string Handle1 { get; set; } = "";
        public string Handle2 { get; set; } = "";
        public double Angle { get; set; }
    }

    public class TangentConstraintRequest
    {
        public string Handle1 { get; set; } = "";
        public string Handle2 { get; set; } = "";
    }

    public class SymmetryConstraintRequest
    {
        public string Handle1 { get; set; } = "";
        public string Handle2 { get; set; } = "";
        public string PlaneHandle { get; set; } = "";
    }

    public class ExportStlRequest
    {
        public string Path { get; set; } = "";
        public bool Binary { get; set; } = true;
    }

    public class ConstraintRequest
    {
        public string Handle1 { get; set; } = "";
        public string Handle2 { get; set; } = "";
    }

    public class SingleConstraintRequest
    {
        public string Handle { get; set; } = "";
    }

    public class TangentConstraintRequest2
    {
        public string HandleLine { get; set; } = "";
        public string HandleCurve { get; set; } = "";
    }

    public class SymmetricConstraintRequest
    {
        public string Handle1 { get; set; } = "";
        public string Handle2 { get; set; } = "";
        public string PlaneHandle { get; set; } = "";
    }

    public class DistanceConstraintRequest
    {
        public string Handle1 { get; set; } = "";
        public string Handle2 { get; set; } = "";
        public double Distance { get; set; }
    }

    // ── Sheet Metal ────────────────────────────────────────────

    public class BaseFlangeRequest
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double Width { get; set; }
        public double Length { get; set; }
        public double Thickness { get; set; }
    }

    public class EdgeFlangeRequest
    {
        public string BaseHandle { get; set; } = "";
        public double BendRadius { get; set; } = 5.0;
    }

    public class BendRequest
    {
        public string Handle { get; set; } = "";
        public double BendRadius { get; set; } = 5.0;
    }

    public class HandlePointRequest
    {
        public string Handle { get; set; } = "";
        public double X { get; set; }
        public double Y { get; set; }
    }

    public class CreateBasePlateRequest
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double Width { get; set; }
        public double Length { get; set; }
        public double Thickness { get; set; }
    }

    // ── 3D Features ───────────────────────────────────────────

    public class SimpleHoleRequest
    {
        public string SolidHandle { get; set; } = "";
        public double Diameter { get; set; }
        public double Depth { get; set; }
    }

    public class StandardHoleRequest
    {
        public string SolidHandle { get; set; } = "";
        public double Diameter { get; set; }
        public double Depth { get; set; }
        public string Standard { get; set; } = "ISO";
    }

    public class ShellRequest
    {
        public string SolidHandle { get; set; } = "";
        public double Thickness { get; set; }
        public bool Outward { get; set; }
    }

    public class MirrorFeatureRequest
    {
        public string SolidHandle { get; set; } = "";
        public string PlaneHandle { get; set; } = "";
    }

    public class CircularPatternRequest
    {
        public string SolidHandle { get; set; } = "";
        public string FeatureHandle { get; set; } = "";
        public int Count { get; set; }
        public double Angle { get; set; }
    }

    public class RectangularPatternRequest
    {
        public string SolidHandle { get; set; } = "";
        public string FeatureHandle { get; set; } = "";
        public int CountX { get; set; }
        public double SpacingX { get; set; }
        public int CountY { get; set; }
        public double SpacingY { get; set; }
    }

    public class CreateSketchRequest
    {
        public string SolidHandle { get; set; } = "";
    }

    public class SketchCircleRequest
    {
        public string SketchHandle { get; set; } = "";
        public double Cx { get; set; }
        public double Cy { get; set; }
        public double Cz { get; set; }
        public double Radius { get; set; }
    }

    public class SketchLineRequest
    {
        public string SketchHandle { get; set; } = "";
        public double X1 { get; set; }
        public double Y1 { get; set; }
        public double Z1 { get; set; }
        public double X2 { get; set; }
        public double Y2 { get; set; }
        public double Z2 { get; set; }
    }

    public class CreateProfileRequest
    {
        public string SketchHandle { get; set; } = "";
    }

    public class ExtrudeFeatureRequest
    {
        public string SolidHandle { get; set; } = "";
        public string ProfileHandle { get; set; } = "";
        public double Height { get; set; }
        public double TaperAngle { get; set; }
        public bool Direction { get; set; } = true;
    }

    public class RevolveFeatureRequest
    {
        public string SolidHandle { get; set; } = "";
        public string ProfileHandle { get; set; } = "";
        public double AxisX { get; set; }
        public double AxisY { get; set; }
        public double AxisZ { get; set; }
        public double DirX { get; set; }
        public double DirY { get; set; }
        public double DirZ { get; set; }
        public double Angle { get; set; }
    }

    // ── Helix ──────────────────────────────────────────────
    public class HelixRequest
    {
        public double CenterX { get; set; }
        public double CenterY { get; set; }
        public double CenterZ { get; set; }
        public double StartRadius { get; set; } = 20;
        public double EndRadius { get; set; } = 20;
        public double Height { get; set; } = 50;
        public double Turns { get; set; } = 3;
        public string? Layer { get; set; }
    }

    // ── Region ─────────────────────────────────────────────
    public class RegionRequest
    {
        public List<string> CurveHandles { get; set; } = new();
    }

    // ── Boundary ───────────────────────────────────────────
    public class BoundaryRequest
    {
        public double PointX { get; set; }
        public double PointY { get; set; }
        public string? Layer { get; set; }
    }

    // ── Gradient ────────────────────────────────────────────
    public class CreateGradientRequest
    {
        public string Color1 { get; set; } = "1,1,1";
        public string Color2 { get; set; } = "0,0,0";
        public double Scale { get; set; } = 1.0;
        public string? GradientType { get; set; } = "linear";
        public List<string>? BoundaryHandles { get; set; }
        public List<double>? PointXs { get; set; }
        public List<double>? PointYs { get; set; }
    }

    // ── Arc Length Dimension ───────────────────────────────
    public class CreateArcLenDimRequest
    {
        public double CenterX { get; set; }
        public double CenterY { get; set; }
        public double Radius { get; set; } = 50;
        public double StartAngle { get; set; }
        public double EndAngle { get; set; }
        public double DimX { get; set; }
        public double DimY { get; set; }
    }

    // ── Export IFC ─────────────────────────────────────────
    public class ExportIfcRequest
    {
        public string Path { get; set; } = "";
    }

    // ── Mesh ───────────────────────────────────────────────
    public class CreateMeshRequest
    {
        public List<List<double>> Vertices { get; set; } = new();
        public List<int> FaceIndices { get; set; } = new();
        public int SmoothLevel { get; set; } = 0;
        public string? Layer { get; set; }
    }

    public class EditMeshRequest
    {
        public string Handle { get; set; } = "";
        public List<List<double>>? Vertices { get; set; }
        public List<int>? VertexIndices { get; set; }
        public int? Subdivide { get; set; } // -1=divide down, 0=none, 1=divide up
    }

    // ── Viewport ────────────────────────────────────────────
    public class SetViewportRequest
    {
        public string Name { get; set; } = "*Active";
        public string Type { get; set; } = "single"; // single, 2horiz, 2vert, 3, 4
    }

    // ── Render ──────────────────────────────────────────────
    public class RenderRequest
    {
        public string? OutputFile { get; set; }
    }

    // ── NURBS Curve ─────────────────────────────────────────
    public class CreateNurbCurveRequest
    {
        public int Degree { get; set; } = 3;
        public bool Periodic { get; set; }
        public List<List<double>> ControlPoints { get; set; } = new();
        public List<double> Knots { get; set; } = new();
        public List<double>? Weights { get; set; }
        public string? Layer { get; set; }
    }

    // ── NURBS Surface ───────────────────────────────────────
    public class CreateNurbSurfaceRequest
    {
        public int DegreeU { get; set; } = 3;
        public int DegreeV { get; set; } = 3;
        public bool Rational { get; set; }
        public List<List<double>> ControlPoints { get; set; } = new();
        public List<double> UKnots { get; set; } = new();
        public List<double> VKnots { get; set; } = new();
        public List<double>? Weights { get; set; }
        public int NumControlU { get; set; }
        public int NumControlV { get; set; }
        public string? Layer { get; set; }
    }

    // ── Modify NURBS ────────────────────────────────────────
    public class ModifyNurbRequest
    {
        public string Handle { get; set; } = "";
        public List<List<double>>? ControlPoints { get; set; }
        public List<double>? Knots { get; set; }
    }

    // ── MultiCAD API Request Types ──────────────────────────
    public class GridAxisRequest
    {
        public string Type { get; set; } = "rect";
        public double OriginX { get; set; }
        public double OriginY { get; set; }
        public List<double> SpacingsX { get; set; } = new() { 100 };
        public List<double> SpacingsY { get; set; } = new() { 100 };
        public string NamingX { get; set; } = "digits";
        public string NamingY { get; set; } = "letters";
    }

    public class GridLabelRequest
    {
        public string GridHandle { get; set; } = "";
        public string Label { get; set; } = "";
        public int AxisIndex { get; set; }
        public string Direction { get; set; } = "X";
    }

    public class CreateRoomRequest
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double Width { get; set; } = 1000;
        public double Height { get; set; } = 1000;
        public string? Name { get; set; }
    }

    public class CustomObjectRequest
    {
        public string ClassName { get; set; } = "";
        public Dictionary<string, object>? Properties { get; set; }
    }

    public class ParametricObjectRequest
    {
        public string Type { get; set; } = "";
        public Dictionary<string, object>? Parameters { get; set; }
    }

    public class ReactorRequest
    {
        public string EntityHandle { get; set; } = "";
        public string EventType { get; set; } = "modified";
    }

    public class Break2dRequest
    {
        public string ViewHandle { get; set; } = "";
        public double X1 { get; set; }
        public double Y1 { get; set; }
        public double X2 { get; set; }
        public double Y2 { get; set; }
    }

    public class MotionPreviewRequest
    {
        public string Handle { get; set; } = "";
    }

    public class BodyContourRequest
    {
        public string SolidHandle { get; set; } = "";
    }
}
