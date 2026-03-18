import asyncio
import logging
from typing import Dict

import icechunk
import pystac
import xarray as xr
import xpublish
from fastapi.middleware.cors import CORSMiddleware
from xpublish.plugins import load_default_plugins

from xpublish_edr import CfEdrPlugin
from xpublish_tiles.xpublish.tiles.plugin import TilesPlugin
from xpublish_tiles.xpublish.wms.plugin import WMSPlugin

CATALOG_URL = "https://r2-pub.openscicomp.io/stac/dynamical/catalog.json"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("serve")


def open_dataset(item: pystac.Item) -> xr.Dataset:
    # Find icechunk asset
    asset = next(
        (
            a
            for a in item.assets.values()
            if a.media_type == "application/vnd.zarr+icechunk"
            or "icechunk" in (a.title or "").lower()
        ),
        None,
    )
    if not asset:
        raise ValueError(f"No icechunk asset found in item {item.id}")

    href = asset.href
    parts = href.removeprefix("s3://").split("/", 1)
    bucket = parts[0]
    prefix = parts[1]

    storage = icechunk.s3_storage(
        bucket=bucket, prefix=prefix, region="us-west-2", anonymous=True
    )
    repo = icechunk.Repository.open(storage)
    session = repo.readonly_session("main")
    ds = xr.open_zarr(session.store, chunks=None)
    ds.attrs["_xpublish_id"] = item.id
    return ds


def fetch_datasets() -> Dict[str, xr.Dataset]:
    logger.info(f"Fetching datasets from {CATALOG_URL}")
    try:
        catalog = pystac.Catalog.from_file(CATALOG_URL)
        new_datasets = {}
        for item in catalog.get_all_items():
            try:
                new_datasets[item.id] = open_dataset(item)
                logger.info(f"Loaded dataset: {item.id}")
            except Exception as e:
                logger.error(f"Error loading dataset {item.id}: {e}")
        return new_datasets
    except Exception as e:
        logger.error(f"Error fetching catalog: {e}")
        return {}


# Initialize datasets synchronously at startup
datasets = fetch_datasets()

rest = xpublish.Rest(
    datasets=datasets,
    plugins={
        **load_default_plugins(),
        "edr": CfEdrPlugin(),
        "tiles": TilesPlugin(),
        "wms": WMSPlugin(),
    },
)
rest.app.add_middleware(CORSMiddleware, allow_origins=["*"])


@rest.app.on_event("startup")
async def schedule_refresh():
    async def refresh_task():
        while True:
            await asyncio.sleep(3600)  # Refresh every hour
            try:
                new_datasets = await asyncio.to_thread(fetch_datasets)
                if new_datasets:
                    # xpublish.Rest._datasets is the internal mapping
                    rest._datasets.clear()
                    rest._datasets.update(new_datasets)
                    logger.info(f"Successfully refreshed {len(new_datasets)} datasets")
            except Exception as e:
                logger.error(f"Background refresh failed: {e}")

    asyncio.create_task(refresh_task())


@rest.app.get("/health")
def health():
    return {"status": "ok", "datasets": list(rest._datasets.keys())}


app = rest.app
