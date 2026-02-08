from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.address import Address, AddressCreate, AddressUpdate
from app.services.address_service import address_service

router = APIRouter()

@router.get("/", response_model=List[Address])
async def get_addresses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all addresses for the current user.
    """
    addresses = await address_service.get_user_addresses(db, current_user.id)
    return addresses

@router.get("/default", response_model=Address)
async def get_default_address(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get the default address for the current user.
    """
    address = await address_service.get_default_address(db, current_user.id)
    if not address:
        raise HTTPException(status_code=404, detail="No default address found")
    return address

@router.post("/", response_model=Address, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_in: AddressCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new address for the current user.
    """
    address = await address_service.create_address(db, current_user.id, address_in)
    return address

@router.get("/{address_id}", response_model=Address)
async def get_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific address by ID.
    """
    address = await address_service.get_address(db, address_id, current_user.id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address

@router.patch("/{address_id}", response_model=Address)
async def update_address(
    address_id: int,
    address_in: AddressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update an address.
    """
    address = await address_service.update_address(db, address_id, current_user.id, address_in)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address

@router.delete("/{address_id}")
async def delete_address(
    address_id: int,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete an address.
    """
    success = await address_service.delete_address(db, address_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Address not found")
    response.status_code = status.HTTP_204_NO_CONTENT

@router.post("/{address_id}/set-default", response_model=Address)
async def set_default_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Set an address as the default address.
    """
    address = await address_service.set_default_address(db, address_id, current_user.id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address
