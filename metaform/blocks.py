from __future__ import annotations
from typing import Any, Union, Optional, Literal


_VARIABLE = "variable"
_DATA = "data"
_MODULE = "module"
_RESOURCE = "resource"
_PROPERTY = "property"
_MAP = "map"
_OUTPUT = "output"
_GROUP_VALENCE = {
    _VARIABLE: 1,
    _DATA: 2,
    _MODULE: 1,
    _RESOURCE: 2,
    _PROPERTY: 1,
    _MAP: 0,
    _OUTPUT: 1,
}
_GROUPS = list(_GROUP_VALENCE.keys())


class BlockError(Exception):
    """
    Exception to return due to issues defining blocks
    """


class Caller:
    def __init__(self, base: Any, call: str):
        self.base = base
        self.call = call

    def __str__(self) -> str:
        return f"{str(self.base)}.{self.call}"

    def __repr__(self) -> str:
        return self.__str__()


class Block:
    _tab_space = "    "
    _group_abbrv = {_VARIABLE: "var", _MAP: ""}

    def __init__(
        self,
        _group: str,
        *args: str,
        **kwargs: Union[str, int, float, Block, bool, list, dict],
    ):
        self._group = _group
        self.group, self.group_abbrv, self.ids = self._group_id_reprs(_group, args)
        self.properties = kwargs
        self._max_elements = 4
        self._tomap = True
        self.dependencies = set()
        self._format_props()  # needs to run on start to capture all dependencies

    def _group_id_reprs(self, s: str, ids: tuple[str]) -> tuple[str, str, tuple[str]]:
        if (s == _MAP) and not ids:
            return "", "", ids
        elif s == _PROPERTY:
            return ids[0], ids[0], ids[1:]
        else:
            return s, self._group_abbrv.get(s, s), ids

    def _write_ids(self) -> str:
        return " ".join([self.group] + [f'"{id}"' for id in self.ids]).strip() + " "

    def _write(self, comment: str = "", pad: int = 0) -> str:
        """
        Creates a string block that translates Block to Terraform
        """
        lines = [f"#{comment}"] if comment else []
        lines.append(self._write_ids() + "{")
        lines += self._format_props(pad)
        lines.append("}")
        return "\n".join(map(lambda s: pad * self._tab_space + s, lines))

    def _format_props(self, pad: int = 0) -> list[str]:
        """
        Returns a list of parameter lines
        """
        max_len = max(len(k) for k in self.properties.keys())
        basic_params = []
        property_params = []
        for k, v in self.properties.items():
            if isinstance(v, Block):
                self._add_dependencies(v)
            elif isinstance(v, Caller):
                self._add_dependencies(v.base)
            if isinstance(v, Block):
                property_params.append(v._write(pad=pad + 1))
            else:
                base_string = f"{self._tab_space}{k}{' ' * (max_len - len(k))} = "
                if isinstance(v, dict):
                    map_rep = self._map_rep(v)
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
        return ".".join([self.group_abbrv] + list(self.ids)).strip(".")

    def _parse(self, s: Union[Caller, int, float, str, bool]) -> str:
        if isinstance(s, Caller):
            return str(s)
        elif isinstance(s, int or float):
            return str(s)
        elif isinstance(s, bool):
            return str(s).lower()
        else:
            return f'"{s}"'

    def __getitem__(self, attribute: str) -> str:
        return Caller(self, attribute)

    def _map_rep(self, d: dict, pad=0) -> list[str]:
        dummy_block = Block(_MAP, **d)
        if self._tomap:
            base = dummy_block._format_props(pad=pad + 6)
            base[0] = "tomap(" + base[0]
            base[-1] = base[-1] + ")"
        else:
            base = dummy_block._format_props(pad=pad)
        if len(base) < self._max_elements:
            base = [base[0] + ",".join(base[1:-1]) + base[-1]]
        return base

    def _validate(self):
        # TODO: Validate new blocks exist and have all required properties
        group_valence = _GROUP_VALENCE.get(self._group, len(self.ids))
        if group_valence != len(self.ids):
            raise BlockError(
                f'Group "{self._group}" requires valence {group_valence}, but got {len(self.ids)}.'
            )

    def _add_dependencies(self, v: Block):
        for sub in [v] + list(v.dependencies):
            if sub._group in [_VARIABLE, _DATA, _MODULE, _RESOURCE, _OUTPUT]:
                self.dependencies.add(v)
