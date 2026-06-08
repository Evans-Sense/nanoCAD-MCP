using System;
using System.Collections.Generic;
using System.Reflection;
using Multicad;
using Multicad.Mc3D;
using Multicad.DatabaseServices;

namespace MapiTest
{
    public static class AccessibilityCheck
    {
        public static string Report()
        {
            var lines = new List<string>();

            void CheckType(string name, Type t)
            {
                if (t == null)
                {
                    lines.Add($"  [MISSING] {name}");
                    return;
                }
                lines.Add($"  [OK]      {t.FullName}  (asm={t.Assembly.GetName().Name})");
            }

            lines.Add("=== Type accessibility report ===");

            CheckType("Multicad.Mc3D.Mc3dConstraint", typeof(Mc3dConstraint));
            CheckType("Multicad.Mc3D.Service", typeof(Service));
            CheckType("Multicad.McObjectId", typeof(McObjectId));
            CheckType("Multicad.McObjectComplexId", typeof(McObjectComplexId));
            CheckType("Multicad.SubentType", typeof(SubentType));
            CheckType("Multicad.Mc3D.EntityGeomType", typeof(EntityGeomType));
            CheckType("Multicad.Mc3D.Mc3dSolid", typeof(Mc3dSolid));
            CheckType("Multicad.Mc3D.ExtrudeFeature", typeof(ExtrudeFeature));
            CheckType("Multicad.DatabaseServices.Constraints.Constraints2D", typeof(Multicad.DatabaseServices.Constraints.Constraints2D));

            try
            {
                var t = typeof(Mc3dConstraint);
                lines.Add("");
                lines.Add($"=== Methods on {t.FullName} ===");
                foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.Static))
                {
                    var ps = string.Join(", ", Array.ConvertAll(m.GetParameters(), p => $"{p.ParameterType.Name} {p.Name}"));
                    lines.Add($"  {m.ReturnType.Name} {m.Name}({ps})");
                }
            }
            catch (Exception ex)
            {
                lines.Add($"  [ERROR] {ex.Message}");
            }

            return string.Join(Environment.NewLine, lines);
        }
    }
}
