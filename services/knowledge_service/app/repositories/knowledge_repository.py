from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.course_service.app.models.course import (
    Course,
)
from services.knowledge_service.app.models.knowledge import (
    Asset,
    EvidenceRef,
    Material,
    MaterialChunk,
    MaterialEmbedding,
    MaterialExtraction,
)


class KnowledgeRepository:
    async def get_owned_course(
        self,
        db: AsyncSession,
        *,
        course_id: UUID,
        owner_id: UUID,
    ):
        result = await db.execute(
            select(Course).where(
                Course.id == course_id,
                Course.owner_id == owner_id,
            )
        )

        return result.scalar_one_or_none()

    async def create_material(
        self,
        db: AsyncSession,
        *,
        owner_id: UUID,
        course_id: UUID,
        asset: Asset,
        source_type: str,
        original_filename: str,
    ) -> Material:
        db.add(asset)

        await db.flush()

        material = Material(
            owner_id=owner_id,
            course_id=course_id,
            asset_id=asset.id,
            source_type=source_type,
            original_filename=(
                original_filename
            ),
            status="uploaded",
        )

        db.add(material)

        await db.commit()
        await db.refresh(material)

        return material

    async def get_material(
        self,
        db: AsyncSession,
        *,
        material_id: UUID,
        owner_id: UUID,
    ):
        stmt = (
            select(Material, Asset)
            .join(
                Asset,
                Material.asset_id
                == Asset.id,
            )
            .where(
                Material.id
                == material_id,
                Material.owner_id
                == owner_id,
            )
        )

        result = await db.execute(stmt)

        return result.one_or_none()

    async def list_materials(
        self,
        db: AsyncSession,
        *,
        owner_id: UUID,
        course_id: UUID,
    ) -> list[Material]:
        result = await db.execute(
            select(Material)
            .where(
                Material.owner_id
                == owner_id,
                Material.course_id
                == course_id,
            )
            .order_by(
                Material.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def list_chunks(
        self,
        db: AsyncSession,
        *,
        material_id: UUID,
        owner_id: UUID,
    ) -> list[MaterialChunk]:
        stmt = (
            select(MaterialChunk)
            .join(
                Material,
                MaterialChunk.material_id
                == Material.id,
            )
            .where(
                MaterialChunk.material_id
                == material_id,
                Material.owner_id
                == owner_id,
            )
            .order_by(
                MaterialChunk.chunk_index
            )
        )

        result = await db.execute(stmt)

        return list(
            result.scalars().all()
        )

    async def clear_derivatives(
        self,
        db: AsyncSession,
        *,
        material_id: UUID,
    ) -> None:
        result = await db.execute(
            select(
                MaterialExtraction
            ).where(
                MaterialExtraction.material_id
                == material_id
            )
        )

        extraction = (
            result.scalar_one_or_none()
        )

        if extraction is not None:
            await db.delete(extraction)

            await db.flush()
