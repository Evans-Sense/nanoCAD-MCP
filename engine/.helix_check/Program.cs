using System;
using System.Linq;
using System.Reflection;
using System.Collections.Generic;

class Program {
    static void Main() {
        // Just check AddToCurrentDocument availability
        var paths = new[] {
            @"F:\nanoCAD\NC_SDK_RU_26.0.7228.4926.8429\include-x64\mapimgd.dll",
            @"F:\nanoCAD\NC_SDK_RU_26.0.7228.4926.8429\include-x64\hostmgd.dll",
            @"F:\nanoCAD\NC_SDK_RU_26.0.7228.4926.8429\include-x64\hostdbmgd.dll",
            typeof(object).Assembly.Location,
        };
        var resolver = new PathAssemblyResolver(paths.Where(f => System.IO.File.Exists(f)));
        using var mlc = new MetadataLoadContext(resolver, "System.Private.CoreLib");
        var asm = mlc.LoadFromAssemblyPath(@"F:\nanoCAD\NC_SDK_RU_26.0.7228.4926.8429\include-x64\mapimgd.dll");
        
        // Find McRoom
        foreach (var t in asm.GetExportedTypes().Where(t => t.Name == "McRoom").Take(1)) {
            Console.WriteLine("=== McRoom methods ===");
            foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.Instance).Take(40)) {
                try { Console.WriteLine($"  {m.ReturnType.Name} {m.Name}({string.Join(",", Array.ConvertAll(m.GetParameters(), p => p.ParameterType.Name))})"); } catch {}
            }
        }
        
        // Find Polyline3d in Multicad.Geometry vs Teigha
        foreach (var t in asm.GetExportedTypes().Where(t => t.Name == "Polyline3d").Take(2)) {
            Console.WriteLine($"\n=== Polyline3d ({t.Namespace}) methods ===");
            foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.Instance).Take(15)) {
                try { Console.WriteLine($"  {m.ReturnType.Name} {m.Name}({string.Join(",", Array.ConvertAll(m.GetParameters(), p => p.ParameterType.Name))})"); } catch {}
            }
            foreach (var p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance).Take(10)) {
                try { Console.WriteLine($"  prop {p.PropertyType.Name} {p.Name}"); } catch {}
            }
        }
    }
}
