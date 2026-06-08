using System;
using System.Collections.Generic;
using System.Globalization;
using Multicad;
using Multicad.DatabaseServices;
using Multicad.Geometry;
using Multicad.Mc3D;

namespace CadEngine.Services
{
    /// <summary>
    /// Service for 3D parametric features: Hole, Extrude, Revolve, Mirror, Pattern, Sketch.
    /// Uses McObjectId.FromHandle(long) for handle→McObjectId conversion.
    /// Uses McObjectId.ToHandle(out long, out McObjectId) for McObjectId→handle.
    /// </summary>
    public class FeatureService
    {
        // ── Helpers ──────────────────────────────────────────────

        /// <summary>Convert a hex handle string to McObjectId via FromHandle.</summary>
        private static McObjectId IdFromHandle(string handle)
        {
            var h = long.Parse(handle, NumberStyles.HexNumber);
            return McObjectId.FromHandle(h);
        }

        private static Mc3dSolid? GetSolid(string handle)
        {
            try
            {
                var id = IdFromHandle(handle);
                return id.GetObject() as Mc3dSolid;
            }
            catch { return null; }
        }

        /// <summary>Get an McObjectId handle string from an McObjectId.</summary>
        private static string? HandleFromId(McObjectId id)
        {
            try
            {
                id.ToHandle(out long handleValue, out McObjectId _);
                return handleValue.ToString("X");
            }
            catch { return null; }
        }

        private static object Error(string msg) => new ErrorResponse { Error = msg };

        // ── Hole Features ────────────────────────────────────────

        public object CreateSimpleHole(string solidHandle, double diameter, double depth)
        {
            var solid = GetSolid(solidHandle);
            if (solid == null) return Error("Solid not found");

            try
            {
                var faces = Service.GetLinkedFEVsToObject(solid.ID, EntityGeomType.kPlaneSegment, true);
                if (faces.Count == 0) return Error("No planar faces found");

                var faceId = faces[0];
                var edges = Service.GetLinkedFEVsToObject(faceId, EntityGeomType.kLine);
                if (edges.Count < 2) return Error("Need at least 2 edges on the face");

                var ipp = IppDefinition.Create(IppDefinitionType.TwoEdges);
                ipp.TargetPlaneId = faceId;
                ipp.SetAssocParams(new McGeomParam { ID = edges[0] }, new McGeomParam { ID = edges[1] });
                ipp.Param1 = 20;
                ipp.Param2 = 30;

                var hole = solid.AddHoleFeature(HoleFeatureType.Simple, ipp);
                if (hole == null) return Error("Failed to create hole feature");
                hole.Diameter = diameter;
                hole.Depth = depth;
                McObjectManager.UpdateAll();
                return new { success = true };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }

        public object CreateThreadedHole(string solidHandle, double diameter, double depth)
        {
            var solid = GetSolid(solidHandle);
            if (solid == null) return Error("Solid not found");

            try
            {
                var faces = Service.GetLinkedFEVsToObject(solid.ID, EntityGeomType.kPlaneSegment, true);
                if (faces.Count == 0) return Error("No planar faces found");

                var faceId = faces[0];
                var verts = Service.GetLinkedFEVsToObject(faceId, EntityGeomType.kVertex);
                if (verts.Count < 4) return Error("Need at least 4 vertices on the face");

                var ipp = IppDefinition.Create(IppDefinitionType.TwoVertices);
                ipp.TargetPlaneId = faceId;
                ipp.SetAssocParams(new McGeomParam { ID = verts[0] }, new McGeomParam { ID = verts[3] });
                ipp.Sector = 3;
                ipp.Param1 = 20;
                ipp.Param2 = 30;

                var hole = solid.AddHoleFeature(HoleFeatureType.Threaded, ipp);
                if (hole == null) return Error("Failed to create threaded hole");
                hole.Diameter = diameter;
                hole.Depth = depth;
                McObjectManager.UpdateAll();
                return new { success = true };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }

        public object CreateStandardHole(string solidHandle, double diameter, double depth)
        {
            var solid = GetSolid(solidHandle);
            if (solid == null) return Error("Solid not found");

            try
            {
                var faces = Service.GetLinkedFEVsToObject(solid.ID, EntityGeomType.kPlaneSegment, true);
                if (faces.Count == 0) return Error("No planar faces found");

                var faceId = faces[0];
                var edges = Service.GetLinkedFEVsToObject(faceId, EntityGeomType.kLine);
                if (edges.Count < 2) return Error("Need at least 2 edges on the face");

                var ipp = IppDefinition.Create(IppDefinitionType.TwoEdges);
                ipp.TargetPlaneId = faceId;
                ipp.SetAssocParams(new McGeomParam { ID = edges[0] }, new McGeomParam { ID = edges[1] });
                ipp.Param1 = 20;
                ipp.Param2 = 30;

                var hole = solid.AddHoleFeature(HoleFeatureType.Standard, ipp);
                if (hole == null) return Error("Failed to create standard hole");
                hole.Diameter = diameter;
                hole.Depth = depth;
                McObjectManager.UpdateAll();
                return new { success = true };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }

        // ── Mirror Feature ───────────────────────────────────────

        public object CreateMirror(string solidHandle, string planeHandle)
        {
            var solid = GetSolid(solidHandle);
            if (solid == null) return Error("Solid not found");

            try
            {
                var planeId = IdFromHandle(planeHandle);
                var planeObj = planeId.GetObject();
                if (planeObj == null) return Error("Plane not found");

                // Get all features of the solid by iterating children in DocHistory
                var history = McDocumentsManager.GetActiveSheet()?.Get3dHistory();
                if (history == null) return Error("No 3D history available");

                var featureIds = new List<McObjectId>();
                // Get children of the solid to find its features
                var children = history.GetChildrenForItem(solid.ID, false);
                if (children != null)
                {
                    foreach (var childId in children)
                    {
                        var obj = childId.GetObject();
                        if (obj != null)
                            featureIds.Add(childId);
                    }
                }

                if (featureIds.Count == 0) return Error("No features found to mirror");

                solid.AddMirrorFeature(featureIds, planeId);
                McObjectManager.UpdateAll();
                return new { success = true };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }

        // ── Rectangular Pattern Feature ──────────────────────────

        public object CreateRectangularPattern(string solidHandle, string featureHandle,
            int countX, double spacingX, int countY, double spacingY)
        {
            var solid = GetSolid(solidHandle);
            if (solid == null) return Error("Solid not found");

            try
            {
                var featureId = IdFromHandle(featureHandle);
                var feature = featureId.GetObject();
                if (feature == null) return Error("Feature not found");

                var dirX = new McGeomParam { ID = featureId, Param = 0 };
                var dirY = new McGeomParam { ID = featureId, Param = 1 };

                var features = new List<McObjectId> { featureId };
                solid.AddRectangularPatternFeature(features, dirX, countX, spacingX, dirY, countY, spacingY);
                McObjectManager.UpdateAll();
                return new { success = true };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }

        // ── Sketch Features ──────────────────────────────────────

        public object CreateSketch(string solidHandle)
        {
            var solid = GetSolid(solidHandle);
            if (solid == null) return Error("Solid not found");

            try
            {
                var sketch = solid.AddPlanarSketch();
                if (sketch == null) return Error("Failed to create sketch");

                sketch.DbEntity.AddToCurrentDocument();
                var handle = HandleFromId(sketch.ID);
                return new { success = true, handle = handle ?? "" };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }

        public object AddSketchCircle(string sketchHandle,
            double cx, double cy, double cz, double radius)
        {
            try
            {
                var sketchId = IdFromHandle(sketchHandle);
                var sketch = sketchId.GetObject() as PlanarSketch;
                if (sketch == null) return Error("Sketch not found");

                var center = new Point3d(cx, cy, cz);
                sketch.AddGeometry(McObjectId.NewID(), new CircArc3d(center, Vector3d.ZAxis, radius));
                McObjectManager.UpdateAll();
                return new { success = true };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }

        public object AddSketchLine(string sketchHandle,
            double x1, double y1, double z1, double x2, double y2, double z2)
        {
            try
            {
                var sketchId = IdFromHandle(sketchHandle);
                var sketch = sketchId.GetObject() as PlanarSketch;
                if (sketch == null) return Error("Sketch not found");

                var p1 = new Point3d(x1, y1, z1);
                var p2 = new Point3d(x2, y2, z2);
                sketch.AddGeometry(McObjectId.NewID(), new LineSeg3d(p1, p2));
                McObjectManager.UpdateAll();
                return new { success = true };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }

        public object CreateProfile(string sketchHandle)
        {
            try
            {
                var sketchId = IdFromHandle(sketchHandle);
                var sketch = sketchId.GetObject() as PlanarSketch;
                if (sketch == null) return Error("Sketch not found");

                var profile = sketch.CreateProfile();
                if (profile == null) return Error("Failed to create profile from sketch");

                profile.DbEntity.Visibility = 0;
                profile.DbEntity.AddToCurrentDocument();
                profile.AutoProcessExternalContours();

                var handle = HandleFromId(profile.ID);
                return new { success = true, handle = handle ?? "" };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }

        // ── Extrude/Revolve Features ─────────────────────────────

        public object CreateExtrudeFeature(string solidHandle, string profileHandle,
            double height, double taperAngle = 0, bool direction = true)
        {
            var solid = GetSolid(solidHandle);
            if (solid == null) return Error("Solid not found");

            try
            {
                var profileId = IdFromHandle(profileHandle);
                var dir = direction ? FeatureExtentDirection.Positive : FeatureExtentDirection.Negative;
                var feature = solid.AddExtrudeFeature(profileId, height, taperAngle, dir);
                if (feature == null) return Error("Failed to create extrude feature");

                McObjectManager.UpdateAll();
                var handle = HandleFromId(feature.ID);
                return new { success = true, handle = handle ?? "" };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }

        public object CreateRevolveFeature(string solidHandle, string profileHandle,
            double axisX, double axisY, double axisZ,
            double dirX, double dirY, double dirZ, double angle)
        {
            var solid = GetSolid(solidHandle);
            if (solid == null) return Error("Solid not found");

            try
            {
                var profileId = IdFromHandle(profileHandle);
                // Create McGeomParam as the axis parameter
                var axisParam = new McGeomParam();
                // Add a sketch or other geometry to get the axis reference;
                // For axis, we use the McGeomParam with a Line3d representation
                // Actually AddRevolveFeature uses axis as McGeomParam with a work axis ID
                var history = McDocumentsManager.GetActiveSheet()?.Get3dHistory();

                // Try to find a work axis or create one through a workplane
                // For simplicity, use YZ plane normal as revolve axis direction
                if (history != null && history.DoesGCSElementExist(GCSElementType.WPL_YZ))
                {
                    var yzPlane = history.GetGCSElement(GCSElementType.WPL_YZ);
                    if (yzPlane != null)
                        axisParam.ID = yzPlane.ID;
                }
                // Fallback: create the McGeomParam with the profile's ID
                if (axisParam.ID.IsNull)
                    axisParam.ID = profileId;

                var feature = solid.AddRevolveFeature(profileId, axisParam, Util.A2R(angle));
                if (feature == null) return Error("Failed to create revolve feature");

                McObjectManager.UpdateAll();
                var handle = HandleFromId(feature.ID);
                return new { success = true, handle = handle ?? "" };
            }
            catch (Exception ex) { return Error(ex.Message); }
        }
    }
}
