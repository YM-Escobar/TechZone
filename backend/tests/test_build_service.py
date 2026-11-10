
# ============================================================
# IMPORTS
# ============================================================

# SimpleNamespace permite crear objetos sencillos para simular usuarios.
from types import SimpleNamespace

# MagicMock y patch permiten simular repositorios y dependencias.
from unittest.mock import MagicMock, patch

# pytest permite organizar las pruebas y comprobar excepciones.
import pytest

# Excepciones utilizadas por BuildService.
# Importa las excepciones utilizadas para comprobar errores del servicio.
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError

# Modelos de ensamblajes y productos.
from app.Models.build import Build, BuildItem
from app.Models.product import Product, ProductCategory

# Esquemas utilizados para crear, actualizar y agregar componentes.
from app.Schema.build_schema import BuildCreate, BuildItemIn, BuildUpdate

# Servicio que contiene la lógica de los ensamblajes.
from app.Services.builds import BuildService


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def service():
    # Simula los tres repositorios utilizados por BuildService.
    with (
        patch("app.Services.builds.BuildRepository"),
        patch("app.Services.builds.ProductRepository") as product_repository,
        patch("app.Services.builds.AdvisoryRepository"),
    ):
        # Inicializa el servicio sin utilizar una base de datos real.
        build_service = BuildService(db=MagicMock())

        # Devuelve el servicio y su repositorio de productos simulado.
        yield build_service, product_repository.return_value


@pytest.fixture
def create_service():
    # Simula los repositorios utilizados por BuildService.
    with (
        patch("app.Services.builds.BuildRepository") as build_repository,
        patch("app.Services.builds.ProductRepository") as product_repository,
        patch("app.Services.builds.AdvisoryRepository") as advisory_repository,
    ):
        # Inicializa el servicio sin utilizar una base de datos real.
        build_service = BuildService(db=MagicMock())

        # Devuelve el servicio y los repositorios simulados.
        yield (
            build_service,
            build_repository.return_value,
            product_repository.return_value,
        )


# ============================================================
# HELPER PARA CREAR PRODUCTOS
# ============================================================

def make_product(
    product_id: int,
    is_active: bool = True,
    is_builder_eligible: bool = True,
) -> Product:
    # Crea un producto simulado con los estados indicados.
    return Product(
        id=product_id,
        name=f"GPU {product_id}",
        brand="Marca",
        category=ProductCategory.GPU,
        price=500,
        stock=5,
        specs={},
        is_active=is_active,
        is_builder_eligible=is_builder_eligible,
    )


# ============================================================
# PRUEBAS DE _set_items
# ============================================================

def test_set_items_accepts_active_eligible_products(service):
    # Obtiene el servicio y el repositorio simulado.
    build_service, products_repository = service

    # Prepara dos productos activos y elegibles.
    gpu = make_product(1)
    cpu = make_product(2)

    # Simula la consulta de productos.
    products_repository.get_many.return_value = [gpu, cpu]

    # Crea una build vacía.
    build = Build(name="PC Gamer", user_id=1)

    # Prepara los componentes que se agregarán.
    items = [
        BuildItemIn(product_id=1, quantity=1),
        BuildItemIn(product_id=2, quantity=1),
    ]

    # Ejecuta la asignación de componentes.
    build_service._set_items(build, items)

    # Comprueba que ambos componentes se hayan agregado.
    assert len(build.items) == 2

    # Comprueba que los productos agregados sean los esperados.
    assert {item.product.id for item in build.items} == {1, 2}


def test_set_items_rejects_ineligible_product(service):
    # Obtiene el servicio y el repositorio simulado.
    build_service, products_repository = service

    # Crea un producto activo, pero no elegible.
    gpu = make_product(1, is_builder_eligible=False)

    # Simula la consulta del producto.
    products_repository.get_many.return_value = [gpu]

    # Crea una build vacía.
    build = Build(name="PC Gamer", user_id=1)

    # Prepara el componente que se intentará agregar.
    items = [BuildItemIn(product_id=1)]

    # Comprueba que el servicio rechace el producto.
    with pytest.raises(BadRequestError):
        build_service._set_items(build, items)


def test_set_items_rejects_inactive_product(service):
    # Obtiene el servicio y el repositorio simulado.
    build_service, products_repository = service

    # Crea un producto elegible, pero inactivo.
    gpu = make_product(1, is_active=False)

    # Simula la consulta del producto.
    products_repository.get_many.return_value = [gpu]

    # Crea una build vacía.
    build = Build(name="PC Gamer", user_id=1)

    # Prepara el componente que se intentará agregar.
    items = [BuildItemIn(product_id=1)]

    # Comprueba que el servicio rechace el producto.
    with pytest.raises(BadRequestError):
        build_service._set_items(build, items)


def test_set_items_rejects_nonexistent_product(service):
    # Obtiene el servicio y el repositorio simulado.
    build_service, products_repository = service

    # Simula una consulta que no encuentra el producto.
    products_repository.get_many.return_value = []

    # Crea una build vacía.
    build = Build(name="PC Gamer", user_id=1)

    # Prepara un componente cuyo producto no existe.
    items = [BuildItemIn(product_id=999)]

    # Comprueba que el servicio rechace el producto.
    with pytest.raises(BadRequestError):
        build_service._set_items(build, items)


def test_set_items_combines_duplicate_products(service):
    # Obtiene el servicio y el repositorio simulado.
    build_service, products_repository = service

    # Crea un producto válido.
    gpu = make_product(1)

    # Simula la consulta del producto.
    products_repository.get_many.return_value = [gpu]

    # Crea una build vacía.
    build = Build(name="PC Gamer", user_id=1)

    # Agrega dos veces el mismo producto con cantidades diferentes.
    items = [
        BuildItemIn(product_id=1, quantity=2),
        BuildItemIn(product_id=1, quantity=3),
    ]

    # Ejecuta la asignación de componentes.
    build_service._set_items(build, items)

    # Comprueba que se haya creado un solo componente con cantidad 5.
    assert len(build.items) == 1

    # Comprueba que el componente corresponda al producto esperado.
    assert build.items[0].product.id == 1

    # Comprueba que las cantidades se hayan sumado correctamente.
    assert build.items[0].quantity == 5


# ============================================================
# PRUEBAS DE CREATE
# ============================================================

def test_create_build_with_valid_products(create_service):
    # Obtiene el servicio y los repositorios simulados.
    build_service, builds_repository, products_repository = create_service

    # Crea dos productos activos y elegibles.
    gpu = make_product(1)
    cpu = make_product(2)

    # Simula la búsqueda de los productos.
    products_repository.get_many.return_value = [gpu, cpu]

    # Simula un usuario propietario de la build.
    owner = MagicMock()
    owner.id = 10

    # Prepara los datos de creación de la build.
    data = BuildCreate(
        name="PC Gamer",
        description="Configuración para videojuegos",
        is_public=True,
        items=[
            BuildItemIn(product_id=1, quantity=1),
            BuildItemIn(product_id=2, quantity=1),
        ],
    )

    # Ejecuta la creación de la build.
    build_service.create(owner, data)

    # Comprueba que el repositorio haya recibido una build.
    builds_repository.add.assert_called_once()

    # Recupera la build enviada al repositorio.
    saved_build = builds_repository.add.call_args.args[0]

    # Comprueba los datos principales de la build.
    assert saved_build.name == "PC Gamer"
    assert saved_build.description == "Configuración para videojuegos"
    assert saved_build.is_public is True
    assert saved_build.user_id == 10

    # Comprueba que se hayan agregado los dos productos.
    assert len(saved_build.items) == 2

    # Comprueba que los productos sean los esperados.
    assert {item.product.id for item in saved_build.items} == {1, 2}


def test_create_build_rejects_ineligible_product(create_service):
    # Obtiene el servicio y los repositorios simulados.
    build_service, builds_repository, products_repository = create_service

    # Crea un producto activo, pero no elegible.
    gpu = make_product(1, is_builder_eligible=False)

    # Simula la búsqueda del producto.
    products_repository.get_many.return_value = [gpu]

    # Simula el usuario propietario.
    owner = MagicMock()
    owner.id = 10

    # Prepara una build con el producto no elegible.
    data = BuildCreate(
        name="PC Gamer",
        description="Configuración de prueba",
        is_public=False,
        items=[BuildItemIn(product_id=1, quantity=1)],
    )

    # Comprueba que la creación rechace el producto.
    with pytest.raises(BadRequestError):
        build_service.create(owner, data)

    # Comprueba que no se haya guardado la build.
    builds_repository.add.assert_not_called()


def test_create_build_rejects_nonexistent_product(create_service):
    # Obtiene el servicio y los repositorios simulados.
    build_service, builds_repository, products_repository = create_service

    # Simula una búsqueda sin resultados.
    products_repository.get_many.return_value = []

    # Simula el usuario propietario.
    owner = MagicMock()
    owner.id = 10

    # Prepara una build con un producto inexistente.
    data = BuildCreate(
        name="PC Gamer",
        description="Configuración de prueba",
        is_public=False,
        items=[BuildItemIn(product_id=999, quantity=1)],
    )

    # Comprueba que la creación rechace el producto inexistente.
    with pytest.raises(BadRequestError):
        build_service.create(owner, data)

    # Comprueba que no se haya guardado la build.
    builds_repository.add.assert_not_called()


# ============================================================
# PRUEBAS DE UPDATE
# ============================================================

def test_update_build_changes_general_fields(create_service):
    # Obtiene el servicio y los repositorios simulados.
    build_service, builds_repository, products_repository = create_service

    # Simula una build existente.
    build = Build(
        name="PC Inicial",
        description="Descripción inicial",
        user_id=10,
        is_public=False,
    )

    # Simula que el repositorio encuentra la build.
    builds_repository.get.return_value = build

    # Simula el usuario propietario.
    user = MagicMock()
    user.id = 10

    # Prepara los datos que se actualizarán.
    data = BuildUpdate(
        name="PC Gamer Actualizada",
        is_public=True,
    )

    # Ejecuta la actualización.
    build_service.update(1, user, data)

    # Comprueba que se hayan actualizado los campos.
    assert build.name == "PC Gamer Actualizada"
    assert build.is_public is True

    # Comprueba que la descripción se haya conservado.
    assert build.description == "Descripción inicial"

    # Comprueba que se haya guardado la build.
    builds_repository.save.assert_called_once_with(build)

    # Comprueba que no se hayan consultado productos.
    products_repository.get_many.assert_not_called()


def test_update_build_replaces_items(create_service):
    # Obtiene el servicio y los repositorios simulados.
    build_service, builds_repository, products_repository = create_service

    # Crea los productos anterior y nuevo.
    old_gpu = make_product(1)
    new_gpu = make_product(2)

    # Simula una build que ya contiene un producto.
    build = Build(
        name="PC Gamer",
        user_id=10,
        items=[
            BuildItem(
                product_id=1,
                product=old_gpu,
                quantity=1,
            )
        ],
    )

    # Simula la búsqueda de la build.
    builds_repository.get.return_value = build

    # Simula la búsqueda del nuevo producto.
    products_repository.get_many.return_value = [new_gpu]

    # Simula el usuario propietario.
    user = MagicMock()
    user.id = 10

    # Prepara la nueva lista de componentes.
    data = BuildUpdate(
        items=[BuildItemIn(product_id=2, quantity=3)]
    )

    # Ejecuta la actualización.
    build_service.update(1, user, data)

    # Comprueba que la lista anterior haya sido reemplazada.
    assert len(build.items) == 1

    # Comprueba que el nuevo producto sea el agregado.
    assert build.items[0].product.id == 2

    # Comprueba que se haya actualizado la cantidad.
    assert build.items[0].quantity == 3

    # Comprueba que se haya guardado la build.
    builds_repository.save.assert_called_once_with(build)


def test_update_build_rejects_non_owner(create_service):
    # Obtiene el servicio y los repositorios simulados.
    build_service, builds_repository, products_repository = create_service

    # Simula una build perteneciente a otro usuario.
    build = Build(
        name="PC Gamer",
        user_id=10,
    )

    # Simula la búsqueda de la build.
    builds_repository.get.return_value = build

    # Simula un usuario que no es propietario.
    user = MagicMock()
    user.id = 20
    user.is_staff = False

    # Prepara una actualización.
    data = BuildUpdate(name="PC Modificada")

    # Comprueba que se rechace la actualización.
    with pytest.raises(ForbiddenError):
        build_service.update(1, user, data)

    # Comprueba que no se haya guardado la build.
    builds_repository.save.assert_not_called()

    # Comprueba que no se hayan consultado productos.
    products_repository.get_many.assert_not_called()


def test_update_build_rejects_ineligible_product(create_service):
    # Obtiene el servicio y los repositorios simulados.
    build_service, builds_repository, products_repository = create_service

    # Crea una build existente.
    build = Build(
        name="PC Gamer",
        user_id=10,
    )

    # Simula la búsqueda de la build.
    builds_repository.get.return_value = build

    # Crea un producto activo, pero no elegible.
    gpu = make_product(1, is_builder_eligible=False)

    # Simula la búsqueda del producto.
    products_repository.get_many.return_value = [gpu]

    # Simula el usuario propietario.
    user = MagicMock()
    user.id = 10

    # Prepara una actualización con un producto no elegible.
    data = BuildUpdate(
        items=[BuildItemIn(product_id=1, quantity=1)]
    )

    # Comprueba que se rechace el producto.
    with pytest.raises(BadRequestError):
        build_service.update(1, user, data)

    # Comprueba que no se haya guardado la build.
    builds_repository.save.assert_not_called()


def test_update_build_clears_description(create_service):
    # Obtiene el servicio y los repositorios simulados.
    build_service, builds_repository, products_repository = create_service

    # Simula una build con descripción existente.
    build = Build(
        name="PC Gamer",
        description="Descripción anterior",
        user_id=10,
    )

    # Simula la búsqueda de la build.
    builds_repository.get.return_value = build

    # Simula el usuario propietario.
    user = MagicMock()
    user.id = 10

    # Envía explícitamente None para borrar la descripción.
    data = BuildUpdate(description=None)

    # Ejecuta la actualización.
    build_service.update(1, user, data)

    # Comprueba que la descripción se haya eliminado.
    assert build.description is None

    # Comprueba que se haya guardado la build.
    builds_repository.save.assert_called_once_with(build)

    # Comprueba que no se hayan consultado productos.
    products_repository.get_many.assert_not_called()


# ============================================================
# PRUEBAS DE CLONE
# ============================================================

def test_clone_build_copies_data_and_items(create_service):
    # Obtiene el servicio y los repositorios simulados.
    service, build_repository, product_repository = create_service

    # El usuario que clona es el propietario de la configuración original.
    user = SimpleNamespace(id=20, is_staff=False)

    # Producto que contiene la configuración original.
    gpu = make_product(product_id=1)

    # Configuración original con un componente.
    source = SimpleNamespace(
        id=10,
        user_id=20,
        name="PC Gamer",
        description="Configuración para gaming",
        is_public=False,
        items=[
            SimpleNamespace(
                product_id=1,
                product=gpu,
                quantity=2,
            )
        ],
    )

    # Simula la recuperación de la configuración.
    build_repository.get.return_value = source
    build_repository.add.side_effect = lambda build: build

    # get_many debe devolver una lista de productos, no un diccionario.
    product_repository.get_many.return_value = [gpu]

    # Ejecuta la clonación.
    result = service.clone(10, user)

    # Verifica los datos generales de la copia.
    assert result.user_id == user.id
    assert result.name == "PC Gamer (copia)"
    assert result.description == source.description

    # Verifica que se haya copiado el componente y su cantidad.
    assert len(result.items) == 1
    assert result.items[0].product_id == 1
    assert result.items[0].quantity == 2

    # La copia debe guardarse mediante el repositorio.
    build_repository.add.assert_called_once()


def test_clone_build_truncates_long_name(create_service):
    # Obtiene el servicio y los repositorios simulados.
    service, build_repository, product_repository = create_service

    # Usuario propietario de la configuración original.
    user = SimpleNamespace(id=20, is_staff=False)

    # Configuración original con nombre de 120 caracteres.
    source = SimpleNamespace(
        id=10,
        user_id=20,
        name="A" * 120,
        description=None,
        is_public=False,
        items=[],
    )

    # Simula la recuperación de la configuración.
    build_repository.get.return_value = source
    # Simula que el repositorio guarda y devuelve la configuración recibida.
    build_repository.add.side_effect = lambda build: build

    # La configuración no tiene productos que consultar.
    product_repository.get_many.return_value = []

    # Ejecuta la clonación.
    result = service.clone(10, user)

    # Comprueba que el nombre de la copia no supere los 120 caracteres.
    assert len(result.name) == 120
    assert result.name == ("A" * 120 + " (copia)")[:120]

    # Comprueba que la copia se haya guardado.
    build_repository.add.assert_called_once()


def test_clone_build_rejects_ineligible_product(create_service):
    # Obtiene el servicio y los repositorios simulados.
    service, build_repository, product_repository = create_service

    # Usuario propietario de la configuración original.
    user = SimpleNamespace(id=20, is_staff=False)

    # Producto activo, pero no elegible.
    ineligible_gpu = make_product(
        product_id=1,
        is_builder_eligible=False,
    )

    # Configuración original que contiene el producto no elegible.
    source = SimpleNamespace(
        id=10,
        user_id=20,
        name="PC Gamer",
        description=None,
        is_public=False,
        items=[
            SimpleNamespace(
                product_id=1,
                product=ineligible_gpu,
                quantity=1,
            )
        ],
    )

    # Simula la recuperación de la configuración.
    build_repository.get.return_value = source

    # Simula la búsqueda del producto.
    product_repository.get_many.return_value = [ineligible_gpu]

    # Comprueba que la clonación rechace el producto no elegible.
    with pytest.raises(BadRequestError):
        service.clone(10, user)

    # Comprueba que no se haya guardado la copia.
    build_repository.add.assert_not_called()


def test_clone_build_rejects_inactive_product(create_service):
    # Obtiene el servicio y los repositorios simulados.
    service, build_repository, product_repository = create_service

    # Usuario propietario de la configuración original.
    user = SimpleNamespace(id=20, is_staff=False)

    # Producto elegible, pero inactivo.
    inactive_gpu = make_product(
        product_id=1,
        is_active=False,
    )

    # Configuración original que contiene el producto inactivo.
    source = SimpleNamespace(
        id=10,
        user_id=20,
        name="PC Gamer",
        description=None,
        is_public=False,
        items=[
            SimpleNamespace(
                product_id=1,
                product=inactive_gpu,
                quantity=1,
            )
        ],
    )

    # Simula la recuperación de la configuración.
    build_repository.get.return_value = source

    # Simula la búsqueda del producto.
    product_repository.get_many.return_value = [inactive_gpu]

    # Comprueba que la clonación rechace el producto inactivo.
    with pytest.raises(BadRequestError):
        service.clone(10, user)

    # Comprueba que no se haya guardado la copia.
    build_repository.add.assert_not_called()

def test_list_public_returns_paginated_result(create_service):
    # Obtiene el servicio y el repositorio simulado.
    service, build_repository, _ = create_service

    # Simula las configuraciones públicas que devuelve el repositorio.
    builds = [
        SimpleNamespace(id=1, name="PC Gamer"),
        SimpleNamespace(id=2, name="PC Oficina"),
    ]
    build_repository.list_public.return_value = (builds, 10)

    # Ejecuta la consulta con paginación y búsqueda.
    result = service.list_public(skip=0, limit=5, search="PC")

    # Verifica que se haya consultado correctamente el repositorio.
    build_repository.list_public.assert_called_once_with(
        0, 5, search="PC"
    )

    # Verifica los datos de paginación.
    assert result.items == builds
    assert result.total == 10
    assert result.skip == 0
    assert result.limit == 5


def test_list_mine_returns_paginated_result(create_service):
    # Obtiene el servicio y el repositorio simulado.
    service, build_repository, _ = create_service

    # Usuario propietario de las configuraciones.
    user = SimpleNamespace(id=20, is_staff=False)

    # Simula las configuraciones pertenecientes al usuario.
    builds = [
        SimpleNamespace(id=1, name="Mi PC"),
        SimpleNamespace(id=2, name="PC Trabajo"),
    ]
    build_repository.list_by_owner.return_value = (builds, 2)

    # Ejecuta la consulta.
    result = service.list_mine(user=user, skip=0, limit=10)

    # Verifica que se haya consultado por el ID del propietario.
    build_repository.list_by_owner.assert_called_once_with(
        20, 0, 10
    )

    # Verifica los datos devueltos.
    assert result.items == builds
    assert result.total == 2
    assert result.skip == 0
    assert result.limit == 10


def test_list_public_builds_returns_paginated_result(create_service):
    # Obtiene el servicio y el repositorio simulado.
    service, build_repository, _ = create_service

    # Configuraciones públicas simuladas.
    builds = [
        SimpleNamespace(id=1, name="PC Gamer"),
        SimpleNamespace(id=2, name="PC Trabajo"),
    ]

    # Simula la respuesta del repositorio.
    build_repository.list_public.return_value = (builds, 10)

    # Ejecuta la consulta.
    result = service.list_public(skip=0, limit=2, search="PC")

    # Verifica los resultados y la paginación.
    assert result.items == builds
    assert result.total == 10
    assert result.skip == 0
    assert result.limit == 2

    # Verifica que se envíen correctamente los parámetros.
    build_repository.list_public.assert_called_once_with(
        0, 2, search="PC"
    )


def test_list_mine_returns_user_builds(create_service):
    # Obtiene el servicio y el repositorio simulado.
    service, build_repository, _ = create_service

    # Usuario propietario de las configuraciones.
    user = SimpleNamespace(id=20)

    # Configuraciones pertenecientes al usuario.
    builds = [
        SimpleNamespace(id=1, user_id=20),
        SimpleNamespace(id=2, user_id=20),
    ]

    # Simula la respuesta del repositorio.
    build_repository.list_by_owner.return_value = (builds, 2)

    # Ejecuta la consulta.
    result = service.list_mine(user, skip=0, limit=10)

    # Verifica los resultados.
    assert result.items == builds
    assert result.total == 2
    assert result.skip == 0
    assert result.limit == 10

    # Verifica que se consulte utilizando el ID del usuario.
    build_repository.list_by_owner.assert_called_once_with(
        user.id, 0, 10
    )

def test_get_public_build_without_user(create_service):
    # Obtiene el servicio y el repositorio simulado.
    service, build_repository, _ = create_service

    # Configuración pública.
    build = SimpleNamespace(
        id=1,
        user_id=20,
        is_public=True,
    )

    build_repository.get.return_value = build

    # Un visitante sin sesión puede consultar una configuración pública.
    result = service.get(1, None)

    assert result is build
    build_repository.get.assert_called_once_with(1)


def test_get_private_build_by_owner(create_service):
    # Obtiene el servicio y los repositorios simulados.
    service, build_repository, _ = create_service

    # Propietario de la configuración.
    user = SimpleNamespace(id=20, is_staff=False)

    # Configuración privada.
    build = SimpleNamespace(
        id=1,
        user_id=20,
        is_public=False,
    )

    build_repository.get.return_value = build

    # El propietario puede consultar su configuración.
    result = service.get(1, user)

    assert result is build


def test_get_private_build_by_staff(create_service):
    # Obtiene el servicio y los repositorios simulados.
    service, build_repository, _ = create_service

    # Usuario con permisos de staff.
    user = SimpleNamespace(id=30, is_staff=True)

    # Configuración privada de otro usuario.
    build = SimpleNamespace(
        id=1,
        user_id=20,
        is_public=False,
    )

    build_repository.get.return_value = build

    # El usuario staff puede consultar la configuración.
    result = service.get(1, user)

    assert result is build


def test_get_private_build_recommended_by_advisory(create_service):
    # Obtiene el servicio y los repositorios simulados.
    service, build_repository, _ = create_service

    # Usuario que recibió la recomendación.
    user = SimpleNamespace(id=30, is_staff=False)

    # Configuración privada de otro usuario.
    build = SimpleNamespace(
        id=1,
        user_id=20,
        is_public=False,
    )

    build_repository.get.return_value = build

    # Simula que la configuración fue recomendada al usuario.
    service.advisories.is_build_recommended_to.return_value = True

    # El usuario puede consultar la configuración recomendada.
    result = service.get(1, user)

    assert result is build

    service.advisories.is_build_recommended_to.assert_called_once_with(
        build.id,
        user.id,
    )


def test_get_private_build_rejects_unauthorized_user(create_service):
    # Obtiene el servicio y los repositorios simulados.
    service, build_repository, _ = create_service

    # Usuario sin permisos.
    user = SimpleNamespace(id=30, is_staff=False)

    # Configuración privada de otro usuario.
    build = SimpleNamespace(
        id=1,
        user_id=20,
        is_public=False,
    )

    build_repository.get.return_value = build

    # No existe una recomendación para este usuario.
    service.advisories.is_build_recommended_to.return_value = False

    # Un usuario sin autorización no puede consultar la configuración.
    with pytest.raises(NotFoundError):
        service.get(1, user)


def test_get_nonexistent_build(create_service):
    # Obtiene el servicio y el repositorio simulado.
    service, build_repository, _ = create_service

    # Simula que la configuración no existe.
    build_repository.get.return_value = None

    # La consulta debe producir NotFoundError.
    with pytest.raises(NotFoundError):
        service.get(999, None)

def test_delete_build_by_owner(create_service):
    # Obtiene el servicio y el repositorio simulado.
    service, build_repository, _ = create_service

    # Propietario de la configuración.
    user = SimpleNamespace(id=20, is_admin=False)

    # Configuración perteneciente al usuario.
    build = SimpleNamespace(id=1, user_id=20)

    build_repository.get.return_value = build

    # Ejecuta la eliminación.
    result = service.delete(1, user)

    # El método no debe devolver ningún valor.
    assert result is None

    # Verifica que el repositorio reciba la configuración correcta.
    build_repository.delete.assert_called_once_with(build)


def test_delete_build_by_admin(create_service):
    # Obtiene el servicio y el repositorio simulado.
    service, build_repository, _ = create_service

    # Administrador que elimina una configuración ajena.
    user = SimpleNamespace(id=30, is_admin=True)

    # Configuración de otro usuario.
    build = SimpleNamespace(id=1, user_id=20)

    build_repository.get.return_value = build

    # Ejecuta la eliminación.
    result = service.delete(1, user)

    # Verifica que la operación termine correctamente.
    assert result is None
    build_repository.delete.assert_called_once_with(build)


def test_delete_build_rejects_non_owner(create_service):
    # Obtiene el servicio y el repositorio simulado.
    service, build_repository, _ = create_service

    # Usuario sin permisos administrativos.
    user = SimpleNamespace(id=30, is_admin=False)

    # Configuración perteneciente a otro usuario.
    build = SimpleNamespace(id=1, user_id=20)

    build_repository.get.return_value = build

    # La eliminación debe ser rechazada.
    with pytest.raises(ForbiddenError):
        service.delete(1, user)

    # Verifica que el repositorio no elimine la configuración.
    build_repository.delete.assert_not_called()


def test_delete_nonexistent_build(create_service):
    # Obtiene el servicio y el repositorio simulado.
    service, build_repository, _ = create_service

    # Simula que la configuración no existe.
    build_repository.get.return_value = None

    # La operación debe generar NotFoundError.
    with pytest.raises(NotFoundError):
        service.delete(999, SimpleNamespace(id=20, is_admin=False))

    # No debe intentarse eliminar una configuración inexistente.
    build_repository.delete.assert_not_called()
