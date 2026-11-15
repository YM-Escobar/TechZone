#HELPERS: CAMPOS QUE SE USARAN DURANTE LAS VALIDACIONES
from typing import Any


#COMPRUEBA QUE EL VALOR SEA ENTERO POSITIVO
def is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0

#COMPRUEBA QUE EL VALOR SEA ENTERO MAYOR O IGUAL A CERO
def is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0

#COMPRUEBA QUE EL VALOR SEA UN TEXTO NO VACIO
def is_non_empty_string(value: Any) -> bool: 
    return isinstance(value, str) and bool(value.strip())
    
#COMPRUEBA QUE UN VALOR SEA UNA LISTA CON ELEMENTOS DE TEXTO NO VACIOS
def is_string_list(value:Any) -> bool:
    return(
        isinstance(value, list)
        and all(is_non_empty_string(item) for item in value)
    )

#COMPRUEBA QUE UN VALOR SEA UN DICCIONARIO  
def is_dict(value: Any) -> bool:
    return isinstance(value, dict)

#COMPRUEBA QUE UN VALOR SEA UNA LISTA CON ELEMENTOS QUE SEAN DICCIONARIO
def is_list_of_dicts(value: Any) -> bool:
    return(
        isinstance(value, list)
        and all(isinstance(item, dict) for item in value)
    )
    
#COMPRUEBA QUE UN DICCIONARIO CONTENGA TODAS LAS CLAVES OBLIGATORIAS(clave valor del dict)
def has_required_keys(
    data: Any,
    required_keys: set[str]
) -> bool:
    return(
        isinstance(data, dict)
        and all(key in data and data[key] is not None for key in required_keys)
    )
    
