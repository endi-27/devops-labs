from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.repository import ProductRepository
from src.schemas import ProductCreate, ProductResponse, ProductUpdate, StockChangeRequest
from src.service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


def get_product_service(session: AsyncSession = Depends(get_db_session)) -> ProductService:
    repository = ProductRepository(session)
    return ProductService(repository)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    product = await service.create_product(payload)
    return ProductResponse.model_validate(product)


@router.get("", response_model=list[ProductResponse])
async def get_all_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    only_available: bool = Query(False),
    service: ProductService = Depends(get_product_service),
) -> list[ProductResponse]:
    products = await service.get_all_products(skip=skip, limit=limit, only_available=only_available)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    product = await service.get_product_by_id(product_id)
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    product = await service.update_product(product_id, payload)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> None:
    await service.delete_product(product_id)


@router.post("/{product_id}/reserve", response_model=ProductResponse)
async def reserve_stock(
    product_id: int,
    payload: StockChangeRequest,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    product = await service.reserve_stock(product_id, payload.quantity)
    return ProductResponse.model_validate(product)


@router.post("/{product_id}/release", response_model=ProductResponse)
async def release_stock(
    product_id: int,
    payload: StockChangeRequest,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    product = await service.release_stock(product_id, payload.quantity)
    return ProductResponse.model_validate(product)
