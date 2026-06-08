using System;
using System.Collections.Generic;
using System.Linq;
using HostMgd.ApplicationServices;
using HostMgd.EditorInput;
using Teigha.DatabaseServices;
using Teigha.Runtime;
using App = HostMgd.ApplicationServices.Application;

namespace CadEngine
{
    public class SelectionService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;

        public EntitySelectionListResponse SelectEntities(string? entityType = null, string? layer = null, int? color = null, int maxCount = 1000)
        {
            var db = Db;
            if (db == null)
                return new EntitySelectionListResponse { Success = false, Entities = new List<EntitySelectionInfo>() };

            var editor = GetEditor();
            if (editor == null)
                return new EntitySelectionListResponse { Success = false, Entities = new List<EntitySelectionInfo>() };

            try
            {
                var filter = BuildFilter(entityType, layer, color);
                var result = filter != null
                    ? editor.SelectAll(filter)
                    : editor.SelectAll();

                if (result.Status != PromptStatus.OK || result.Value == null)
                    return new EntitySelectionListResponse { Success = true, Entities = new List<EntitySelectionInfo>() };

                var pickedEntities = result.Value;
                var entities = new List<EntitySelectionInfo>();
                int count = 0;

                using var tr = db.TransactionManager.StartTransaction();
                foreach (SelectedObject obj in pickedEntities)
                {
                    if (count >= maxCount) break;
                    if (obj == null) continue;

                    try
                    {
                        var ent = (Entity)tr.GetObject(obj.ObjectId, OpenMode.ForRead);
                        entities.Add(new EntitySelectionInfo
                        {
                            Handle = ent.Handle.ToString(),
                            Type = ent.GetRXClass().DxfName,
                            Layer = ent.Layer,
                        });
                        count++;
                    }
                    catch { }
                }
                tr.Commit();

                return new EntitySelectionListResponse { Success = true, Entities = entities };
            }
            catch (System.Exception ex)
            {
                PluginEntry.DebugLog($"SelectEntities error: {ex.Message}");
                return new EntitySelectionListResponse { Success = false, Entities = new List<EntitySelectionInfo>() };
            }
        }

        public EntitySelectionListResponse SelectByHandles(List<string> handles)
        {
            var db = Db;
            if (db == null)
                return new EntitySelectionListResponse { Success = false, Entities = new List<EntitySelectionInfo>() };

            var entities = new List<EntitySelectionInfo>();
            using var tr = db.TransactionManager.StartTransaction();

            foreach (var handleStr in handles)
            {
                try
                {
                    var handle = new Handle(Convert.ToInt64(handleStr, 16));
                    var objectId = db.GetObjectId(false, handle, 0);
                    if (objectId.IsNull || !objectId.IsValid) continue;

                    var ent = (Entity)tr.GetObject(objectId, OpenMode.ForRead);
                    entities.Add(new EntitySelectionInfo
                    {
                        Handle = ent.Handle.ToString(),
                        Type = ent.GetRXClass().DxfName,
                        Layer = ent.Layer,
                    });
                }
                catch { }
            }
            tr.Commit();

            return new EntitySelectionListResponse { Success = true, Entities = entities };
        }

        public EntityDetailInfoResponse GetEntityDetail(string handleStr)
        {
            var db = Db;
            if (db == null)
                return new EntityDetailInfoResponse { Success = false };

            try
            {
                var handle = new Handle(Convert.ToInt64(handleStr, 16));
                var objectId = db.GetObjectId(false, handle, 0);
                if (objectId.IsNull || !objectId.IsValid)
                    return new EntityDetailInfoResponse { Success = false };

                using var tr = db.TransactionManager.StartTransaction();
                var ent = (Entity)tr.GetObject(objectId, OpenMode.ForRead);

                var detail = new EntityDetailInfoResponse
                {
                    Success = true,
                    Handle = ent.Handle.ToString(),
                    Type = ent.GetRXClass().DxfName,
                    Layer = ent.Layer,
                    Color = ent.ColorIndex,
                    Linetype = ent.Linetype,
                };

                // Add geometric properties based on type
                if (ent is Line line)
                {
                    detail.Length = line.Length;
                    detail.StartX = line.StartPoint.X;
                    detail.StartY = line.StartPoint.Y;
                    detail.StartZ = line.StartPoint.Z;
                    detail.EndX = line.EndPoint.X;
                    detail.EndY = line.EndPoint.Y;
                    detail.EndZ = line.EndPoint.Z;
                }
                else if (ent is Circle circle)
                {
                    detail.Radius = circle.Radius;
                    detail.CenterX = circle.Center.X;
                    detail.CenterY = circle.Center.Y;
                    detail.CenterZ = circle.Center.Z;
                    detail.Area = Math.PI * circle.Radius * circle.Radius;
                }
                else if (ent is Arc arc)
                {
                    detail.Radius = arc.Radius;
                    detail.CenterX = arc.Center.X;
                    detail.CenterY = arc.Center.Y;
                    detail.CenterZ = arc.Center.Z;
                    detail.StartAngle = arc.StartAngle * 180.0 / Math.PI;
                    detail.EndAngle = arc.EndAngle * 180.0 / Math.PI;
                }
                else if (ent is Polyline polyline)
                {
                    detail.Area = Math.Abs(polyline.Area);
                    detail.Length = polyline.Length;
                    detail.VertexCount = polyline.NumberOfVertices;
                }
                else if (ent is DBText text)
                {
                    detail.Content = text.TextString;
                    detail.Height = text.Height;
                    detail.PositionX = text.Position.X;
                    detail.PositionY = text.Position.Y;
                }
                else if (ent is MText mtext)
                {
                    detail.Content = mtext.Contents;
                    detail.Height = mtext.TextHeight;
                    detail.PositionX = mtext.Location.X;
                    detail.PositionY = mtext.Location.Y;
                }

                tr.Commit();
                return detail;
            }
            catch
            {
                return new EntityDetailInfoResponse { Success = false };
            }
        }

        private static SelectionFilter? BuildFilter(string? entityType, string? layer, int? color)
        {
            var conditions = new List<TypedValue>();

            if (!string.IsNullOrEmpty(entityType))
                conditions.Add(new TypedValue((int)DxfCode.Start, entityType));

            if (!string.IsNullOrEmpty(layer))
                conditions.Add(new TypedValue((int)DxfCode.LayerName, layer));

            if (color.HasValue)
                conditions.Add(new TypedValue((int)DxfCode.Color, color.Value));

            return conditions.Count > 0 ? new SelectionFilter(conditions.ToArray()) : null;
        }

        private static Editor? GetEditor()
        {
            try
            {
                var doc = CadContext.ActiveDocument;
                return doc?.Editor;
            }
            catch
            {
                return null;
            }
        }
    }

    // ── Response/Request Models ───────────────────────────────

    public class SelectEntitiesRequest
    {
        public string? EntityType { get; set; }
        public string? Layer { get; set; }
        public int? Color { get; set; }
        public int MaxCount { get; set; } = 1000;
    }

    public class SelectByHandlesRequest
    {
        public List<string> Handles { get; set; } = new();
    }

    public class EntitySelectionListResponse
    {
        public bool Success { get; set; }
        public List<EntitySelectionInfo> Entities { get; set; } = new();
    }

    public class EntitySelectionInfo
    {
        public string Handle { get; set; } = "";
        public string Type { get; set; } = "";
        public string Layer { get; set; } = "";
    }

    public class EntityDetailInfoResponse
    {
        public bool Success { get; set; }
        public string Handle { get; set; } = "";
        public string Type { get; set; } = "";
        public string Layer { get; set; } = "";
        public int Color { get; set; }
        public string Linetype { get; set; } = "";

        // Geometric properties (populated based on entity type)
        public double? Length { get; set; }
        public double? Area { get; set; }
        public double? Radius { get; set; }
        public double? StartAngle { get; set; }
        public double? EndAngle { get; set; }
        public int? VertexCount { get; set; }
        public string? Content { get; set; }
        public double? Height { get; set; }
        public double? StartX { get; set; }
        public double? StartY { get; set; }
        public double? StartZ { get; set; }
        public double? EndX { get; set; }
        public double? EndY { get; set; }
        public double? EndZ { get; set; }
        public double? CenterX { get; set; }
        public double? CenterY { get; set; }
        public double? CenterZ { get; set; }
        public double? PositionX { get; set; }
        public double? PositionY { get; set; }
    }
}
