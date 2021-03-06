from typing import Dict, Iterable, List, Tuple
import functools

from fuzzywuzzy import fuzz, process  # type:ignore
import flask
import flask_restx  # type:ignore
import pandas as pd  # type:ignore

from foodbank_southlondon.api import rest, utils
from foodbank_southlondon.api.requests import models, namespace, parsers


# CONFIG VARIABLES
_FBSL_CONGESTION_ZONE_POSTCODES_GSHEET_ID = "FBSL_CONGESTION_ZONE_POSTCODES_GSHEET_ID"
_FBSL_FORM_EDIT_URL_TEMPLATE = "FBSL_FORM_EDIT_URL_TEMPLATE"
_FBSL_FUZZY_SEARCH_THRESHOLD = "FBSL_FUZZY_SEARCH_THRESHOLD"
_FBSL_FORM_ID = "FBSL_FORM_ID"
_FBSL_REQUESTS_GSHEET_ID = "FBSL_REQUESTS_GSHEET_ID"

# INTERNALS
_CACHE_NAME = "requests"


@namespace.route("/")
class Requests(flask_restx.Resource):

    @rest.expect(parsers.requests_params)
    @rest.marshal_with(models.page_of_requests)
    @utils.paginate("Packing Date", "Time of Day", "Postcode", "request_id")
    def get(self) -> Tuple[Dict, int, int]:
        """List all Client Requests."""
        params = parsers.requests_params.parse_args(flask.request)
        refresh_cache = params["refresh_cache"]
        packing_dates = set(packing_date.strip() for packing_date in (params["packing_dates"] or ()))
        client_full_names = set(client_full_name.strip() for client_full_name in (params["client_full_names"] or ()))
        postcodes = set(postcode.upper().strip() for postcode in (params["postcodes"] or ()))
        voucher_numbers = set("" if voucher_number.strip() == "?" else voucher_number.strip() for voucher_number in (params["voucher_numbers"] or ()))
        last_request_only = params["last_request_only"]
        df = cache(force_refresh=refresh_cache)
        if packing_dates:
            df = df.loc[df["Packing Date"].isin(packing_dates)]
        name_attribute = "Client Full Name"
        if client_full_names or postcodes or voucher_numbers:
            df = df.loc[df[name_attribute].map(functools.partial(fuzzy_match, choices=client_full_names)) |
                        df["Postcode"].str.upper().str.startswith(tuple(postcodes)) |
                        df["Postcode"].str.upper().str.endswith(tuple(postcodes)) |
                        df["Voucher Number"].isin(voucher_numbers)]
        if last_request_only:
            df = df.assign(rank=df.groupby([name_attribute]).cumcount(ascending=False) + 1).query("rank == 1").drop("rank", axis=1)
        df = df.assign(edit_details_url=df["request_id"].map(_edit_details_url),
                       congestion_zone=df["Postcode"].isin(_congestion_zone_postcodes()["Postcode"].values))
        return (df, params["page"], params["per_page"])


@namespace.route("/<string:request_ids>")
@namespace.doc(params={"request_ids": "A comma separated list of request_id values to retrieve."})
class RequestsByID(flask_restx.Resource):

    @rest.response(404, "Not Found")
    @rest.expect(parsers.pagination_params)
    @rest.marshal_with(models.page_of_requests)
    @utils.paginate("Postcode")
    def get(self, request_ids: str) -> Tuple[Dict, int, int]:
        """Get all Client Requests by provided request_id values."""
        request_id_values = set(request_id.strip() for request_id in request_ids.split(","))
        params = parsers.requests_params.parse_args(flask.request)
        refresh_cache = params["refresh_cache"]
        request_id_attribute = "request_id"
        df = cache(force_refresh=refresh_cache)
        df = df.loc[df[request_id_attribute].isin(request_id_values)]
        missing_request_ids = request_id_values.difference(df[request_id_attribute].unique())
        if missing_request_ids:
            rest.abort(404, f"the following Request ID values {missing_request_ids} were not found.")
        df = df.assign(edit_details_url=df[request_id_attribute].map(_edit_details_url),
                       congestion_zone=df["Postcode"].isin(_congestion_zone_postcodes()["Postcode"].values))
        return (df, params["page"], params["per_page"])


@namespace.route("/distinct/")
class DistinctRequestsValues(flask_restx.Resource):

    @rest.expect(parsers.distinct_requests_params)
    @rest.marshal_with(models.distinct_request_values)
    def get(self) -> Dict[str, List]:
        """Get the distinct values of a Requests attribute."""
        params = parsers.distinct_requests_params.parse_args(flask.request)
        packing_dates = set(packing_date.strip() for packing_date in (params["packing_dates"] or ()))
        attribute = params["attribute"]
        refresh_cache = params["refresh_cache"]
        df = cache(force_refresh=refresh_cache)
        if packing_dates:
            df = df.loc[df["Packing Date"].isin(packing_dates)]
        distinct_values = df[attribute].unique()
        return {"values": sorted(distinct_values)}


def _congestion_zone_postcodes() -> pd.DataFrame:
    return utils.cache("congestion_zone_postcodes", flask.current_app.config[_FBSL_CONGESTION_ZONE_POSTCODES_GSHEET_ID])


def _edit_details_url(request_id: str) -> str:
    return flask.current_app.config[_FBSL_FORM_EDIT_URL_TEMPLATE].format(form_id=flask.current_app.config[_FBSL_FORM_ID], request_id=request_id)


def cache(force_refresh: bool = False) -> pd.DataFrame:
    return utils.cache(_CACHE_NAME, flask.current_app.config[_FBSL_REQUESTS_GSHEET_ID], force_refresh=force_refresh)


def fuzzy_match(text: str, choices: Iterable) -> bool:
    search_threshold = flask.current_app.config[_FBSL_FUZZY_SEARCH_THRESHOLD]
    possibilities = process.extract(text, choices, scorer=fuzz.partial_ratio)
    return any(p[1] >= search_threshold for p in possibilities)
