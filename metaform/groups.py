class Block:
    tab_space = "    "

    def __init__(self, _id: str="", _type: str="", _group: str="", config_blocks=[], **kwargs):
        self.id = _id
        self.type = _type
        self.config_blocks = [block for block in config_blocks if hasattr(block, "_is_block")]
        if (self.type != "") and (self.id != ""):
            self.type_prefix = self.type + "."  
        elif self.id == "":
            self.type_prefix = self.type
        else:
            self.type_prefix = ""
        self.properties = kwargs
        self.group = _group
        if (self.group != "") and (self.type != "") and (self.id != ""):
            self.group_prefix = self.group + "."
        elif (self.type == "") and (self.id == ""):
            self.group_prefix = self.group
        else:
            self.group_prefix = ""
        self._is_block = True
    
    @property
    def _local(self):
        return f"{self.type_prefix}{self.id}"

    def _write(self, comment: str="", pad: int=0):
        '''
        Creates a string block that translates Block to Terraform
        '''
        lines = [f"#{comment}"] if comment else []
        opening_type = '' if (not self.type) else f'\"{self.type}\" '
        opening_group = '' if (not self.group) else f"{self.group} "
        opening_id = '' if (not self.id) else f"\"{self.id}\""
        lines.append(f"{opening_group}{opening_type}{opening_id}" + " {")
        lines += self._format_props(pad)
        lines.append("}")
        return "\n".join(map(lambda s: pad * " " + s, lines))

    def _format_props(self, pad: int=0):
        '''
        Returns a list of parameter lines
        '''
        max_len = max(len(k) for k in self.properties.keys())
        basic_params = []
        config_params = [block._write(pad=pad+4) for block in self.config_blocks]
        for k, v in self.properties.items():
            if hasattr(v, "_is_block"):
                config_params.append(v._write(pad=pad + 4))
            else:
                basic_params.append(
                    f"{self.tab_space}{k}{' ' * (max_len - len(k))} = {self._parse_annotation(str(v))}"
                )
        return basic_params + config_params

    def __str__(self):
        return "%%" + self.__repr__()
    
    def __repr__(self):
        return f"{self.group_prefix}{self.type_prefix}{self.id}"

    def _parse_annotation(self, s):
        return s.replace("%", "") if (s[:2] == "%%") else f"\"{s}\""

    def __getitem__(self, attribute: str):
        return f"{self.__str__()}.{attribute}"

class UnitMixin:
    
    def __getitem__(self, block_name: str) -> Block:
        return self.blocks[block_name]
    
    def __setitem__(self, block_name: str, block: Block):
        self.blocks[block_name] = block
        return self


class Group(UnitMixin):

    def __init__(self, group: str=""):
        self.group = group
        self.blocks = {}
    
    def __call__(self, _type: str, _id: str,  **kwargs):
        new_block = Block(_id, _type, self.group, **kwargs)
        self.blocks[new_block._local] = new_block
        return new_block


class Modules(UnitMixin):

    def __init__(self):
        self.blocks = {}
    
    def __call__(self, _id: str,  **kwargs):
        new_block = Block(_id, "module", "", **kwargs)
        self.blocks[new_block._local] = new_block
        return new_block
 

Data = Group("data")


Resource = Group("resource")


Module = Modules()


class Config(Block):
    def __init__(self, _id, **kwargs):
        super().__init__("", "", _id, **kwargs)