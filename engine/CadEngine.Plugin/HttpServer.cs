using System;
using System.IO;
using System.Net;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using CadEngine.Services;

namespace CadEngine
{
    public class HttpServer : IDisposable
    {
        private readonly int _port;
        private readonly CancellationToken _cancellationToken;
        private HttpListener? _listener;
        private bool _disposed;

        private readonly EntityService _entityService;
        private readonly LayerService _layerService;
        private readonly DocumentService _documentService;
        private readonly SystemService _systemService;
        private readonly SolidService _solidService;
        private readonly SymbolService _symbolService;
        private readonly TableService _tableService;
        private readonly HatchService _hatchService;
        private readonly DimensionService _dimensionService;
        private readonly MeasurementService _measurementService;
        private readonly MultiCadService _multiCadService;
        private readonly TransformationService _transformationService;
        private readonly PrimitiveService _primitiveService;
        private readonly SelectionService _selectionService;
        private readonly SheetMetalService _sheetMetalService;
        private readonly FeatureService _featureService;

        private static readonly JsonSerializerOptions JsonOptions = new()
        {
            PropertyNamingPolicy = new SnakeCaseNamingPolicy(),
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            WriteIndented = false
        };

        public HttpServer(int port, CancellationToken cancellationToken)
        {
            _port = port;
            _cancellationToken = cancellationToken;
            _entityService = new EntityService();
            _layerService = new LayerService();
            _documentService = new DocumentService();
            _systemService = new SystemService();
            _solidService = new SolidService();
            _symbolService = new SymbolService();
            _tableService = new TableService();
            _hatchService = new HatchService();
            _dimensionService = new DimensionService();
            _measurementService = new MeasurementService();
            _transformationService = new TransformationService();
            _primitiveService = new PrimitiveService();
            _selectionService = new SelectionService();
            _sheetMetalService = new SheetMetalService();
            _featureService = new FeatureService();
            _multiCadService = new MultiCadService();
        }

        public async Task Start()
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add($"http://localhost:{_port}/");
            _listener.Start();
            PluginEntry.DebugLog($"HTTP listener started on localhost:{_port}");

            while (!_cancellationToken.IsCancellationRequested)
            {
                try
                {
                    var ctx = await _listener.GetContextAsync().ConfigureAwait(false);
                    _ = HandleRequestAsync(ctx);
                }
                catch (HttpListenerException) when (_cancellationToken.IsCancellationRequested)
                {
                    break;
                }
                catch (ObjectDisposedException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    // Prevent a single bad request from crashing the entire server.
                    // Log and continue processing.
                    PluginEntry.DebugLog($"Main loop exception: {ex.Message}");
                }
            }
        }

        private async Task HandleRequestAsync(HttpListenerContext context)
        {
            try
            {
                PluginEntry.DebugLog($"Request: {context.Request.HttpMethod} {context.Request.Url?.AbsolutePath}");

                // Refresh document reference on every request.
                // This ensures we always point to the current document,
                // even after NEW/QNEW or other document-destroying operations.
                // Note: RefreshDocument only overwrites ActiveDocument if
                // MdiActiveDocument returns non-null (it may return null on background threads).
                CadContext.RefreshDocument();
                PluginEntry.DebugLog($"ActiveDocument={(CadContext.ActiveDocument != null ? CadContext.ActiveDocument.Name : "null")}");

                var req = context.Request;
                var method = req.HttpMethod.ToUpperInvariant();
                var path = req.Url?.AbsolutePath?.TrimEnd('/') ?? "/";

                object? result;
                try
                {
                    result = RouteRequest(method, path, req);
                }
                catch (Exception routeEx)
                {
                    PluginEntry.DebugLog($"Route error [{method} {path}]: {routeEx.Message}");
                    result = new ErrorResponse
                    {
                        Error = $"Error executing {method} {path}",
                        Details = routeEx.Message,
                    };
                }

                PluginEntry.DebugLog($"Response OK: {context.Request.HttpMethod} {context.Request.Url?.AbsolutePath}");
                await WriteJsonResponseSafe(context.Response, result);
            }
            catch (Exception ex)
            {
                PluginEntry.DebugLog($"HTTP error [{context.Request.HttpMethod} {context.Request.Url?.AbsolutePath}]: {ex}");
                await WriteJsonResponseSafe(context.Response, new ErrorResponse { Error = ex.Message }, 500);
            }
        }

        /// <summary>
        /// Writes a JSON response with exception-safe handling.
        /// Never throws — any error is silently logged.
        /// </summary>
        private static async Task WriteJsonResponseSafe(HttpListenerResponse response, object? data, int statusCode = 200)
        {
            try
            {
                response.StatusCode = statusCode;
                response.ContentType = "application/json; charset=utf-8";
                if (data == null)
                {
                    response.StatusCode = 404;
                    response.Close();
                    return;
                }
                var json = JsonSerializer.Serialize(data, JsonOptions);
                var buffer = Encoding.UTF8.GetBytes(json);
                response.ContentLength64 = buffer.Length;
                await response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
                response.Close();
            }
            catch (Exception ex)
            {
                PluginEntry.DebugLog($"WriteJsonResponseSafe error: {ex.Message}");
                try { response.Close(); } catch { }
            }
        }

        private object? RouteRequest(string method, string path, HttpListenerRequest request)
        {
            // Health
            if (method == "GET" && path == "/api/system/health")
                return _systemService.GetHealth();

            // System
            if (method == "GET" && path == "/api/system/info")
                return _systemService.GetInfo();

            if (method == "GET" && path == "/api/system/fonts")
                return _systemService.GetFonts();

            if (method == "POST" && path == "/api/system/command")
            {
                var req = ParseBody<CommandRequest>(request);
                return req != null ? _systemService.ExecuteCommand(req.FullCommand) : BadRequest();
            }

            if (method == "GET" && TryMatch(path, "/api/system/variable/{name}", out var varGetName))
                return _systemService.GetVariable(varGetName!);

            if (method == "POST" && TryMatch(path, "/api/system/variable/{name}", out var varSetName))
            {
                var req = ParseBody<SetVariableRequest>(request);
                return req != null ? _systemService.SetVariable(varSetName!, req.Value) : BadRequest();
            }

            // Document
            if (method == "GET" && path == "/api/document")
                return _documentService.GetInfo();

            if (method == "POST" && path == "/api/document/save")
            {
                var req = ParseBody<SaveRequest>(request);
                return _documentService.Save(req?.Path);
            }

            if (method == "POST" && path == "/api/document/export/pdf")
            {
                var req = ParseBody<ExportRequest>(request);
                return req != null ? _documentService.ExportPdf(req.Path) : BadRequest();
            }

            if (method == "POST" && path == "/api/document/export/dwg")
            {
                var req = ParseBody<ExportRequest>(request);
                return req != null ? _documentService.ExportDwg(req.Path) : BadRequest();
            }

            if (method == "POST" && path == "/api/document/export/dxf")
            {
                var req = ParseBody<ExportRequest>(request);
                return req != null ? _documentService.ExportDxf(req.Path) : BadRequest();
            }

            if (method == "POST" && path == "/api/document/zoom/extents")
                return _documentService.ZoomExtents();

            if (method == "POST" && path == "/api/document/new")
            {
                var req = ParseBody<NewDocumentRequest>(request);
                return _documentService.NewDocument(req?.Template, req?.SavePath);
            }

            if (method == "POST" && path == "/api/document/open")
            {
                var req = ParseBody<OpenDocumentRequest>(request);
                return req != null ? _documentService.Open(req.Path) : BadRequest();
            }

            if (method == "POST" && path == "/api/document/close")
                return _documentService.Close();

            // Entity creation
            if (method == "POST" && path == "/api/entity/line")
            {
                var req = ParseBody<LineRequest>(request);
                return req != null ? _entityService.CreateLine(req) : BadRequest();
            }

            if (method == "POST" && path == "/api/entity/circle")
            {
                var req = ParseBody<CircleRequest>(request);
                return req != null ? _entityService.CreateCircle(req) : BadRequest();
            }

            if (method == "POST" && path == "/api/entity/arc")
            {
                var req = ParseBody<ArcRequest>(request);
                return req != null ? _entityService.CreateArc(req) : BadRequest();
            }

            if (method == "POST" && path == "/api/entity/polyline")
            {
                var req = ParseBody<PolylineRequest>(request);
                return req != null ? _entityService.CreatePolyline(req) : BadRequest();
            }

            if (method == "POST" && path == "/api/entity/text")
            {
                var req = ParseBody<TextRequest>(request);
                return req != null ? _entityService.CreateText(req) : BadRequest();
            }

            if (method == "POST" && path == "/api/entity/mtext")
            {
                var req = ParseBody<MTextRequest>(request);
                return req != null ? _entityService.CreateMText(req) : BadRequest();
            }

            if (method == "POST" && path == "/api/entity/point")
            {
                var req = ParseBody<PointRequest>(request);
                return req != null ? _entityService.CreatePoint(req) : BadRequest();
            }

            if (method == "POST" && path == "/api/entity/ellipse")
            {
                var req = ParseBody<EllipseRequest>(request);
                return req != null ? _entityService.CreateEllipse(req) : BadRequest();
            }

            if (method == "POST" && path == "/api/entity/spline")
            {
                var req = ParseBody<SplineRequest>(request);
                return req != null ? _entityService.CreateSpline(req) : BadRequest();
            }

            if (method == "POST" && path == "/api/entity/rectangle")
            {
                var req = ParseBody<RectangleRequest>(request);
                return req != null ? _entityService.CreateRectangle(req) : BadRequest();
            }

            // Helix
            if (method == "POST" && path == "/api/entity/helix")
            {
                var req = ParseBody<HelixRequest>(request);
                return req != null ? _entityService.CreateHelix(req) : BadRequest();
            }

            // Region
            if (method == "POST" && path == "/api/entity/region")
            {
                var req = ParseBody<RegionRequest>(request);
                return req != null ? _entityService.CreateRegion(req) : BadRequest();
            }

            // Boundary
            if (method == "POST" && path == "/api/entity/boundary")
            {
                var req = ParseBody<BoundaryRequest>(request);
                return req != null ? _entityService.CreateBoundary(req) : BadRequest();
            }

            // Mesh
            if (method == "POST" && path == "/api/entity/mesh")
            {
                var req = ParseBody<CreateMeshRequest>(request);
                return req != null ? _entityService.CreateMesh(req) : BadRequest();
            }

            if (method == "PATCH" && path == "/api/entity/mesh")
            {
                var req = ParseBody<EditMeshRequest>(request);
                return req != null ? _entityService.EditMesh(req) : BadRequest();
            }

            // Viewport
            if (method == "POST" && path == "/api/viewport")
            {
                var req = ParseBody<SetViewportRequest>(request);
                return req != null ? _entityService.SetViewport(req) : BadRequest();
            }

            // Render
            if (method == "POST" && path == "/api/render")
            {
                var req = ParseBody<RenderRequest>(request);
                return req != null ? _entityService.Render(req) : BadRequest();
            }

            // NURBS Curve
            if (method == "POST" && path == "/api/entity/nurbcurve")
            {
                var req = ParseBody<CreateNurbCurveRequest>(request);
                return req != null ? _entityService.CreateNurbCurve(req) : BadRequest();
            }

            // NURBS Surface
            if (method == "POST" && path == "/api/entity/nurbsurface")
            {
                var req = ParseBody<CreateNurbSurfaceRequest>(request);
                return req != null ? _entityService.CreateNurbSurface(req) : BadRequest();
            }

            // Modify NURBS
            if (method == "PATCH" && path == "/api/entity/nurb")
            {
                var req = ParseBody<ModifyNurbRequest>(request);
                return req != null ? _entityService.ModifyNurb(req) : BadRequest();
            }

            // Entity manipulation
            if (method == "DELETE" && TryMatch(path, "/api/entity/{handle}", out var delHandle))
                return _entityService.DeleteEntity(delHandle!);

            if (method == "GET" && TryMatch(path, "/api/entity/{handle}", out var getHandle))
                return _entityService.GetEntity(getHandle!);

            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/move", out var moveHandle))
            {
                var req = ParseBody<MoveRequest>(request);
                return req != null ? _entityService.MoveEntity(moveHandle!, req) : BadRequest();
            }

            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/copy", out var copyHandle))
                return _entityService.CopyEntity(copyHandle!);

            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/rotate", out var rotHandle))
            {
                var req = ParseBody<RotateRequest>(request);
                return req != null ? _entityService.RotateEntity(rotHandle!, req) : BadRequest();
            }

            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/scale", out var scaleHandle))
            {
                var req = ParseBody<ScaleRequest>(request);
                return req != null ? _entityService.ScaleEntity(scaleHandle!, req) : BadRequest();
            }

            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/mirror", out var mirHandle))
            {
                var req = ParseBody<MirrorRequest>(request);
                return req != null ? _entityService.MirrorEntity(mirHandle!, req) : BadRequest();
            }

            // Linetype
            if (method == "GET" && path == "/api/linetype")
                return _layerService.GetLinetypes();

            // Layer
            if (method == "GET" && path == "/api/layer")
                return _layerService.GetLayers();

            if (method == "POST" && path == "/api/layer")
            {
                var req = ParseBody<CreateLayerRequest>(request);
                return req != null ? _layerService.CreateLayer(req) : BadRequest();
            }

            if (method == "DELETE" && TryMatch(path, "/api/layer/{name}", out var delLayer))
                return _layerService.DeleteLayer(delLayer!);

            if (method == "POST" && TryMatch(path, "/api/layer/{name}/current", out var curLayer))
                return _layerService.SetCurrentLayer(curLayer!);

            if (method == "PATCH" && TryMatch(path, "/api/layer/{name}", out var layerState))
            {
                var req = ParseBody<LayerStateRequest>(request);
                return req != null ? _layerService.SetLayerState(layerState!, req) : BadRequest();
            }

            // Block
            if (method == "GET" && path == "/api/block")
                return _entityService.GetBlocks();

            if (method == "POST" && path == "/api/block/create")
            {
                var req = ParseBody<CreateBlockRequest>(request);
                return req != null ? _entityService.CreateBlock(req) : BadRequest();
            }

            if (method == "POST" && TryMatch(path, "/api/block/{name}/insert", out var insBlock))
            {
                var req = ParseBody<InsertBlockRequest>(request);
                return req != null ? _entityService.InsertBlock(insBlock!, req) : BadRequest();
            }

            if (method == "DELETE" && TryMatch(path, "/api/block/{name}", out var delBlock))
                return _entityService.DeleteBlock(delBlock!);

            if (method == "GET" && TryMatch(path, "/api/block/{name}/entities", out var getBlockEnts))
                return _entityService.GetBlockEntities(getBlockEnts!);

            // Block explode
            if (method == "POST" && TryMatch(path, "/api/block/{name}/explode", out var explodeBlock))
                return _entityService.ExplodeBlock(explodeBlock!);


            // 3D Solid Primitives
            if (method == "POST" && path == "/api/solid/box")
            { PluginEntry.DebugLog("POST /api/solid/box: parsing body..."); var req = ParseBody<BoxRequest>(request); PluginEntry.DebugLog($"POST /api/solid/box: parsed, req={req != null}"); return req != null ? _solidService.CreateBox(req) : BadRequest(); }
            if (method == "POST" && path == "/api/solid/sphere")
            { var req = ParseBody<SphereRequest>(request); return req != null ? _solidService.CreateSphere(req) : BadRequest(); }
            if (method == "POST" && path == "/api/solid/cylinder")
            { var req = ParseBody<CylinderRequest>(request); return req != null ? _solidService.CreateCylinder(req) : BadRequest(); }
            if (method == "POST" && path == "/api/solid/cone")
            { var req = ParseBody<ConeRequest>(request); return req != null ? _solidService.CreateCone(req) : BadRequest(); }
            if (method == "POST" && path == "/api/solid/torus")
            { var req = ParseBody<TorusRequest>(request); return req != null ? _solidService.CreateTorus(req) : BadRequest(); }
            if (method == "POST" && path == "/api/solid/wedge")
            { var req = ParseBody<WedgeRequest>(request); return req != null ? _solidService.CreateWedge(req) : BadRequest(); }
            if (method == "POST" && path == "/api/solid/pyramid")
            { var req = ParseBody<PyramidRequest>(request); return req != null ? _solidService.CreatePyramid(req) : BadRequest(); }
            // 3D Boolean (parse /api/solid/{h1}/{op}/{h2})
            if (method == "POST" && path.StartsWith("/api/solid/") && path.Count(c => c == '/') == 5)
            {
                var parts = path.Split('/');
                var h1 = parts[3]; var op = parts[4]; var h2 = parts[5];
                if (op == "union") return _solidService.BooleanUnion(h1, h2);
                if (op == "subtract") return _solidService.BooleanSubtract(h1, h2);
                if (op == "intersect") return _solidService.BooleanIntersect(h1, h2);
            }
            // 3D Extrude/Revolve
            if (method == "POST" && path == "/api/solid/extrude")
            { var req = ParseBody<ExtrudeRequest>(request); return req != null ? _solidService.Extrude(req) : BadRequest(); }
            if (method == "POST" && path == "/api/solid/revolve")
            { var req = ParseBody<RevolveRequest>(request); return req != null ? _solidService.Revolve(req) : BadRequest(); }
            // 3D Move/Rotate
            if (method == "POST" && TryMatch(path, "/api/solid/{handle}/move3d", out var mvHandle))
            { var req = ParseBody<MoveRequest>(request); return req != null ? _solidService.MoveSolid(mvHandle!, req.Dx, req.Dy, req.Dz) : BadRequest(); }
            // 3D View
            if (method == "POST" && path == "/api/solid/view")
            { var req = ParseBody<ViewRequest>(request); return req != null ? _solidService.Set3dView(req.Direction, req.RenderMode) : BadRequest(); }
            // 3D Properties
            if (method == "GET" && TryMatch(path, "/api/solid/{handle}/props", out var propHandle))
            { return _solidService.GetSolidProps(propHandle!); }
            // 3D Zoom
            if (method == "POST" && path == "/api/solid/zoom")
            { return _solidService.ZoomExt(); }

            // === SYMBOLS (MultiCAD) ===
            if (method == "POST" && path == "/api/symbol/roughness")
            { var req = ParseBody<CreateRoughnessRequest>(request); return req != null ? _symbolService.CreateRoughness(req) : BadRequest(); }
            if (method == "POST" && path == "/api/symbol/old-roughness")
            { var req = ParseBody<CreateOldRoughnessRequest>(request); return req != null ? _symbolService.CreateOldRoughness(req) : BadRequest(); }
            if (method == "POST" && path == "/api/symbol/tolerance")
            { var req = ParseBody<CreateToleranceRequest>(request); return req != null ? _symbolService.CreateTolerance(req) : BadRequest(); }
            if (method == "POST" && path == "/api/symbol/datum")
            { var req = ParseBody<CreateDatumRequest>(request); return req != null ? _symbolService.CreateDatumIdentifier(req) : BadRequest(); }
            if (method == "POST" && path == "/api/symbol/weld")
            { var req = ParseBody<CreateWeldRequest>(request); return req != null ? _symbolService.CreateWeld(req) : BadRequest(); }
            if (method == "POST" && path == "/api/symbol/leader")
            { var req = ParseBody<CreateLeaderRequest>(request); return req != null ? _symbolService.CreateLeader(req) : BadRequest(); }
            if (method == "POST" && path == "/api/symbol/note-comb")
            { var req = ParseBody<CreateNoteCombRequest>(request); return req != null ? _symbolService.CreateNoteComb(req) : BadRequest(); }
            if (method == "POST" && path == "/api/symbol/dim-number")
            { var req = ParseBody<CreateDimNumberRequest>(request); return req != null ? _symbolService.CreateDimNumber(req) : BadRequest(); }

            // === TABLES (MultiCAD) ===
            if (method == "POST" && path == "/api/table")
            { PluginEntry.DebugLog("POST /api/table: parsing body..."); var req = ParseBody<CreateTableRequest>(request); PluginEntry.DebugLog($"POST /api/table: parsed, req={req != null}"); return req != null ? _tableService.CreateTable(req) : BadRequest(); }
            if (method == "GET" && TryMatch(path, "/api/table/{handle}", out var tableGetHandle))
            { return _tableService.GetTableInfo(tableGetHandle!); }
            if (method == "PATCH" && TryMatch(path, "/api/table/{handle}/cell", out var tableEditHandle))
            { var req = ParseBody<EditTableCellRequest>(request); return req != null ? _tableService.EditTableCell(tableEditHandle!, req) : BadRequest(); }

            if (method == "DELETE" && TryMatch(path, "/api/table/{handle}", out var tableDelHandle))
            { return _tableService.DeleteTable(tableDelHandle!); }

            // === HATCH ===
            if (method == "POST" && path == "/api/hatch")
            { var req = ParseBody<CreateHatchRequest>(request); return req != null ? _hatchService.CreateHatch(req) : BadRequest(); }
            if (method == "GET" && TryMatch(path, "/api/hatch/{handle}", out var hatchHandle))
            { return _hatchService.GetHatchInfo(hatchHandle!); }
            if (method == "PATCH" && TryMatch(path, "/api/hatch/{handle}", out var hatchEditHandle))
            { var req = ParseBody<EditHatchRequest>(request); return req != null ? _hatchService.EditHatch(hatchEditHandle!, req) : BadRequest(); }

            // === DIMENSIONS ===
            if (method == "POST" && path == "/api/dimension/aligned")
            { var req = ParseBody<CreateAlignedDimRequest>(request); return req != null ? _dimensionService.CreateAlignedDimension(req) : BadRequest(); }
            if (method == "POST" && path == "/api/dimension/rotated")
            { var req = ParseBody<CreateRotatedDimRequest>(request); return req != null ? _dimensionService.CreateRotatedDimension(req) : BadRequest(); }
            if (method == "POST" && path == "/api/dimension/radial")
            { var req = ParseBody<CreateRadialDimRequest>(request); return req != null ? _dimensionService.CreateRadialDimension(req) : BadRequest(); }
            if (method == "POST" && path == "/api/dimension/diametric")
            { var req = ParseBody<CreateDiametricDimRequest>(request); return req != null ? _dimensionService.CreateDiametricDimension(req) : BadRequest(); }
            if (method == "POST" && path == "/api/dimension/angular")
            { var req = ParseBody<CreateAngularDimRequest>(request); return req != null ? _dimensionService.CreateAngularDimension(req) : BadRequest(); }
            if (method == "POST" && path == "/api/dimension/ordinate")
            { var req = ParseBody<CreateOrdinateDimRequest>(request); return req != null ? _dimensionService.CreateOrdinateDimension(req) : BadRequest(); }

            // === DIMLINEAR ===
            if (method == "POST" && path == "/api/dimension/linear")
            { var req = ParseBody<LinearDimRequest>(request); return req != null ? _dimensionService.CreateLinearDimension(req) : BadRequest(); }

            // Arc Length Dimension
            if (method == "POST" && path == "/api/dimension/arc_length")
            { var req = ParseBody<CreateArcLenDimRequest>(request); return req != null ? _dimensionService.CreateArcLengthDimension(req) : BadRequest(); }

            // === GRADIENT ===
            if (method == "POST" && path == "/api/gradient")
            { var req = ParseBody<CreateGradientHatchRequest>(request); return req != null ? _hatchService.CreateGradientHatch(req) : BadRequest(); }

            // === EXPORT IFC ===
            if (method == "POST" && path == "/api/document/export/ifc")
            { var req = ParseBody<ExportIfcRequest>(request); return req != null ? _documentService.ExportIfc(req.Path) : BadRequest(); }

            // === IMPORT IFC ===
            if (method == "POST" && path == "/api/document/import/ifc")
            { var req = ParseBody<ExportIfcRequest>(request); return req != null ? _documentService.ImportIfc(req.Path) : BadRequest(); }

            // === GET IFC ENTITIES ===
            if (method == "GET" && path == "/api/document/ifc/entities")
            { return _documentService.GetIfcEntities(); }

            // === LAYER MANAGEMENT ===
            if (method == "POST" && TryMatch(path, "/api/layer/{name}/isolate", out var isoLayer))
            { return _layerService.LayerIsolate(isoLayer!); }
            if (method == "POST" && TryMatch(path, "/api/layer/{name}/off", out var offLayer))
            { return _layerService.LayerOff(offLayer!); }
            if (method == "POST" && TryMatch(path, "/api/layer/{name}/freeze", out var frzLayer))
            { return _layerService.LayerFreeze(frzLayer!); }
            if (method == "POST" && path == "/api/layer/on")
            { return _layerService.LayerOnAll(); }
            if (method == "POST" && path == "/api/layer/thaw")
            { return _layerService.LayerThawAll(); }

            // === MEASUREMENTS ===
            if (method == "POST" && path == "/api/measurement/distance")
            { var req = ParseBody<DistanceRequest>(request); return req != null ? _measurementService.GetDistance(req) : BadRequest(); }
            if (method == "POST" && path == "/api/measurement/angle")
            { PluginEntry.DebugLog("POST /api/measurement/angle: parsing body..."); var req = ParseBody<AngleRequest>(request); PluginEntry.DebugLog($"POST /api/measurement/angle: parsed, req={req != null}"); return req != null ? _measurementService.GetAngle(req) : BadRequest(); }
            if (method == "GET" && TryMatch(path, "/api/measurement/area/{handle}", out var areaHandle))
            { return _measurementService.GetArea(areaHandle!); }
            if (method == "GET" && TryMatch(path, "/api/entity/{handle}/info", out var infoHandle))
            { return _measurementService.GetEntityInfo(infoHandle!); }
            if (method == "GET" && path == "/api/measurement/entities")
             { return _measurementService.GetAllEntities(); }

            // === SELECTION / QSELECT ===
            if (method == "POST" && path == "/api/selection/select")
            { var req = ParseBody<SelectEntitiesRequest>(request); return req != null ? _selectionService.SelectEntities(req.EntityType, req.Layer, req.Color, req.MaxCount) : BadRequest(); }
            if (method == "POST" && path == "/api/selection/by-handles")
            { var req = ParseBody<SelectByHandlesRequest>(request); return req != null ? _selectionService.SelectByHandles(req.Handles) : BadRequest(); }
            if (method == "GET" && TryMatch(path, "/api/selection/entity/{handle}", out var selHandle))
            { return _selectionService.GetEntityDetail(selHandle!); }

            // === TRANSFORMATIONS ===
            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/stretch", out var strHandle))
            { var req = ParseBody<StretchRequest>(request); return req != null ? _transformationService.StretchEntity(req) : BadRequest(); }
            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/explode", out var expHandle))
            { return _transformationService.ExplodeEntity(expHandle!); }
            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/divide", out var divHandle))
            { var req = ParseBody<DivideRequest>(request); return req != null ? _transformationService.DivideEntity(divHandle!, req.Segments) : BadRequest(); }
            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/measure", out var measHandle))
            { var req = ParseBody<MeasureRequest>(request); return req != null ? _transformationService.MeasureEntity(measHandle!, req.Distance) : BadRequest(); }
            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/array3d", out var arrHandle))
            { var req = ParseBody<Array3DRequest>(request); return req != null ? _transformationService.Array3D(req) : BadRequest(); }
            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/align3d", out var alignHandle))
            { var req = ParseBody<Align3DRequest>(request); return req != null ? _transformationService.Align3D(req) : BadRequest(); }
            if (method == "POST" && TryMatch(path, "/api/entity/{handle}/mirror3d", out var mir3Handle))
            { var req = ParseBody<Mirror3DRequest>(request); return req != null ? _transformationService.Mirror3D(req) : BadRequest(); }

            // === NEW PRIMITIVES ===
            if (method == "POST" && path == "/api/entity/polygon")
            { var req = ParseBody<PolygonRequest>(request); return req != null ? _primitiveService.CreatePolygon(req) : BadRequest(); }
            if (method == "POST" && path == "/api/entity/donut")
            { var req = ParseBody<DonutRequest>(request); return req != null ? _primitiveService.CreateDonut(req) : BadRequest(); }
            if (method == "POST" && path == "/api/entity/xline")
            { var req = ParseBody<XLineRequest>(request); return req != null ? _primitiveService.CreateXLine(req) : BadRequest(); }
            if (method == "POST" && path == "/api/entity/ray")
            { var req = ParseBody<RayRequest>(request); return req != null ? _primitiveService.CreateRay(req) : BadRequest(); }

            // === DOCUMENT MANAGEMENT ===
            if (method == "POST" && path == "/api/document/undo")
            { return _documentService.Undo(); }
            if (method == "POST" && path == "/api/document/redo")
            { return _documentService.Redo(); }
            if (method == "POST" && path == "/api/document/purge")
            { return _documentService.Purge(); }
            if (method == "POST" && path == "/api/document/import/step")
            { var req = ParseBody<ImportExportRequest>(request); return req != null ? _documentService.ImportStep(req.Path) : BadRequest(); }
            if (method == "POST" && path == "/api/document/export/step")
            {
                var req = ParseBody<ImportExportRequest>(request);
                return req != null ? _documentService.ExportStep(req.Path) : BadRequest();
            }

            if (method == "POST" && path == "/api/document/export/stl")
            {
                var req = ParseBody<ExportStlRequest>(request);
                return req != null ? _documentService.ExportStl(req.Path, req.Binary) : BadRequest();
            }

            // === 2D CONSTRAINTS ===
            if (method == "POST" && path == "/api/constraint/parallel")
            { var req = ParseBody<ConstraintRequest>(request); return req != null ? _transformationService.ConstraintParallel(req.Handle1, req.Handle2) : BadRequest(); }
            if (method == "POST" && path == "/api/constraint/coincident")
            { var req = ParseBody<ConstraintRequest>(request); return req != null ? _transformationService.ConstraintCoincident(req.Handle1, req.Handle2) : BadRequest(); }
            if (method == "POST" && path == "/api/constraint/fix")
            { var req = ParseBody<SingleConstraintRequest>(request); return req != null ? _transformationService.ConstraintFix(req.Handle) : BadRequest(); }
            if (method == "POST" && path == "/api/constraint/horizontal")
            { var req = ParseBody<SingleConstraintRequest>(request); return req != null ? _transformationService.ConstraintHorizontal(req.Handle) : BadRequest(); }
            if (method == "POST" && path == "/api/constraint/vertical")
            { var req = ParseBody<SingleConstraintRequest>(request); return req != null ? _transformationService.ConstraintVertical(req.Handle) : BadRequest(); }
            if (method == "POST" && path == "/api/constraint/tangent")
            { var req = ParseBody<TangentConstraintRequest2>(request); return req != null ? _transformationService.ConstraintTangent(req.HandleLine, req.HandleCurve) : BadRequest(); }

            // === 2D CONSTRAINTS (extended) ===
            if (method == "POST" && path == "/api/constraint/perpendicular")
            { var req = ParseBody<ConstraintRequest>(request); return req != null ? _transformationService.ConstraintPerpendicular(req.Handle1, req.Handle2) : BadRequest(); }
            if (method == "POST" && path == "/api/constraint/collinear")
            { var req = ParseBody<ConstraintRequest>(request); return req != null ? _transformationService.ConstraintCollinear(req.Handle1, req.Handle2) : BadRequest(); }
            if (method == "POST" && path == "/api/constraint/concentric")
            { var req = ParseBody<ConstraintRequest>(request); return req != null ? _transformationService.ConstraintConcentric(req.Handle1, req.Handle2) : BadRequest(); }
            if (method == "POST" && path == "/api/constraint/equal")
            { var req = ParseBody<ConstraintRequest>(request); return req != null ? _transformationService.ConstraintEqual(req.Handle1, req.Handle2) : BadRequest(); }
            if (method == "POST" && path == "/api/constraint/symmetric")
            { var req = ParseBody<SymmetricConstraintRequest>(request); return req != null ? _transformationService.ConstraintSymmetric(req.Handle1, req.Handle2, req.PlaneHandle) : BadRequest(); }
            if (method == "POST" && path == "/api/constraint/distance")
            { var req = ParseBody<DistanceConstraintRequest>(request); return req != null ? _transformationService.ConstraintDistance(req.Handle1, req.Handle2, req.Distance) : BadRequest(); }
            // === SHEET METAL ===
            if (method == "POST" && path == "/api/sheetmetal/base-flange")
            { var req = ParseBody<BaseFlangeRequest>(request); return req != null ? _sheetMetalService.CreateBaseFlange(req) : BadRequest(); }
            if (method == "POST" && path == "/api/sheetmetal/edge-flange")
            { var req = ParseBody<EdgeFlangeRequest>(request); return req != null ? _sheetMetalService.CreateEdgeFlange(req) : BadRequest(); }
            if (method == "POST" && path == "/api/sheetmetal/bend")
            { var req = ParseBody<BendRequest>(request); return req != null ? _sheetMetalService.CreateBend(req.Handle, req.BendRadius) : BadRequest(); }
            if (method == "POST" && path == "/api/sheetmetal/unfold")
            { var req = ParseBody<HandlePointRequest>(request); return req != null ? _sheetMetalService.Unfold(req.Handle, req.X, req.Y) : BadRequest(); }
            if (method == "POST" && path == "/api/sheetmetal/base-plate")
            { var req = ParseBody<CreateBasePlateRequest>(request); return req != null ? _sheetMetalService.CreateBasePlate(req.X, req.Y, req.Width, req.Length, req.Thickness) : BadRequest(); }

            // === ASSEMBLY ===
            if (method == "POST" && path == "/api/assembly/insert")
            { var req = ParseBody<InsertPartRequest>(request); return req != null ? _solidService.InsertPart(req.BlockName, req.X, req.Y, req.Z) : BadRequest(); }
            if (method == "POST" && path == "/api/assembly/mate")
            { var req = ParseBody<MateRequest>(request); return req != null ? _solidService.AssemblyMate(req.Handle1, req.Handle2) : BadRequest(); }
            if (method == "POST" && path == "/api/assembly/angle")
            { var req = ParseBody<AngleConstraintRequest>(request); return req != null ? _solidService.AssemblyAngle(req.Handle1, req.Handle2, req.Angle) : BadRequest(); }
            if (method == "POST" && path == "/api/assembly/tangent")
            { var req = ParseBody<TangentConstraintRequest>(request); return req != null ? _solidService.AssemblyTangent(req.Handle1, req.Handle2) : BadRequest(); }
            if (method == "POST" && path == "/api/assembly/symmetry")
            { var req = ParseBody<SymmetryConstraintRequest>(request); return req != null ? _solidService.AssemblySymmetry(req.Handle1, req.Handle2, req.PlaneHandle) : BadRequest(); }

            // === 3D FEATURES ===
            if (method == "POST" && path == "/api/feature/hole/simple")
            { var req = ParseBody<SimpleHoleRequest>(request); return req != null ? _featureService.CreateSimpleHole(req.SolidHandle, req.Diameter, req.Depth) : BadRequest(); }
            if (method == "POST" && path == "/api/feature/hole/threaded")
            { var req = ParseBody<SimpleHoleRequest>(request); return req != null ? _featureService.CreateThreadedHole(req.SolidHandle, req.Diameter, req.Depth) : BadRequest(); }
            if (method == "POST" && path == "/api/feature/hole/standard")
            { var req = ParseBody<StandardHoleRequest>(request); return req != null ? _featureService.CreateStandardHole(req.SolidHandle, req.Diameter, req.Depth) : BadRequest(); }
            if (method == "POST" && path == "/api/feature/mirror")
            { var req = ParseBody<MirrorFeatureRequest>(request); return req != null ? _featureService.CreateMirror(req.SolidHandle, req.PlaneHandle) : BadRequest(); }
            if (method == "POST" && path == "/api/feature/pattern/rectangular")
            { var req = ParseBody<RectangularPatternRequest>(request); return req != null ? _featureService.CreateRectangularPattern(req.SolidHandle, req.FeatureHandle, req.CountX, req.SpacingX, req.CountY, req.SpacingY) : BadRequest(); }
            if (method == "POST" && path == "/api/feature/sketch")
            { var req = ParseBody<CreateSketchRequest>(request); return req != null ? _featureService.CreateSketch(req.SolidHandle) : BadRequest(); }
            if (method == "POST" && path == "/api/feature/sketch/circle")
            { var req = ParseBody<SketchCircleRequest>(request); return req != null ? _featureService.AddSketchCircle(req.SketchHandle, req.Cx, req.Cy, req.Cz, req.Radius) : BadRequest(); }
            if (method == "POST" && path == "/api/feature/sketch/line")
            { var req = ParseBody<SketchLineRequest>(request); return req != null ? _featureService.AddSketchLine(req.SketchHandle, req.X1, req.Y1, req.Z1, req.X2, req.Y2, req.Z2) : BadRequest(); }
            if (method == "POST" && path == "/api/feature/sketch/profile")
            { var req = ParseBody<CreateProfileRequest>(request); return req != null ? _featureService.CreateProfile(req.SketchHandle) : BadRequest(); }
            if (method == "POST" && path == "/api/feature/extrude")
            { var req = ParseBody<ExtrudeFeatureRequest>(request); return req != null ? _featureService.CreateExtrudeFeature(req.SolidHandle, req.ProfileHandle, req.Height, req.TaperAngle, req.Direction) : BadRequest(); }
            if (method == "POST" && path == "/api/feature/revolve")
            { var req = ParseBody<RevolveFeatureRequest>(request); return req != null ? _featureService.CreateRevolveFeature(req.SolidHandle, req.ProfileHandle, req.AxisX, req.AxisY, req.AxisZ, req.DirX, req.DirY, req.DirZ, req.Angle) : BadRequest(); }

            // === MLEADER ===
            if (method == "POST" && path == "/api/symbol/mleader")
            { var req = ParseBody<MLeaderRequest>(request); return req != null ? _symbolService.CreateMLeader(req) : BadRequest(); }

            // === MULTICAD API (main thread via MainThreadExecutor) ===
            if (method == "POST" && path == "/api/multicad/grid-axis")
            { var req = ParseBody<GridAxisRequest>(request); return req != null ? _multiCadService.CreateGridAxis(req.Type, req.OriginX, req.OriginY, req.SpacingsX, req.SpacingsY, req.NamingX, req.NamingY) : BadRequest(); }

            if (method == "POST" && path == "/api/multicad/grid-label")
            { var req = ParseBody<GridLabelRequest>(request); return req != null ? _multiCadService.CreateGridLabel(req.GridHandle, req.Label, req.AxisIndex, req.Direction) : BadRequest(); }

            if (method == "POST" && path == "/api/multicad/room")
            { var req = ParseBody<CreateRoomRequest>(request); return req != null ? _multiCadService.CreateRoom(req.X, req.Y, req.Width, req.Height, req.Name) : BadRequest(); }

            if (method == "GET" && TryMatch(path, "/api/multicad/room/{handle}", out var roomHandle))
            { return _multiCadService.GetRoomProperties(roomHandle!); }

            if (method == "POST" && path == "/api/multicad/custom-object")
            { var req = ParseBody<CustomObjectRequest>(request); return req != null ? _multiCadService.CreateCustomObject(req.ClassName, req.Properties) : BadRequest(); }

            if (method == "POST" && path == "/api/multicad/parametric")
            { var req = ParseBody<ParametricObjectRequest>(request); return req != null ? _multiCadService.CreateParametricObject(req.Type, req.Parameters) : BadRequest(); }

            if (method == "POST" && path == "/api/multicad/reactor")
            { var req = ParseBody<ReactorRequest>(request); return req != null ? _multiCadService.CreateReactor(req.EntityHandle, req.EventType) : BadRequest(); }

            if (method == "POST" && path == "/api/multicad/2d-break")
            { var req = ParseBody<Break2dRequest>(request); return req != null ? _multiCadService.Create2dBreak(req.ViewHandle, req.X1, req.Y1, req.X2, req.Y2) : BadRequest(); }

            if (method == "POST" && path == "/api/multicad/motion-preview/start")
            { var req = ParseBody<MotionPreviewRequest>(request); return req != null ? _multiCadService.StartMotionPreview(req.Handle) : BadRequest(); }

            if (method == "POST" && path == "/api/multicad/motion-preview/stop")
            { return _multiCadService.StopMotionPreview(); }

            if (method == "POST" && path == "/api/multicad/body-contour")
            { var req = ParseBody<BodyContourRequest>(request); return req != null ? _multiCadService.CreateBodyContour(req.SolidHandle) : BadRequest(); }

            if (method == "GET" && TryMatch(path, "/api/multicad/3d-faces/{handle}", out var facesHandle))
            { return _multiCadService.Check3dFaces(facesHandle!); }

            return null;
        }

        private static bool TryMatch(string path, string pattern, out string? param)
        {
            param = null;
            var regex = "^" + Regex.Replace(pattern, @"\{(\w+)\}", @"([^/]+)") + "$";
            var match = Regex.Match(path, regex, RegexOptions.IgnoreCase);
            if (!match.Success) return false;
            param = match.Groups[1].Success ? match.Groups[1].Value : null;
            return true;
        }

        private static T? ParseBody<T>(HttpListenerRequest request) where T : class
        {
            try
            {
                using var reader = new StreamReader(request.InputStream, request.ContentEncoding);
                var body = reader.ReadToEnd();
                return JsonSerializer.Deserialize<T>(body, JsonOptions);
            }
            catch (JsonException ex)
            {
                PluginEntry.DebugLog($"JSON parse error: {ex.Message}");
                return null;
            }
        }

        private static ErrorResponse BadRequest()
        {
            return new ErrorResponse { Error = "Invalid request body" };
        }

        public void Dispose()
        {
            if (_disposed) return;
            _disposed = true;
            _listener?.Stop();
            _listener?.Close();
        }
    }
}
