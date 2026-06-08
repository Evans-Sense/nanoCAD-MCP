using System;
using System.Collections.Generic;
using System.Linq;
using Teigha.DatabaseServices;
using HostMgd.ApplicationServices;
using Multicad;
using Multicad.DatabaseServices;
using Multicad.Symbols;
using Multicad.Architecture;
using Multicad.Objects;
using Multicad.Geometry;
using Multicad.ApplicationServices;
using App = HostMgd.ApplicationServices.Application;

namespace CadEngine
{
    public class MultiCadService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;

        // ── Grid Axis (rectangular) ────────────────────────
        public object CreateGridAxis(string type, double originX, double originY,
                                     List<double> spacingsX, List<double> spacingsY,
                                     string namingX, string namingY)
        {
            return MainThreadExecutor.Execute(() =>
            {
                try
                {
                    if (type == "polar")
                    {
                        var grPol = new McSpdsGridPolar();
                        grPol.DbEntity.AddToCurrentDocument();
                        return new { success = true, message = "Polar grid axis created" };
                    }

                    var grRect = new McSpdsGridRect();
                    var axMetsX = grRect.getAxisMethods(AxisGridKind.AxisGridKind_X);
                    axMetsX.AddRange(spacingsX[0], (uint)spacingsX.Count);
                    var axMetsY = grRect.getAxisMethods(AxisGridKind.AxisGridKind_Y);
                    axMetsY.AddRange(spacingsY[0], (uint)spacingsY.Count);
                    grRect.DbEntity.AddToCurrentDocument();
                    return new { success = true, message = "Rectangular grid axis created" };
                }
                catch (Exception ex)
                {
                    return new { success = false, error = ex.Message };
                }
            });
        }

        // ── Grid Label ──────────────────────────────────────
        public object CreateGridLabel(string gridHandle, string label,
                                      int axisIndex, string direction)
        {
            return MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var dir = direction == "Y"
                        ? AxisGridKind.AxisGridKind_Y
                        : AxisGridKind.AxisGridKind_X;
                    var objs = ObjectFilter.Create(true)
                        .AddType(typeof(McSpdsGridRect)).GetObjects().ToArray();
                    foreach (var mcId in objs)
                    {
                        var gridEnt = mcId.GetObject() as McEntitySpdsGrid;
                        if (gridEnt == null) continue;
                        var axMets = gridEnt.getAxisMethods(dir);
                        if (axisIndex >= 0 && axisIndex < axMets.Count)
                        {
                            var axis = axMets.GetAxis((uint)axisIndex);
                            if (axis != null && axis.Methods != null)
                            {
                                axis.Methods.Markers.NamingType =
                                    Chunk_naming_type.Chunk_naming_type_any;
                                axis.Methods.Markers.First.Value = label;
                            }
                        }
                        return new { success = true };
                    }
                    return new { success = false, error = "Grid not found" };
                }
                catch (Exception ex)
                {
                    return new { success = false, error = ex.Message };
                }
            });
        }

        // ── Room ────────────────────────────────────────────
        public object CreateRoom(double x, double y, double width,
                                 double height, string? name)
        {
            return MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var room = new McRoom();
                    var extSquare = new Multicad.Geometry.Polyline3d();
                    extSquare.Vertices.AddVertex(new Point3d(x, y, 0));
                    extSquare.Vertices.AddVertex(new Point3d(x, y + height, 0));
                    extSquare.Vertices.AddVertex(
                        new Point3d(x + width, y + height, 0));
                    extSquare.Vertices.AddVertex(new Point3d(x + width, y, 0));
                    extSquare.SetClosed(true);

                    if (room.Loops.Count > 0)
                    {
                        room.Loops[0].External = extSquare;
                        room.DrawBoundary = true;
                    }

                    room.DbEntity.AddToCurrentDocument();
                    return new { success = true, message = "Room created" };
                }
                catch (Exception ex)
                {
                    return new { success = false, error = ex.Message };
                }
            });
        }

        public object GetRoomProperties(string handle)
        {
            return MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var rooms = ObjectFilter.Create(true)
                        .AddType(McRoom.TypeID).GetObjects().ToArray();
                    foreach (var mcId in rooms)
                    {
                        var room = mcId.GetObject() as McRoom;
                        if (room == null) continue;

                        double area = 0;
                        foreach (var loop in room.Loops)
                        {
                            area += loop.External.GetArea();
                            if (loop.Internal != null)
                            {
                                foreach (var inner in loop.Internal)
                                    area -= inner.GetArea();
                            }
                        }

                        var result = new Dictionary<string, object>
                        {
                            ["area"] = area,
                            ["loopCount"] = room.Loops.Count,
                            ["drawBoundary"] = room.DrawBoundary,
                        };
                        return new { success = true, room = result };
                    }
                    return new { success = false, error = "Room not found" };
                }
                catch (Exception ex)
                {
                    return new { success = false, error = ex.Message };
                }
            });
        }

        // ── Custom Object (stub) ────────────────────────────
        public object CreateCustomObject(string className,
                                         Dictionary<string, object>? properties)
        {
            return new { success = false,
                error = "Custom objects require full MultiCAD class registration." };
        }

        public object ModifyCustomObject(string handle,
                                         Dictionary<string, object>? properties)
        {
            return new { success = false,
                error = "Modifying custom objects requires direct MultiCAD API." };
        }

        // ── Parametric Object (stub) ────────────────────────
        public object CreateParametricObject(string type,
                                             Dictionary<string, object>? parameters)
        {
            return new { success = false,
                error = "Parametric objects require McParametricCalculator." };
        }

        public object UpdateParametric(string handle)
        {
            return new { success = false,
                error = "Parametric update requires McParametricObject API." };
        }

        // ── Reactors (stub) ─────────────────────────────────
        public object CreateReactor(string entityHandle, string eventType)
        {
            return new { success = false,
                error = "Reactors require a custom McNotifyReactor subclass." };
        }

        // ── Motion Preview (stub) ───────────────────────────
        public object StartMotionPreview(string handle)
        {
            return new { success = false,
                error = "Motion preview requires Mc3dAnimationManager integration." };
        }

        public object StopMotionPreview()
        {
            return new { success = true,
                message = "Motion preview stop requested." };
        }

        // ── 2D Break Symbol ─────────────────────────────────
        public object Create2dBreak(string viewHandle, double x1, double y1,
                                    double x2, double y2)
        {
            return MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var breakSym = new McConnectionBreak();
                    breakSym.DbEntity.AddToCurrentDocument();
                    return new { success = true,
                        message = "2D break symbol created" };
                }
                catch (Exception ex)
                {
                    return new { success = false, error = ex.Message };
                }
            });
        }

        // ── Body Contour (stub) ─────────────────────────────
        public object CreateBodyContour(string solidHandle)
        {
            return new { success = false,
                error = "Body contour requires McContourBuilder API." };
        }

        // ── Grid Axis Labels ────────────────────────────────
        public object SetGridLabel(string gridType, int index,
                                   string label, string direction)
        {
            return MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var targetType = gridType == "polar"
                        ? typeof(McSpdsGridPolar)
                        : typeof(McSpdsGridRect);
                    var objs = ObjectFilter.Create(true)
                        .AddType(targetType).GetObjects().ToArray();
                    if (objs.Length == 0)
                        return new { success = false,
                            error = "No grid axis found" };

                    var gridEnt = objs[0].GetObject() as McEntitySpdsGrid;
                    if (gridEnt == null)
                        return new { success = false,
                            error = "Not a grid axis" };

                    var dir = direction == "Y"
                        ? AxisGridKind.AxisGridKind_Y
                        : AxisGridKind.AxisGridKind_X;
                    var axMets = gridEnt.getAxisMethods(dir);

                    if (index >= 0 && index < axMets.Count)
                    {
                        var axis = axMets.GetAxis((uint)index);
                        if (axis != null && axis.Methods != null)
                        {
                            axis.Methods.Markers.NamingType =
                                Chunk_naming_type.Chunk_naming_type_any;
                            axis.Methods.Markers.First.Value = label;
                        }
                    }

                    axMets.NamingMode = Chunk_naming_mode.Chunk_naming_mode_manual;
                    return new { success = true };
                }
                catch (Exception ex)
                {
                    return new { success = false, error = ex.Message };
                }
            });
        }

        // ── 3D Faces via Teigha Brep ────────────────────────
        public object Check3dFaces(string handle)
        {
            return MainThreadExecutor.Execute(() =>
            {
                try
                {
                    if (!long.TryParse(handle,
                        System.Globalization.NumberStyles.HexNumber,
                        null, out var h))
                        return new { success = false,
                            error = "Invalid handle" };

                    using var tr = Db.TransactionManager.StartTransaction();
                    var id = Db.GetObjectId(false, new Handle(h), 0);
                    if (id.IsNull)
                        return new { success = false,
                            error = "Entity not found" };

                    var ent = tr.GetObject(id, OpenMode.ForRead) as Entity;
                    if (ent == null)
                        return new { success = false,
                            error = "Not an entity" };

                    // Use Teigha Brep for face enumeration
                    var result = new List<object>();
                    try
                    {
                        var brepType = Type.GetType(
                            "Teigha.Brep.Brep, hostdbmgd");
                        if (brepType == null)
                            return new { success = false,
                                error = "Brep API not available" };

                        var brep = Activator.CreateInstance(brepType, ent);
                        var facesProp = brepType.GetProperty("Faces");
                        if (facesProp != null)
                        {
                            var faces = facesProp.GetValue(brep) as System.Collections.IEnumerable;
                            if (faces != null)
                            {
                                foreach (var face in faces)
                                {
                                    var areaProp = face.GetType()
                                        .GetProperty("Area");
                                    if (areaProp != null)
                                    {
                                        result.Add(new
                                        {
                                            area = (double)areaProp.GetValue(face)
                                        });
                                    }
                                }
                            }
                        }
                    }
                    catch
                    {
                        return new { success = false,
                            error = "Brep API not available" };
                    }

                    tr.Commit();
                    return new { success = true,
                        faces = result, count = result.Count };
                }
                catch (Exception ex)
                {
                    return new { success = false, error = ex.Message };
                }
            });
        }
    }
}
