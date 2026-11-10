
# MagicMock permite simular el repositorio sin acceder a la base de datos.
from unittest.mock import MagicMock, patch

# pytest permite ejecutar y organizar las pruebas.
import pytest

# Modelo y categorías de productos.
from app.Models.product import Product, ProductCategory

# Esquemas utilizados para crear y actualizar productos.
from app.Schema.product_schema import ProductCreate, ProductUpdate

# Servicio que estamos probando.
from app.Services.products import ProductService


# Especificaciones válidas de una GPU para las pruebas.
VALID_GPU_SPECS = {
    "interface": {
        "generation": "4.0",
        "physical_size": "x16",
        "electrical_lanes": 16,
    },
    "vram_gb": 12,
    "board_power_w": 250,
    "recommended_psu_w": 650,
    "power_connectors_required": [
        {
            "type": "PCIe 8-pin",
            "quantity": 2,
        }
    ],
}


@pytest.fixture
def service():
    # Simula el repositorio para evitar operaciones reales de base de datos.
    with patch("app.Services.products.ProductRepository") as repository_mock:

        # Crea una instancia del servicio.
        product_service = ProductService(db=MagicMock())

        # Devuelve el servicio y el repositorio simulado.
        yield product_service, repository_mock.return_value


def test_create_eligible_product(service):
    # Obtiene el servicio y el repositorio simulado.
    product_service, repository = service

    # Prepara los datos de un producto con especificaciones válidas.
    data = ProductCreate(
        name="GPU de prueba",
        brand="Marca",
        category=ProductCategory.GPU,
        price=500,
        stock=5,
        specs=VALID_GPU_SPECS,
    )

    # Ejecuta la creación del producto.
    product_service.create(data)

    # Comprueba que el repositorio recibió un producto elegible.
    saved_product = repository.add.call_args.args[0]
    assert saved_product.is_builder_eligible is True


def test_create_ineligible_product(service):
    # Obtiene el servicio y el repositorio simulado.
    product_service, repository = service

    # Prepara un producto sin las especificaciones necesarias.
    data = ProductCreate(
        name="GPU incompleta",
        brand="Marca",
        category=ProductCategory.GPU,
        price=500,
        stock=5,
        specs={},
    )

    # Ejecuta la creación del producto.
    product_service.create(data)

    # Comprueba que el producto no sea elegible.
    saved_product = repository.add.call_args.args[0]
    assert saved_product.is_builder_eligible is False


def test_update_product_to_eligible(service):
    # Obtiene el servicio y el repositorio simulado.
    product_service, repository = service

    # Crea un producto inicialmente no elegible.
    product = Product(
        id=1,
        name="GPU de prueba",
        brand="Marca",
        category=ProductCategory.GPU,
        price=500,
        stock=5,
        specs={},
        is_builder_eligible=False,
    )

    # Simula la búsqueda del producto existente.
    product_service._get_any = MagicMock(return_value=product)

    # Prepara una actualización con especificaciones válidas.
    data = ProductUpdate(specs=VALID_GPU_SPECS)

    # Ejecuta la actualización.
    product_service.update(1, data)

    # Comprueba que el producto ahora sea elegible.
    assert product.is_builder_eligible is True

    # Comprueba que se haya guardado el producto actualizado.
    repository.save.assert_called_once_with(product)


def test_update_product_to_ineligible(service):
    # Obtiene el servicio y el repositorio simulado.
    product_service, repository = service

    # Crea un producto inicialmente elegible.
    product = Product(
        id=1,
        name="GPU de prueba",
        brand="Marca",
        category=ProductCategory.GPU,
        price=500,
        stock=5,
        specs=VALID_GPU_SPECS,
        is_builder_eligible=True,
    )

    # Simula la búsqueda del producto existente.
    product_service._get_any = MagicMock(return_value=product)

    # Prepara una actualización que elimina las especificaciones.
    data = ProductUpdate(specs={})

    # Ejecuta la actualización.
    product_service.update(1, data)

    # Comprueba que el producto ahora no sea elegible.
    assert product.is_builder_eligible is False

    # Comprueba que se haya guardado el producto actualizado.
    repository.save.assert_called_once_with(product)
