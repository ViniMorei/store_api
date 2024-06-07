from typing import List
from uuid import UUID
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.core.exceptions import NotFoundException, InsertionException
from datetime import datetime


class ProductUsecase:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient = db_client.get()
        self.database: AsyncIOMotorDatabase = self.client.get_database()
        self.collection = self.database.get_collection("products")

    async def create(self, body: ProductIn) -> ProductOut:
        product_model = ProductModel(**body.model_dump())
        await self.collection.insert_one(product_model.model_dump())

        return ProductOut(**product_model.model_dump())

    async def get(self, id: UUID) -> ProductOut:
        result = await self.collection.find_one({"id": id})

        if not result:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        return ProductOut(**result)

    async def query(self, min_price: Optional[Decimal] = None, max_price: Optional[Decimal] = None) -> List[ProductOut]:
        query = {}
        if min_price:
            query["price"] = {"$gte": min_price}
        if max_price:
            query["price"]["$lte"] = max_price

        products = await self.db["products"].find(query).to_list(length=None)
        return [ProductOut(**product) for product in products]

    async def update(self, id: UUID4, body: ProductUpdate) -> ProductUpdateOut:
        product = await self.get(id)  # Assume que este método lança NotFoundException se não encontrar

        if not product:
            raise NotFoundException(f"Product not found with id: {id}")

        # Atualiza os campos modificados e o campo updated_at
        for key, value in body.dict(exclude_unset=True).items():
            setattr(product, key, value)
        product.updated_at = datetime.utcnow()

        # Salva o produto atualizado
        await self.save(product)  # Supondo que haja um método save

        return ProductUpdateOut(**product.dict())

    async def delete(self, id: UUID) -> bool:
        product = await self.collection.find_one({"id": id})
        if not product:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        result = await self.collection.delete_one({"id": id})

        return True if result.deleted_count > 0 else False


product_usecase = ProductUsecase()
