using System;
using System.Collections.Generic;
using System.Linq;
using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;
using Teigha.Geometry;
using App = HostMgd.ApplicationServices.Application;

namespace CadEngine
{
    public class LayerService
    {
        private static Database Db => HostApplicationServices.WorkingDatabase;

        public LayersListResponse GetLayers()
        {
            var result = new LayersListResponse();
            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LayerTable)tr.GetObject(Db.LayerTableId, OpenMode.ForRead);

            foreach (ObjectId id in lt)
            {
                var lr = (LayerTableRecord)tr.GetObject(id, OpenMode.ForRead);
                result.Layers.Add(new LayerResponse
                {
                    Name = lr.Name,
                    Color = lr.Color.ColorValue.Name,
                    IsOn = !lr.IsOff,
                    IsFrozen = lr.IsFrozen,
                    IsLocked = lr.IsLocked,
                    Linetype = lr.LinetypeObjectId.IsNull ? "Continuous" : "",
                });
            }
            return result;
        }

        public SuccessResponse CreateLayer(CreateLayerRequest req)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LayerTable)tr.GetObject(Db.LayerTableId, OpenMode.ForWrite);

            if (lt.Has(req.Name))
                return new SuccessResponse { Success = false };

            var lr = new LayerTableRecord { Name = req.Name };
            lt.Add(lr);
            tr.AddNewlyCreatedDBObject(lr, true);
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        public SuccessResponse DeleteLayer(string name)
        {
            if (name == "0") return new SuccessResponse { Success = false };

            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LayerTable)tr.GetObject(Db.LayerTableId, OpenMode.ForWrite);
            if (lt.Has(name))
            {
                var lr = (LayerTableRecord)tr.GetObject(lt[name], OpenMode.ForWrite);
                lr.Erase();
                tr.Commit();
                return new SuccessResponse { Success = true };
            }
            return new SuccessResponse { Success = false };
        }

        public SuccessResponse SetCurrentLayer(string name)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LayerTable)tr.GetObject(Db.LayerTableId, OpenMode.ForRead);
            if (lt.Has(name))
            {
                Db.Clayer = lt[name];
                tr.Commit();
                return new SuccessResponse { Success = true };
            }
            return new SuccessResponse { Success = false };
        }

        public SuccessResponse SetLayerState(string name, LayerStateRequest req)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LayerTable)tr.GetObject(Db.LayerTableId, OpenMode.ForRead);
            if (!lt.Has(name)) return new SuccessResponse { Success = false };

            var lr = (LayerTableRecord)tr.GetObject(lt[name], OpenMode.ForWrite);
            if (req.On.HasValue) lr.IsOff = !req.On.Value;
            if (req.Frozen.HasValue) lr.IsFrozen = req.Frozen.Value;
            if (req.Locked.HasValue) lr.IsLocked = req.Locked.Value;
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        // ── LAYISO / LAYOFF / LAYFRZ / LAYON / LAYTHW ────────

        public LinetypesListResponse GetLinetypes()
        {
            var result = new LinetypesListResponse();
            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LinetypeTable)tr.GetObject(Db.LinetypeTableId, OpenMode.ForRead);

            foreach (ObjectId id in lt)
            {
                var lr = (LinetypeTableRecord)tr.GetObject(id, OpenMode.ForRead);
                result.Linetypes.Add(new LinetypeResponse
                {
                    Name = lr.Name,
                    Description = lr.Comments ?? "",
                });
            }
            return result;
        }

        public SuccessResponse LayerIsolate(string name)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LayerTable)tr.GetObject(Db.LayerTableId, OpenMode.ForRead);
            foreach (ObjectId id in lt)
            {
                var lr = (LayerTableRecord)tr.GetObject(id, OpenMode.ForWrite);
                if (lr.Name != name && lr.Name != "0")
                {
                    lr.IsOff = true;
                }
            }
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        public SuccessResponse LayerOff(string name)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LayerTable)tr.GetObject(Db.LayerTableId, OpenMode.ForRead);
            if (lt.Has(name))
            {
                var lr = (LayerTableRecord)tr.GetObject(lt[name], OpenMode.ForWrite);
                lr.IsOff = true;
            }
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        public SuccessResponse LayerFreeze(string name)
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LayerTable)tr.GetObject(Db.LayerTableId, OpenMode.ForRead);
            if (lt.Has(name))
            {
                var lr = (LayerTableRecord)tr.GetObject(lt[name], OpenMode.ForWrite);
                lr.IsFrozen = true;
            }
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        public SuccessResponse LayerOnAll()
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LayerTable)tr.GetObject(Db.LayerTableId, OpenMode.ForRead);
            foreach (ObjectId id in lt)
            {
                var lr = (LayerTableRecord)tr.GetObject(id, OpenMode.ForWrite);
                lr.IsOff = false;
            }
            tr.Commit();
            return new SuccessResponse { Success = true };
        }

        public SuccessResponse LayerThawAll()
        {
            using var tr = Db.TransactionManager.StartTransaction();
            var lt = (LayerTable)tr.GetObject(Db.LayerTableId, OpenMode.ForRead);
            foreach (ObjectId id in lt)
            {
                var lr = (LayerTableRecord)tr.GetObject(id, OpenMode.ForWrite);
                lr.IsFrozen = false;
            }
            tr.Commit();
            return new SuccessResponse { Success = true };
        }
    }
}
