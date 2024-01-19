from apps.wishmaster.tables import Category, Tag, Wish, WishList, WishTag
from tests.apps.wishmaster.factories import CategoryFactory, TagFactory, WishFactory, WishListFactory, WishTagFactory
from tests.bases import BaseModelFactory


class TestWish:
    async def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=WishFactory, model=Wish)

    async def test__repr__(self) -> None:
        obj: Wish = WishFactory.create()
        result = obj.__repr__()
        expected_result = (
            f'{obj.__class__.__name__}(title="{obj.title}", description="{obj.description}", status="{obj.status}")'
        )
        assert result == expected_result


class TestWishList:
    async def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=WishListFactory, model=WishList)

    async def test__repr__(self) -> None:
        obj: WishList = WishListFactory.create()
        result = obj.__repr__()
        expected_result = f'{obj.__class__.__name__}(title="{obj.title}", owner_id={obj.owner_id!r})'
        assert result == expected_result

    async def test__str__(self) -> None:
        obj: WishList = WishListFactory.create()
        result = obj.__str__()
        expected_result = f'{obj.__class__.__name__}(title="{obj.title}")'
        assert result == expected_result


class TestCategory:
    async def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=CategoryFactory, model=Category)

    async def test__repr__(self) -> None:
        obj: Category = CategoryFactory.create()
        result = obj.__repr__()
        expected_result = f'{obj.__class__.__name__}(title="{obj.title}", owner_id={obj.owner_id!r})'
        assert result == expected_result


class TestTag:
    async def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=TagFactory, model=Tag)

    async def test__repr__(self) -> None:
        obj: Tag = TagFactory.create()
        result = obj.__repr__()
        expected_result = f'{obj.__class__.__name__}(title="{obj.title}")'
        assert result == expected_result


class TestWishTag:
    async def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=WishTagFactory, model=WishTag)

    async def test__repr__(self) -> None:
        obj: WishTag = WishTagFactory.create()
        result = obj.__repr__()
        expected_result = f'{obj.__class__.__name__}(wish_id="{obj.wish_id}", tag_id="{obj.tag_id}")'
        assert result == expected_result
