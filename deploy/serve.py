import icechunk
import xarray as xr
from fastapi.middleware.cors import CORSMiddleware
import xpublish

from xpublish_tiles.xpublish.tiles.plugin import TilesPlugin
from xpublish_tiles.xpublish.wms.plugin import WMSPlugin

DATASETS_CONFIG = [
    ("ecmwf-ifs-ens-forecast", "dynamical-ecmwf-ifs-ens", "ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk/"),
    ("noaa-gefs-analysis", "dynamical-noaa-gefs", "noaa-gefs-analysis/v0.1.2.icechunk/"),
    ("noaa-gefs-forecast", "dynamical-noaa-gefs", "noaa-gefs-forecast-35-day/v0.2.0.icechunk/"),
    ("noaa-gfs-analysis", "dynamical-noaa-gfs", "noaa-gfs-analysis/v0.1.0.icechunk/"),
    ("noaa-gfs-forecast", "dynamical-noaa-gfs", "noaa-gfs-forecast/v0.2.7.icechunk/"),
    ("noaa-hrrr-analysis-v0-1-0", "dynamical-noaa-hrrr", "noaa-hrrr-analysis/v0.1.0.icechunk/"),
    ("noaa-hrrr-analysis-v0-2-0", "dynamical-noaa-hrrr", "noaa-hrrr-analysis/v0.2.0.icechunk/"),
    ("noaa-hrrr-forecast", "dynamical-noaa-hrrr", "noaa-hrrr-forecast-48-hour/v0.1.0.icechunk/"),
]


def open_dataset(dataset_id: str, bucket: str, prefix: str) -> xr.Dataset:
    storage = icechunk.s3_storage(
        bucket=bucket, prefix=prefix, region="us-west-2", anonymous=True
    )
    repo = icechunk.Repository.open(storage)
    session = repo.readonly_session("main")
    ds = xr.open_zarr(session.store, chunks=None)
    ds.attrs["_xpublish_id"] = dataset_id
    return ds


datasets = {
    dataset_id: open_dataset(dataset_id, bucket, prefix)
    for dataset_id, bucket, prefix in DATASETS_CONFIG
}

rest = xpublish.Rest(
    datasets=datasets,
    plugins={"tiles": TilesPlugin(), "wms": WMSPlugin()},
)
rest.app.add_middleware(CORSMiddleware, allow_origins=["*"])


@rest.app.get("/health")
def health():
    return {"status": "ok"}


app = rest.app
