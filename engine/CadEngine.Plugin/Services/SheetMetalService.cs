using HostMgd.ApplicationServices;
using Teigha.DatabaseServices;
using Teigha.Geometry;

namespace CadEngine
{
    public class SheetMetalService
    {
        // Sheet metal commands (EXTRUDE, FILLETEDGE, FLATSHOT) require Plus/Pro edition
        // and crash free edition via SendCommand. Return graceful error.

        public SuccessResponse CreateBaseFlange(BaseFlangeRequest req)
            => new SuccessResponse { Success = false, Error = "Sheet metal not supported in this edition" };

        public SuccessResponse CreateEdgeFlange(EdgeFlangeRequest req)
            => new SuccessResponse { Success = false, Error = "Sheet metal not supported in this edition" };

        public SuccessResponse CreateBend(string solidHandle, double bendRadius)
            => new SuccessResponse { Success = false, Error = "Sheet metal not supported in this edition" };

        public SuccessResponse Unfold(string solidHandle, double x, double y)
            => new SuccessResponse { Success = false, Error = "Sheet metal not supported in this edition" };

        public SuccessResponse CreateBasePlate(double x, double y, double width, double length, double thickness)
            => new SuccessResponse { Success = false, Error = "Sheet metal not supported in this edition" };
    }
}
