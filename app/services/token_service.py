from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.blacklisted_token import BlacklistedToken
from app.core import security

class TokenService:
    async def is_token_blacklisted(self, db: AsyncSession, token: str) -> bool:
        """Check if a token is blacklisted."""
        stmt = select(BlacklistedToken).filter(BlacklistedToken.token == token)
        result = await db.execute(stmt)
        blacklisted = result.scalars().first()
        if blacklisted:
            # Check if token has expired (cleanup expired tokens)
            if blacklisted.expires_at < datetime.now(timezone.utc):
                await db.delete(blacklisted)
                await db.commit()
                return False
            return True
        return False

    async def blacklist_token(
        self, 
        db: AsyncSession, 
        token: str, 
        token_type: str,
        expires_at: datetime
    ) -> BlacklistedToken:
        """Add a token to the blacklist."""
        # Check if already blacklisted
        existing = await self.is_token_blacklisted(db, token)
        if existing:
            # Already blacklisted, return existing
            stmt = select(BlacklistedToken).filter(BlacklistedToken.token == token)
            result = await db.execute(stmt)
            return result.scalars().first()
        
        blacklisted_token = BlacklistedToken(
            token=token,
            token_type=token_type,
            expires_at=expires_at
        )
        db.add(blacklisted_token)
        await db.commit()
        await db.refresh(blacklisted_token)
        return blacklisted_token

    async def blacklist_tokens_from_request(
        self,
        db: AsyncSession,
        access_token: str | None,
        refresh_token: str | None
    ) -> None:
        """Blacklist both access and refresh tokens from a request."""
        if access_token:
            payload = security.decode_token(access_token)
            if payload:
                exp_timestamp = payload.get("exp")
                if exp_timestamp:
                    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                    await self.blacklist_token(db, access_token, security.TOKEN_TYPE_ACCESS, expires_at)
        
        if refresh_token:
            payload = security.decode_token(refresh_token)
            if payload:
                exp_timestamp = payload.get("exp")
                if exp_timestamp:
                    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                    await self.blacklist_token(db, refresh_token, security.TOKEN_TYPE_REFRESH, expires_at)

    async def cleanup_expired_tokens(self, db: AsyncSession) -> int:
        """Remove expired blacklisted tokens from database."""
        stmt = delete(BlacklistedToken).filter(
            BlacklistedToken.expires_at < datetime.now(timezone.utc)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

token_service = TokenService()
