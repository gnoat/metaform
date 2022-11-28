from blocks import (
    Block,
    BlockError,
    _VARIABLE,
    _DATA,
    _MODULE,
    _RESOURCE,
    _OUTPUT,
    _PROPERTY,
    _PROVIDER,
)
from typing import Union, Optional
import itertools
import functools
import os


class DependencyError(Exception):
    """
    Exception to return due to issues resolving dependencies
    """


def resolve_dependencies(
    dependency_map: dict[str, set[str]], base_layer: set[str] = set()
) -> list[set[str]]:
    layers = []
    total_blocks = set(dependency_map.keys())
    while base_layer != total_blocks:
        next_layer = set(
            block
            for block in dependency_map
            if dependency_map[block].issubset(base_layer)
        )
        current_layer = next_layer - base_layer
        layers.append(current_layer)
        base_layer = next_layer
        if not current_layer:
            raise DependencyError(
                "Unable to resolve dependencies, ensure they are consistent and non-circular."
            )
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


class Group:
    _ignore_duplicates = False

    def __init__(self, group: str, registry: Registry):
        self.group = group
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

    def __call__(
        self,
        *ids,
        **kwargs: Optional[Union[str, int, float, Block, bool, list, dict]],
    ) -> Block:
        new_block = Block(self.group, *ids, **kwargs)
        return self._update_tracking_and_return(new_block)


class Providers:
    _ignore_duplicates = False

    def __init__(
        self,
        provider: str,
        source: Optional[str] = None,
        version: Optional[str] = None,
        **kwargs,
    ):
        self.provider = provider
        self.source = source
        self.version = version
        self.properties = kwargs

    def __init__(self, registry: Registry):
        self.registry = registry
        self.blocks = {}
        self.provider_options = {}

    def __getitem__(self, provider_block_id: str) -> Block:
        return self.provider_blocks[provider_block_id]

    def _update_tracking(
        self,
        provider: str,
        source: Optional[str] = None,
        version: Optional[str] = None,
        **kwargs,
    ):
        provider_block = Block("provider", provider, **kwargs)
        required_provider_params = {}
        if source:
            required_provider_params["source"] = source
        elif version:
            required_provider_params["version"] = version
        provider_options = Block(
            "map", provider, _tomap=False, **required_provider_params
        )
        if (str(provider_block) not in self.registry) or self._ignore_duplicates:
            self.registry[str(provider_block)] = provider_block
        else:
            raise BlockError(
                f"Provider {provider} is already registered in the block registry."
            )
        self.provider_options[provider] = provider_options

    def add(
        self,
        provider: str,
        source: Optional[str] = None,
        version: Optional[str] = None,
        **kwargs,
    ):
        self._update_tracking(provider, source, version, **kwargs)

    def build_provider(self):
        return Block(
            "property",
            "terraform",
            _tomap=False,
            required_providers=Block("map", **self.required_provider_params),
        )


class MetaFormer:
    _COMPONENT_ORDER = [_PROPERTY, _VARIABLE, _DATA, _RESOURCE, _MODULE, _OUTPUT]

    def __init__(
        self,
        name: str = "main",
        isolate_module: bool = False,
        split_out: bool = False,
        registry: Optional[Registry] = None,
    ):
        if registry is not None:
            self.registry = registry
        else:
            self.registry = Registry()
        self.name = name
        self.isolate_module = isolate_module

        # create major componenets
        self.data = Group("data", self.registry)
        self.resource = Group("resource", self.registry)
        self.module = Group("module", self.registry)
        self.variable = Group("variable", self.registry)
        self.property = Group("property", self.registry)
        self.output = Group("output", self.registry)
        self.provider = Providers(self.registry)

        # shortened aliases
        self.dat = self.data
        self.res = self.resource
        self.mod = self.module
        self.var = self.variable
        self.prop = self.property
        self.prov = self.provider

    def _clear_registry(self):
        self.registry = Registry()
        return self

    def _collect_dependencies(self) -> dict[str, set[str]]:
        return {
            block_id: {str(dep_block) for dep_block in block.dependencies}
            for block_id, block in self.registry.items()
            if block._group != _PROPERTY
        }

    def _resolve_dependencies(self) -> list[set[str]]:
        return resolve_dependencies(self._collect_dependencies())

    def collect(self) -> list[Block]:
        dependencies = self._resolve_dependencies()
        return functools.reduce(
            lambda m, n: self._sort(set(m)) + self._sort(set(n)), dependencies, []
        )

    def _sort(self, deps: set[Block]) -> list[Block]:
        """
        Sort the dependencies putting in the following order:
            VARIABLES -> DATA -> RESOURCES -> MODULES -> OUTPUTS
        """
        deps = {self.registry[str(block_id)] for block_id in deps}
        ordered = [
            list(filter(lambda b: b._group == comp, deps))
            for comp in self._COMPONENT_ORDER
        ] + [list(filter(lambda b: b._group not in self._COMPONENT_ORDER, deps))]
        return list(itertools.chain(*ordered))

    def _write(self):
        """
        Return the contents of the MetaForm object as a string
        """
        return "\n\n".join(block._write() for block in self.collect())

    def build(self):
        """
        Build out the new terraform scripts from the metaform commands
        """
        if self.isolate_module:
            main_path = os.path.join(os.path.realpath("__main__"), self.name)
            os.mkdir(main_path)
            with open(os.path.join(main_path, "main.tf"), "w") as f:
                f.write(self._write())
        else:
            with open(f"{self.name}.tf", "w") as f:
                f.write(self._write())
