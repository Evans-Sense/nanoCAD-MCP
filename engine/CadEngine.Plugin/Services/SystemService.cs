using System;
using System.Collections.Generic;
using System.Drawing.Text;
using System.IO;
using HostMgd.ApplicationServices;
using App = HostMgd.ApplicationServices.Application;

namespace CadEngine
{
    public class SystemService
    {
        public HealthResponse GetHealth()
        {
            return new HealthResponse
            {
                Status = "ok",
                Version = App.Version.ToString(),
                ActiveDocuments = App.DocumentManager.Count,
            };
        }

        public SystemInfoResponse GetInfo()
        {
            var edition = DetectEdition();
            return new SystemInfoResponse
            {
                Version = App.Version.ToString(),
                Product = App.Version.ToString(),
                LicenseType = edition,
            };
        }

        private string DetectEdition()
        {
            // Detect nanoCAD edition by testing for Plus/Pro-only types.
            // Free edition lacks many Multicad.* assemblies.
            try
            {
                var weldType = Type.GetType("Multicad.Symbols.McIsoWeld, mapimgd");
                if (weldType == null)
                    return "Free";

                var cad3dType = Type.GetType("Multicad.Mc3D.Solid3D, mapimgd");
                if (cad3dType == null)
                    return "Free";

                // Check for Pro-only types (e.g., sheet metal)
                var sheetMetalType = Type.GetType("Multicad.Mc3D.SheetMetalPart, mapimgd");
                if (sheetMetalType == null)
                    return "Plus";

                return "Pro";
            }
            catch
            {
                return "Free";
            }
        }

        public FontsListResponse GetFonts()
        {
            var result = new FontsListResponse();
            try
            {
                using var fonts = new InstalledFontCollection();
                foreach (var family in fonts.Families)
                {
                    result.Fonts.Add(new FontInfoResponse
                    {
                        Name = family.Name,
                        Type = "truetype",
                    });
                }
            }
            catch
            {
                // Font enumeration failed; return empty list
            }

            // Also try scanning nanoCAD font paths for SHX files
            try
            {
                var fontPaths = (string[])App.GetSystemVariable("FontPaths");
                if (fontPaths != null)
                {
                    foreach (var dir in fontPaths)
                    {
                        if (Directory.Exists(dir))
                        {
                            foreach (var shx in Directory.GetFiles(dir, "*.shx"))
                            {
                                var name = Path.GetFileNameWithoutExtension(shx);
                                // Avoid duplicates with TrueType
                                if (!result.Fonts.Exists(f => f.Name.Equals(name, StringComparison.OrdinalIgnoreCase)))
                                {
                                    result.Fonts.Add(new FontInfoResponse
                                    {
                                        Name = name,
                                        Type = "shx",
                                    });
                                }
                            }
                        }
                    }
                }
            }
            catch
            {
                // SHX enumeration is best-effort
            }

            return result;
        }

        public CommandResponse ExecuteCommand(string command)
        {
            // Execute on main thread with safety wrapper.
            // Use synchronous Editor.Command() instead of SendStringToExecute
            // so exceptions are caught by the try-catch block.
            var result = MainThreadExecutor.Execute(() =>
            {
                try
                {
                    var doc = CadContext.ActiveDocument;
                    if (doc == null)
                        return (object?)new CommandResponse
                        {
                            Command = command,
                            Output = "No active document",
                        };
                    // Use Editor.Command (synchronous, not async like SendStringToExecute)
                    // Add ^C^C prefix to cancel any pending interactive command
                    doc.Editor.Command("^C^C" + command);
                    return (object?)new CommandResponse
                    {
                        Command = command,
                        Output = "Command executed on main thread",
                    };
                }
                catch (Exception ex)
                {
                    PluginEntry.DebugLog($"ExecuteCommand error: {ex.Message}");
                    return (object?)new CommandResponse
                    {
                        Command = command,
                        Output = $"Error: {ex.Message}",
                    };
                }
            });
            return result as CommandResponse ?? new CommandResponse { Command = command, Output = "Main thread executor returned null" };
        }

        public VariableResponse GetVariable(string name)
        {
            try
            {
                var value = App.GetSystemVariable(name)?.ToString();
                return new VariableResponse { Name = name, Value = value };
            }
            catch
            {
                return new VariableResponse { Name = name, Value = null };
            }
        }

        public SuccessResponse SetVariable(string name, string value)
        {
            try
            {
                App.SetSystemVariable(name, value);
                return new SuccessResponse { Success = true };
            }
            catch
            {
                return new SuccessResponse { Success = false };
            }
        }
    }
}
