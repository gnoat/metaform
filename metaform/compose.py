from blocks import Block, BlockError
from typing import Union, Optional
import functools


class DependencyError(Exception):
    """
    Exception to return due to issues resolving dependencies
    """


def resolve_dependencies(dependency_map: dict[str, set[str]], base_layer: set[str] = set()) -> list[set[str]]:
    layers = []
    total_blocks = set(dependency_map.keys())
    while base_layer != total_blocks:
        next_layer = set(block for block in dependency_map if dependency_map[block].issubset(base_layer))
        current_layer = next_layer - base_layer
        layers.append(current_layer)
        base_layer = next_layer
        if not current_layer:
            raise DependencyError("Unable to resolve dependencies, ensure they are consistent and non-circular.")
    return layers


class Registry(dict):
    def __init__(self):
        super(Registry, self).__init__()

    def __setitem__(self, block_id: str, block: Block):
        if isinstance(block, Block):
            super(Registry, self).__setitem__(block_id, block)
        return self

    def __getitem__(self, block_id: str) -> Block:
        block = super(Registry, self).get(block_id, None)
        if block:
            return block
        else:
            raise BlockError(f"Block {block_id} is not registered in the registry.")

    def __str__(self):
        return str(list(super(Registry, self).keys()))

    def __repr__(self):
        return self.__str__()


class UnitMixin:
    _ignore_duplicates = False

    def __init__(self, registry: Registry):
        self.registry = registry
        self.blocks = {}

    def __getitem__(self, block_id: str) -> Block:
        return self.blocks[block_id]

    def _update_tracking_and_return(self, new_block: Block):
        self.blocks[str(new_block)] = new_block
        if (str(new_block) not in self.registry) or self._ignore_duplicates:
            self.registry[str(new_block)] = new_block
        else:
            raise BlockError(
                f"Block {new_block} is already registered in the block registry."
            )
        return new_block


class Group(UnitMixin):
    def __init__(self, registry: Registry, group: str):
        super().__init__(registry)
        self.group = group

    def __call__(
        self,
        _type: str,
        _id: str,
        **kwargs: Optional[Union[str, int, float, Block, bool, list, dict]],
    ) -> Block:
        new_block = Block(_id, _type, self.group, **kwargs)
        return self._update_tracking_and_return(new_block)


class Micros(UnitMixin):
    def __init__(
        self, registry: Registry, _without_quotes: str = "", _with_quotes: str = ""
    ):
        super().__init__(registry)
        self.with_quotes = _with_quotes
        self.without_quotes = _without_quotes

    def __call__(
        self,
        _id: str,
        **kwargs: Optional[Union[str, int, float, Block, bool]],
    ) -> Block:
        new_block = Block(
            _id,
            self.with_quotes,
            self.without_quotes,
            **kwargs,
        )
        return self._update_tracking_and_return(new_block)


class Properties(UnitMixin):
    def __init__(self, registry: Registry):
        super().__init__(registry)

    def __call__(
        self, _id: str, **kwargs: Optional[Union[str, int, float, Block, bool, list, dict]]
    ):
        new_prop = Block("", "", _id, **kwargs)
        return self._update_tracking_and_return(new_prop)


class MetaFormer:
    def __init__(self, registry: Optional[Registry] = None):
        if registry is not None:
            self.registry = registry
        else:
            self.registry = Registry()
        self._create_groups()

        # shortened aliases
        self.dat = self.data
        self.res = self.resource
        self.mod = self.module
        self.var = self.variable
        self.pro = self.property

    def _create_groups(self):
        self.data = Group(self.registry, "data")
        self.resource = Group(self.registry, "resource")
        self.module = Micros(self.registry, "module", "")
        self.variable = Micros(self.registry, "variable", "")
        self.property = Properties(self.registry)
        return self

    def _clear_registry(self):
        self.registry = Registry()
        return self
    
    def _collect_dependencies(self) -> dict[str, list[str]]:
        return {block_id: [str(dep_block) for dep_block in block.dependencies] for block_id, block in self.registry}
    
    def _resolve_dependencies(self) -> list[list[str]]:
        return resolve_dependencies(self._collect_dependencies())
    
    def _order_dependencies(self) -> list[Block]:
        dependencies = self._resolve_dependencies()

