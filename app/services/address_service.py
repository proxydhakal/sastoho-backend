from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate

class AddressService:
    async def get_user_addresses(self, db: AsyncSession, user_id: int) -> List[Address]:
        """Get all addresses for a user."""
        stmt = select(Address).filter(Address.user_id == user_id).order_by(Address.is_default.desc(), Address.id.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_address(self, db: AsyncSession, address_id: int, user_id: int) -> Optional[Address]:
        """Get a specific address by ID, ensuring it belongs to the user."""
        stmt = select(Address).filter(Address.id == address_id, Address.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_default_address(self, db: AsyncSession, user_id: int) -> Optional[Address]:
        """Get the default address for a user."""
        stmt = select(Address).filter(Address.user_id == user_id, Address.is_default == True)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def create_address(self, db: AsyncSession, user_id: int, address_in: AddressCreate) -> Address:
        """Create a new address. If is_default is True, unset other default addresses."""
        # If this is set as default, unset other defaults
        if address_in.is_default:
            await self._unset_other_defaults(db, user_id)

        address = Address(
            user_id=user_id,
            **address_in.model_dump()
        )
        db.add(address)
        await db.commit()
        await db.refresh(address)
        return address

    async def update_address(self, db: AsyncSession, address_id: int, user_id: int, address_in: AddressUpdate) -> Optional[Address]:
        """Update an address. If is_default is set to True, unset other defaults."""
        address = await self.get_address(db, address_id, user_id)
        if not address:
            return None

        # If setting as default, unset other defaults
        if address_in.is_default is True:
            await self._unset_other_defaults(db, user_id, exclude_id=address_id)

        # Update fields
        update_data = address_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(address, field, value)

        db.add(address)
        await db.commit()
        await db.refresh(address)
        return address

    async def delete_address(self, db: AsyncSession, address_id: int, user_id: int) -> bool:
        """Delete an address."""
        address = await self.get_address(db, address_id, user_id)
        if not address:
            return False

        await db.delete(address)
        await db.commit()
        return True

    async def set_default_address(self, db: AsyncSession, address_id: int, user_id: int) -> Optional[Address]:
        """Set an address as default, unsetting others."""
        address = await self.get_address(db, address_id, user_id)
        if not address:
            return None

        await self._unset_other_defaults(db, user_id, exclude_id=address_id)
        address.is_default = True
        db.add(address)
        await db.commit()
        await db.refresh(address)
        return address

    async def _unset_other_defaults(self, db: AsyncSession, user_id: int, exclude_id: Optional[int] = None) -> None:
        """Unset default flag for all addresses except the excluded one."""
        stmt = select(Address).filter(Address.user_id == user_id, Address.is_default == True)
        if exclude_id:
            stmt = stmt.filter(Address.id != exclude_id)
        
        result = await db.execute(stmt)
        addresses = result.scalars().all()
        for addr in addresses:
            addr.is_default = False
            db.add(addr)
        await db.commit()

address_service = AddressService()
