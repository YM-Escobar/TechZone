
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.Models.build import Build, BuildItem
from app.Models.user import User
from app.Repository.advisory_repository import AdvisoryRepository
from app.Repository.build_repository import BuildRepository
from app.Repository.product_repository import ProductRepository
from app.Schema.build_schema import BuildCreate, BuildItemIn, BuildUpdate
from app.Schema.common_schema import PageResult, update_data

# Servicio que ejecuta y consolida las reglas de compatibilidad.
from app.Services.compatibility.compatibility_service import CompatibilityService

# Adaptador que transforma los productos de la base de datos
# en la estructura que necesita el motor de compatibilidad.
from app.Services.compatibility.compatibility_input import (
    build_compatibility_components,
)


class BuildService:
    def __init__(self, db: Session):
        # Inicializar los repositorios existentes.
        self.builds = BuildRepository(db)
        self.products = ProductRepository(db)
        self.advisories = AdvisoryRepository(db)

        # Inicializar el servicio de compatibilidad.
        self.compatibility = CompatibilityService()

    def list_public(
        self,
        skip: int,
        limit: int,
        search: str | None = None
    ) -> PageResult[Build]:
        items, total = self.builds.list_public(
            skip,
            limit,
            search=search
        )
        return PageResult(items, total, skip, limit)

    def list_mine(
        self,
        user: User,
        skip: int,
        limit: int
    ) -> PageResult[Build]:
        items, total = self.builds.list_by_owner(
            user.id,
            skip,
            limit
        )
        return PageResult(items, total, skip, limit)

    def get(self, build_id: int, viewer: User | None) -> Build:
        build = self.builds.get(build_id)

        if build is None or not self._can_view(build, viewer):
            raise NotFoundError("Build no encontrada")

        return build

    def create(self, owner: User, data: BuildCreate) -> Build:
        build = Build(
            user_id=owner.id,
            name=data.name,
            description=data.description,
            is_public=data.is_public,
        )

        self._set_items(build, data.items)

        return self.builds.add(build)

    def update(
        self,
        build_id: int,
        user: User,
        data: BuildUpdate
    ) -> Build:
        build = self._get_owned(build_id, user)

        for field, value in update_data(data, {"description"}).items():
            if field != "items":
                setattr(build, field, value)

        if data.items is not None:
            self._set_items(build, data.items)

        return self.builds.save(build)

    def delete(self, build_id: int, user: User) -> None:
        build = self.builds.get(build_id)

        if build is None:
            raise NotFoundError("Build no encontrada")

        if build.user_id != user.id and not user.is_admin:
            raise ForbiddenError("Solo puedes eliminar tus propias builds")

        self.builds.delete(build)

    def clone(self, build_id: int, user: User) -> Build:
        """Copia una build visible a las builds del usuario."""
        source = self.get(build_id, user)

        copy = Build(
            user_id=user.id,
            name=f"{source.name} (copia)"[:120],
            description=source.description
        )

        self._set_items(
            copy,
            [
                BuildItemIn(
                    product_id=item.product_id,
                    quantity=item.quantity
                )
                for item in source.items
            ]
        )

        return self.builds.add(copy)

    def evaluate_compatibility(
        self,
        items: list[BuildItemIn]
    ):
        """
        Evalúa la compatibilidad de una selección de componentes.

        Consulta los productos, comprueba que estén disponibles
        para el configurador y transforma sus datos para el Engine.

        No guarda ni modifica ninguna build.
        """

        # No tiene sentido evaluar una selección completamente vacía.
        if not items:
            raise BadRequestError(
                "Debes seleccionar al menos un componente para evaluar su compatibilidad"
            )

        # Agrupar productos repetidos sumando sus cantidades.
        quantities: dict[int, int] = {}

        for item in items:
            quantities[item.product_id] = (
                quantities.get(item.product_id, 0) + item.quantity
            )

        # Consultar todos los productos seleccionados.
        products_list = self.products.get_many(list(quantities))

        # Crear un diccionario para localizar cada producto por su ID.
        products = {
            product.id: product
            for product in products_list
        }

        # Verificar que todos existan, estén activos y sean elegibles.
        unavailable = [
            product_id
            for product_id in quantities
            if (
                product_id not in products
                or not products[product_id].is_active
                or not products[product_id].is_builder_eligible
            )
        ]

        if unavailable:
            raise BadRequestError(
                f"Productos no encontrados o no disponibles para el builder: {unavailable}"
            )

        # Convertir los productos al formato esperado por el Engine.
        components = build_compatibility_components(
            products=products_list,
            items=items
        )

        # Ejecutar las reglas y consolidar el diagnóstico.
        return self.compatibility.evaluate(components)

    def _can_view(
        self,
        build: Build,
        viewer: User | None
    ) -> bool:
        if build.is_public:
            return True

        if viewer is None:
            return False

        return (
            build.user_id == viewer.id
            or viewer.is_staff
            or self.advisories.is_build_recommended_to(
                build.id,
                viewer.id
            )
        )

    def _get_owned(self, build_id: int, user: User) -> Build:
        build = self.builds.get(build_id)

        if build is None:
            raise NotFoundError("Build no encontrada")

        if build.user_id != user.id:
            raise ForbiddenError("Solo puedes modificar tus propias builds")

        return build

    def _set_items(
        self,
        build: Build,
        items: list[BuildItemIn]
    ) -> None:
        # Agrupar productos repetidos sumando cantidades.
        quantities: dict[int, int] = {}

        for item in items:
            quantities[item.product_id] = (
                quantities.get(item.product_id, 0) + item.quantity
            )

        products = {
            product.id: product
            for product in self.products.get_many(list(quantities))
        }

        # Comprobar existencia, actividad y elegibilidad.
        unavailable = [
            pid
            for pid in quantities
            if (
                pid not in products
                or not products[pid].is_active
                or not products[pid].is_builder_eligible
            )
        ]

        if unavailable:
            raise BadRequestError(
                f"Productos no encontrados o no disponibles para el builder: {unavailable}"
            )

        # Actualizar los ítems existentes para evitar violar
        # la restricción única (build_id, product_id).
        existing = {
            item.product_id: item
            for item in build.items
        }

        for product_id, item in existing.items():
            if product_id not in quantities:
                build.items.remove(item)

        for product_id, quantity in quantities.items():
            if product_id in existing:
                existing[product_id].quantity = quantity
            else:
                build.items.append(
                    BuildItem(
                        product_id=product_id,
                        product=products[product_id],
                        quantity=quantity
                    )
                )
