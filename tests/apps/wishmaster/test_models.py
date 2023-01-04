from apps.wishmaster.models import Wish
from apps.wishmaster.schemas import WishCreateSchema
from tests.apps.wishmaster.factories import WishFactory


class TestWish:
    async def test_factory(self) -> None:
        to_do_schema: WishCreateSchema = WishFactory.build()
        wish: Wish = await WishFactory.create_async()
        wishes: list[Wish] = await WishFactory.create_batch_async(size=2)

        assert isinstance(wish, Wish)
        assert isinstance(to_do_schema, WishCreateSchema)
        for i in wishes:
            assert isinstance(i, Wish)

    async def test__repr__(self) -> None:
        obj: Wish = await WishFactory.create_async()
        result = obj.__repr__()
        expected_result = (
            f'{obj.__class__.__name__}(title="{obj.title}", description="{obj.description}", status="{obj.status}")'
        )
        assert expected_result == result
