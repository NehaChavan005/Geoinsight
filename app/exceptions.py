"""Application-level exceptions.

These live in Member B's scope and are the ONLY error vocabulary the API
surface uses.  Member A's processing layer may raise ``DataNotFoundError``
when raster data is absent; no raw tracebacks ever reach API clients.
"""


class DistrictNotFoundError(Exception):
    def __init__(self, district_id: str):
        self.district_id = district_id
        super().__init__(f"District '{district_id}' is not supported.")


class DataNotFoundError(Exception):
    """A required dataset/boundary file is missing or empty.

    Accepts both positional and keyword styles, e.g.::

        DataNotFoundError("Sentinel-2", "kamrup", "2026-06")
        DataNotFoundError(dataset="sentinel2", district="kamrup", month="2026-06")
    """

    def __init__(self, dataset: str, district: str = "", month: str = ""):
        self.dataset_name = dataset
        self.district_id = district
        self.month = month
        msg = f"{dataset} data is unavailable for district '{district}'"
        if month:
            msg += f" (month: {month})"
        super().__init__(msg)


class InvalidMonthError(Exception):
    def __init__(self, month: str):
        self.month = month
        super().__init__(f"Invalid month format '{month}'. Must use YYYY-MM.")


class ProcessingError(Exception):
    """Generic failure inside the geospatial processing layer."""

    def __init__(self, message: str, dataset: str = ""):
        self.dataset = dataset
        super().__init__(message)


class ProcessingNotConnectedError(Exception):
    """Member A's processing functions have not been wired to the adapter yet.

    Raised by ``app.services.processing_adapter`` when the expected Member A
    function is not present.  No indicator value is ever fabricated; the API
    reports the dataset as unavailable until Member A connects the function.
    """

    def __init__(self, function_name: str):
        self.function_name = function_name
        super().__init__(
            f"Geospatial processing function '{function_name}' is not connected yet."
        )