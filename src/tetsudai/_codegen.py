import json

def sum_type_internal(type_name: str, constructor_names: list[str]) -> str:
    def nullary_constructor_class(name: str) -> str:
        return f'''@dataclass
class {name}:
    pass
'''
    
    constructor_classes = '\n'.join(map(nullary_constructor_class, constructor_names))
    union_of_constructor_classes = ' | '.join(constructor_names)

    return f'{constructor_classes}\n{type_name} = {union_of_constructor_classes}'

def sum_type(type_name: str, constructor_names: list[str]) -> None:
    print(sum_type_internal(type_name, constructor_names))