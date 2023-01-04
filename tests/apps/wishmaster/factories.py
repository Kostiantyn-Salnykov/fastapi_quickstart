from apps.wishmaster.models import Wish
from apps.wishmaster.schemas import WishCreateSchema
from tests.bases import AsyncPersistenceHandler, BaseFactory


class WishFactory(BaseFactory):
    """WishFactory based on Faker and Pydantic."""

    __model__ = WishCreateSchema
    __async_persistence__ = AsyncPersistenceHandler(model=Wish)
