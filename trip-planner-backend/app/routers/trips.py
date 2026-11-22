from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.core.database import get_user_client
from app.core.deps import verify_access_token
from app.core.errors import APIError
from app.schemas.trips import (
    ItineraryItemCreate,
    ItineraryItemOut,
    ItineraryItemUpdate,
    TripCreate,
    TripOut,
    TripUpdate,
)

router = APIRouter(prefix="/api/trips", tags=["trips"])


def _clean(params: dict) -> dict:
    return {key: value for key, value in params.items() if value is not None}


def _get_owned_trip(trip_id: UUID, claims: dict) -> dict:
    supabase = get_user_client(claims["token"])
    user_id = claims["sub"]
    response = (
        supabase.table("trips")
        .select("*")
        .eq("id", str(trip_id))
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not response.data:
        raise APIError("Trip not found", 404)
    return response.data


@router.get("", response_model=list[TripOut])
def list_trips(claims: dict = Depends(verify_access_token)) -> list[TripOut]:
    supabase = get_user_client(claims["token"])
    user_id = claims["sub"]
    response = (
        supabase.table("trips")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [TripOut(**row) for row in (response.data or [])]


@router.post("", response_model=TripOut, status_code=201)
def create_trip(
    payload: TripCreate, claims: dict = Depends(verify_access_token)
) -> TripOut:
    supabase = get_user_client(claims["token"])
    user_id = claims["sub"]
    row = payload.model_dump(mode="json")
    row["user_id"] = user_id
    response = supabase.table("trips").insert(row).execute()
    if not response.data:
        raise APIError("Could not create the trip", 500)
    return TripOut(**response.data[0])


@router.get("/{trip_id}", response_model=TripOut)
def get_trip(trip_id: UUID, claims: dict = Depends(verify_access_token)) -> TripOut:
    return TripOut(**_get_owned_trip(trip_id, claims))


@router.patch("/{trip_id}", response_model=TripOut)
def update_trip(
    trip_id: UUID,
    payload: TripUpdate,
    claims: dict = Depends(verify_access_token),
) -> TripOut:
    supabase = get_user_client(claims["token"])
    user_id = claims["sub"]
    updates = _clean(payload.model_dump(mode="json", exclude_unset=True))
    if not updates:
        raise APIError("No fields to update", 400)
    _get_owned_trip(trip_id, claims)  # 404 when missing or not owned
    response = (
        supabase.table("trips")
        .update(updates)
        .eq("id", str(trip_id))
        .eq("user_id", user_id)
        .execute()
    )
    if not response.data:
        raise APIError("Trip not found", 404)
    return TripOut(**response.data[0])


@router.delete("/{trip_id}", status_code=204)
def delete_trip(
    trip_id: UUID, claims: dict = Depends(verify_access_token)
) -> Response:
    supabase = get_user_client(claims["token"])
    user_id = claims["sub"]
    _get_owned_trip(trip_id, claims)  # 404 when missing or not owned
    supabase.table("trips").delete().eq("id", str(trip_id)).eq("user_id", user_id).execute()
    return Response(status_code=204)


@router.get("/{trip_id}/itinerary", response_model=list[ItineraryItemOut])
def list_itinerary(
    trip_id: UUID, claims: dict = Depends(verify_access_token)
) -> list[ItineraryItemOut]:
    _get_owned_trip(trip_id, claims)  # 404 when missing or not owned
    supabase = get_user_client(claims["token"])
    user_id = claims["sub"]
    response = (
        supabase.table("trip_itinerary_items")
        .select("*")
        .eq("trip_id", str(trip_id))
        .order("day_number", desc=False)
        .order("start_time", desc=False)
        .execute()
    )
    return [ItineraryItemOut(**row) for row in (response.data or [])]


@router.post("/{trip_id}/itinerary", response_model=ItineraryItemOut, status_code=201)
def create_itinerary_item(
    trip_id: UUID,
    payload: ItineraryItemCreate,
    claims: dict = Depends(verify_access_token),
) -> ItineraryItemOut:
    _get_owned_trip(trip_id, claims)  # 404 when missing or not owned
    supabase = get_user_client(claims["token"])
    user_id = claims["sub"]
    row = payload.model_dump(mode="json")
    row["trip_id"] = str(trip_id)
    response = supabase.table("trip_itinerary_items").insert(row).execute()
    if not response.data:
        raise APIError("Could not create the itinerary item", 500)
    return ItineraryItemOut(**response.data[0])


@router.patch("/{trip_id}/itinerary/{item_id}", response_model=ItineraryItemOut)
def update_itinerary_item(
    trip_id: UUID,
    item_id: UUID,
    payload: ItineraryItemUpdate,
    claims: dict = Depends(verify_access_token),
) -> ItineraryItemOut:
    _get_owned_trip(trip_id, claims)  # 404 when missing or not owned
    supabase = get_user_client(claims["token"])
    user_id = claims["sub"]
    updates = _clean(payload.model_dump(mode="json", exclude_unset=True))
    if not updates:
        raise APIError("No fields to update", 400)
    response = (
        supabase.table("trip_itinerary_items")
        .update(updates)
        .eq("id", str(item_id))
        .eq("trip_id", str(trip_id))
        .execute()
    )
    if not response.data:
        raise APIError("Itinerary item not found", 404)
    return ItineraryItemOut(**response.data[0])


@router.delete("/{trip_id}/itinerary/{item_id}", status_code=204)
def delete_itinerary_item(
    trip_id: UUID,
    item_id: UUID,
    claims: dict = Depends(verify_access_token),
) -> Response:
    _get_owned_trip(trip_id, claims)  # 404 when missing or not owned
    supabase = get_user_client(claims["token"])
    user_id = claims["sub"]
    supabase.table("trip_itinerary_items").delete().eq("id", str(item_id)).eq(
        "trip_id", str(trip_id)
    ).execute()
    return Response(status_code=204)
