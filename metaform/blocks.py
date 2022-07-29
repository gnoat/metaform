from __future__ import annotations
from typing import Any, Union


class BlockError(Exception):
    """
    Exception to return due to issues defining blocks
    """


class Caller:
    def __init__(self, base: Any, call: str):
        self.base = base
        self.call = call

    def __str__(self) -> str:
        return f"{str(self.base)}.{str(self.call)}"

    def __repr__(self) -> str:
        return self.__str__()


class Block:
    tab_space = "    "
    _prefix_map = {"variable": "var"}

    def __init__(
        self,
        _id: str = "",
        _type: str = "",
        _group: str = "",
        property_blocks: list[Block] = [],
        **kwargs: Union[str, int, float, Block, bool, list, dict],
    ):
        self.id = _id
        self.type = _type
        self.properties = kwargs
        self.group = _group
        self.property_blocks = [
            block for block in property_blocks if isinstance(block, Block)
        ]
        self.group_prefix, self.type_prefix = self._prefix_parse()
        self.dependencies = []

    def _prefix_parse(self) -> tuple[str, str]:
        group_prefix = ""
        type_prefix = ""
        adjusted_group = self._prefix_map.get(self.group, self.group)
        if self.type and self.id:
            type_prefix = self.type + "."
            if adjusted_group:
                group_prefix = adjusted_group + "."
        elif self.type and not self.id:
            type_prefix = self.type
        elif not self.type and not self.id:
            group_prefix = adjusted_group
        return group_prefix, type_prefix

    def _write(self, comment: str = "", pad: int = 0) -> str:
        """
        Creates a string block that translates Block to Terraform
        """
        lines = [f"#{comment}"] if comment else []
        opening_type = "" if (not self.type) else f' "{self.type}"'
        opening_group = "" if (not self.group) else f"{self.group}"
        opening_id = "" if (not self.id) else f' "{self.id}"'
        opener = f"{opening_group}{opening_type}{opening_id}"
        lines.append(opener + (" " if len(opener) else "") + "{")
        lines += self._format_props(pad)
        lines.append("}")
        return "\n".join(map(lambda s: pad * self.tab_space + s, lines))

    def _format_props(self, pad: int = 0) -> list[str]:
        """
        Returns a list of parameter lines
        """
        max_len = max(len(k) for k in self.properties.keys())
        basic_params = []
        property_params = []
        for k, v in self.properties.items():
            if isinstance(v, Block):
                property_params.append(v._write(pad=pad + 1))
            else:
                base_string = f"{self.tab_space}{k}{' ' * (max_len - len(k))} = "
                if isinstance(v, dict):
                    map_rep = self._map_rep()
                    basic_params.append(base_string + map_rep[0])
                    basic_params += list(
                        map(lambda b: len(base_string) * " " + b, map_rep[1:])
                    )
                elif isinstance(v, tuple or list):
                    basic_params.append(
                        base_string
                        + "tolist(["
                        + ",".join(self._parse(_v) for _v in v)
                        + "])"
                    )
                else:
                    basic_params.append(base_string + self._parse(v))
        return basic_params + property_params

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.group_prefix}{self.type_prefix}{self.id}"

    def _parse(self, s: str) -> str:
        if isinstance(s, Caller):
            self.dependencies.append(s.base)
            return str(s)
        elif isinstance(s, int or float):
            return str(s)
        elif isinstance(s, bool):
            return str(s).lower()
        else:
            return f'"{s}"'

    def __getitem__(self, attribute: str) -> str:
        return Caller(self.__str__(), attribute)

    def _map_rep(self, d: dict, pad=0, tomap=True, max_elements=4) -> list[str]:
        if tomap:
            base = Block("", "", "", **d)._format_props(pad=pad + 6)
            base[0] = "tomap(" + base[0]
            base[-1] = base[-1] + ")"
        else:
            base = Block("", "", "", **d)._format_props(pad=pad)
        if len(base) < max_elements:
            base = [base[0] + ",".join(base[1:-1]) + base[-1]]
        return base

    def _validate(self):
        # TODO: Validate new blocks exist and have all required properties
        return True
