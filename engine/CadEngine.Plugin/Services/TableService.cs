using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;

namespace CadEngine.Services
{
    /// <summary>
    /// Creates tables using pure Teigha API (grid lines + text).
    /// Stores table metadata in a static dictionary keyed by table_id (GUID).
    /// McTable + PlaceObject is avoided because it requires the main CAD thread
    /// and hangs on all background-thread approaches tested (LockDocument,
    /// SynchronizationContext, STA thread).
    /// </summary>
    public class TableService
    {
        // In-memory store: table_id -> TableData
        private static readonly Dictionary<string, TableData> _tableStore = new();

        public object CreateTable(CreateTableRequest req)
        {
            try
            {
                var db = HostApplicationServices.WorkingDatabase;
                if (db == null)
                    return new ErrorResponse { Error = "No working database" };

                double startX = 0, startY = 0;
                double colWidth = req.ColumnWidth > 0 ? req.ColumnWidth : 100;
                double rowHeight = req.RowHeight > 0 ? req.RowHeight : 30;
                double textHeight = rowHeight * 0.5;

                var tableId = Guid.NewGuid().ToString("N");
                var entityHandles = new List<string>();

                using (var tr = db.TransactionManager.StartTransaction())
                {
                    var ms = (BlockTableRecord)tr.GetObject(db.CurrentSpaceId, OpenMode.ForWrite);

                    // Draw horizontal lines for row boundaries (rows+1 lines)
                    for (int i = 0; i <= req.Rows; i++)
                    {
                        double y = startY - i * rowHeight;
                        var line = new Line(
                            new Teigha.Geometry.Point3d(startX, y, 0),
                            new Teigha.Geometry.Point3d(startX + req.Columns * colWidth, y, 0)
                        );
                        AddXData(line, tableId, -1, -1, "gridline");
                        ms.AppendEntity(line);
                        tr.AddNewlyCreatedDBObject(line, true);
                        entityHandles.Add(line.Handle.Value.ToString());
                    }

                    // Draw vertical lines for column boundaries (cols+1 lines)
                    for (int j = 0; j <= req.Columns; j++)
                    {
                        double x = startX + j * colWidth;
                        var line = new Line(
                            new Teigha.Geometry.Point3d(x, startY, 0),
                            new Teigha.Geometry.Point3d(x, startY - req.Rows * rowHeight, 0)
                        );
                        AddXData(line, tableId, -1, -1, "gridline");
                        ms.AppendEntity(line);
                        tr.AddNewlyCreatedDBObject(line, true);
                        entityHandles.Add(line.Handle.Value.ToString());
                    }

                    // Add text for cell values
                    if (req.Cells != null)
                    {
                        foreach (var cell in req.Cells)
                        {
                            if (cell.RowIndex < req.Rows && cell.ColumnIndex < req.Columns && !string.IsNullOrEmpty(cell.Value))
                            {
                                double cx = startX + cell.ColumnIndex * colWidth + colWidth * 0.1;
                                double cy = startY - cell.RowIndex * rowHeight - rowHeight * 0.35;
                                var text = new DBText
                                {
                                    Position = new Teigha.Geometry.Point3d(cx, cy, 0),
                                    Height = textHeight,
                                    TextString = cell.Value
                                };
                                AddXData(text, tableId, cell.RowIndex, cell.ColumnIndex, "celltext");
                                ms.AppendEntity(text);
                                tr.AddNewlyCreatedDBObject(text, true);
                                entityHandles.Add(text.Handle.Value.ToString());
                            }
                        }
                    }

                    tr.Commit();
                }

                // Store metadata
                var tableData = new TableData
                {
                    Rows = req.Rows,
                    Columns = req.Columns,
                    RowHeight = rowHeight,
                    ColumnWidth = colWidth,
                    EntityHandles = entityHandles,
                    Cells = req.Cells?.Select(c => new CellData
                    {
                        RowIndex = c.RowIndex,
                        ColumnIndex = c.ColumnIndex,
                        Value = c.Value
                    }).ToList() ?? new List<CellData>(),
                };
                _tableStore[tableId] = tableData;

                return new TableCreateResponse
                {
                    Success = true,
                    Type = "Table (Teigha)",
                    Handle = tableId,
                };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object GetTableInfo(string handle)
        {
            if (string.IsNullOrEmpty(handle) || !_tableStore.TryGetValue(handle, out var data))
            {
                return new ErrorResponse { Error = $"Table '{handle}' not found. Tables are stored in memory and lost on server restart." };
            }

            var result = new TableInfoResponse
            {
                Success = true,
                Rows = data.Rows,
                Columns = data.Columns,
                RowHeight = data.RowHeight,
                ColumnWidth = data.ColumnWidth,
            };

            if (data.Cells != null)
            {
                foreach (var cell in data.Cells)
                {
                    result.Cells.Add(new CellResponse
                    {
                        RowIndex = cell.RowIndex,
                        ColumnIndex = cell.ColumnIndex,
                        Value = cell.Value,
                    });
                }
            }

            return result;
        }

        public object EditTableCell(string handle, EditTableCellRequest req)
        {
            if (string.IsNullOrEmpty(handle) || !_tableStore.TryGetValue(handle, out var data))
            {
                return new ErrorResponse { Error = $"Table '{handle}' not found" };
            }

            try
            {
                var db = HostApplicationServices.WorkingDatabase;
                if (db == null)
                    return new ErrorResponse { Error = "No working database" };

                using (var tr = db.TransactionManager.StartTransaction())
                {
                    // Find and update the DBText for the requested cell
                    bool found = false;
                    foreach (var entHandleStr in data.EntityHandles)
                    {
                        var entHandle = new Handle(long.Parse(entHandleStr, NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                        var objId = db.GetObjectId(false, entHandle, 0);
                        if (objId.IsNull) continue;

                        try
                        {
                            var obj = tr.GetObject(objId, OpenMode.ForWrite);
                            if (obj is DBText text)
                            {
                                // Parse XData to check row/col
                                int row = -1, col = -1;
                                if (TryParseCellXData(obj.XData, out row, out col) && row == req.RowIndex && col == req.ColumnIndex)
                                {
                                    text.TextString = req.Value;
                                    found = true;
                                    break;
                                }
                            }
                        }
                        catch
                        {
                            // Entity may have been erased; skip
                        }
                    }

                    tr.Commit();

                    if (!found)
                    {
                        return new ErrorResponse { Error = $"Cell ({req.RowIndex},{req.ColumnIndex}) not found in table" };
                    }

                    // Update in-memory store
                    var existingCell = data.Cells?.FirstOrDefault(c => c.RowIndex == req.RowIndex && c.ColumnIndex == req.ColumnIndex);
                    if (existingCell != null)
                    {
                        existingCell.Value = req.Value;
                    }
                    else
                    {
                        data.Cells ??= new List<CellData>();
                        data.Cells.Add(new CellData { RowIndex = req.RowIndex, ColumnIndex = req.ColumnIndex, Value = req.Value });
                    }

                    return new SuccessResponse { Success = true };
                }
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        public object DeleteTable(string handle)
        {
            if (string.IsNullOrEmpty(handle) || !_tableStore.TryGetValue(handle, out var data))
            {
                return new ErrorResponse { Error = $"Table '{handle}' not found" };
            }

            try
            {
                var db = HostApplicationServices.WorkingDatabase;
                if (db == null)
                    return new ErrorResponse { Error = "No working database" };

                using (var tr = db.TransactionManager.StartTransaction())
                {
                    var ms = (BlockTableRecord)tr.GetObject(db.CurrentSpaceId, OpenMode.ForWrite);

                    foreach (var entHandleStr in data.EntityHandles)
                    {
                        var entHandle = new Handle(long.Parse(entHandleStr, NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                        var objId = db.GetObjectId(false, entHandle, 0);
                        if (objId.IsNull) continue;

                        try
                        {
                            var obj = tr.GetObject(objId, OpenMode.ForWrite);
                            obj.Erase();
                        }
                        catch
                        {
                            // Entity may already be erased; skip
                        }
                    }

                    tr.Commit();
                }

                _tableStore.Remove(handle);
                return new SuccessResponse { Success = true };
            }
            catch (Exception ex)
            {
                return new ErrorResponse { Error = ex.Message };
            }
        }

        /// <summary>
        /// Adds XData to an entity with table metadata.
        /// XData structure:
        ///   AppName: "MC_TABLE"
        ///   Data: (1002, "{"), (1000, tableId), (1070, row), (1070, col), (1000, type), (1002, "}")
        /// </summary>
        private static void AddXData(Entity ent, string tableId, int row, int col, string type)
        {
            var rb = new ResultBuffer(
                new TypedValue((int)DxfCode.ExtendedDataRegAppName, "MC_TABLE"),
                new TypedValue((int)DxfCode.ExtendedDataAsciiString, tableId),
                new TypedValue((int)DxfCode.ExtendedDataInteger16, (short)row),
                new TypedValue((int)DxfCode.ExtendedDataInteger16, (short)col),
                new TypedValue((int)DxfCode.ExtendedDataAsciiString, type)
            );
            ent.XData = rb;
        }

        /// <summary>
        /// Tries to parse row/col from XData.
        /// Returns false if the XData doesn't have MC_TABLE app or can't parse.
        /// </summary>
        private static bool TryParseCellXData(ResultBuffer xdata, out int row, out int col)
        {
            row = -1;
            col = -1;
            if (xdata == null) return false;

            int index = 0;
            foreach (var tv in xdata)
            {
                // Skip the app name (first entry)
                if (index == 0) { index++; continue; }

                if (tv.TypeCode == (int)DxfCode.ExtendedDataAsciiString && index == 1)
                {
                    // tableId — skip
                    index++;
                }
                else if (tv.TypeCode == (int)DxfCode.ExtendedDataInteger16 && index == 2)
                {
                    row = (short)tv.Value;
                    index++;
                }
                else if (tv.TypeCode == (int)DxfCode.ExtendedDataInteger16 && index == 3)
                {
                    col = (short)tv.Value;
                    index++;
                }
                else
                {
                    index++;
                }
            }

            return row >= 0 && col >= 0;
        }
    }

    public class CreateTableRequest
    {
        public int Rows { get; set; } = 3;
        public int Columns { get; set; } = 3;
        public double RowHeight { get; set; } = 30;
        public double ColumnWidth { get; set; } = 100;
        public List<CellData>? Cells { get; set; }
    }

    public class EditTableCellRequest
    {
        public int RowIndex { get; set; }
        public int ColumnIndex { get; set; }
        public string Value { get; set; } = "";
    }

    public class CellData
    {
        public int RowIndex { get; set; }
        public int ColumnIndex { get; set; }
        public string Value { get; set; } = "";
    }

    public class TableCreateResponse
    {
        public bool Success { get; set; }
        public string Type { get; set; } = "";
        public string Handle { get; set; } = "";
    }

    public class CellResponse
    {
        public int RowIndex { get; set; }
        public int ColumnIndex { get; set; }
        public string Value { get; set; } = "";
    }

    public class TableInfoResponse
    {
        public bool Success { get; set; }
        public int Rows { get; set; }
        public int Columns { get; set; }
        public double RowHeight { get; set; }
        public double ColumnWidth { get; set; }
        public List<CellResponse> Cells { get; set; } = new();
    }

    // In-memory metadata for a table group
    internal class TableData
    {
        public int Rows { get; set; }
        public int Columns { get; set; }
        public double RowHeight { get; set; }
        public double ColumnWidth { get; set; }
        public List<string> EntityHandles { get; set; } = new();
        public List<CellData>? Cells { get; set; }
    }
}
