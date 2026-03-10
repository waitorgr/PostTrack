from typing import List
from django.core.exceptions import ValidationError
from locations.models import Location, LocationType


def build_route(origin_po: Location, destination_po: Location) -> List[Location]:
    """
    Реалістичний базовий маршрут:
    PO(origin) -> SC(origin) -> DC(origin) -> (DC(dest) якщо інша область) -> SC(dest) -> PO(dest)

    Оптимізація:
    - якщо origin_sc == dest_sc: PO -> SC -> PO
    - якщо origin_dc == dest_dc, але різні SC: PO -> SC -> DC -> SC -> PO
    """
    if origin_po.type != LocationType.POST_OFFICE or destination_po.type != LocationType.POST_OFFICE:
        raise ValidationError("Origin and destination must be Post Offices.")

    origin_sc = origin_po.parent_sc
    dest_sc = destination_po.parent_sc
    if not origin_sc or not dest_sc:
        raise ValidationError("Post office must have parent_sc.")

    origin_dc = origin_sc.parent_dc
    dest_dc = dest_sc.parent_dc
    if not origin_dc or not dest_dc:
        raise ValidationError("Sorting city must have parent_dc.")

    # 1) Той самий район
    if origin_sc.id == dest_sc.id:
        return [origin_po, origin_sc, destination_po]

    # 2) Та сама область, але різні райони
    if origin_dc.id == dest_dc.id:
        return [origin_po, origin_sc, origin_dc, dest_sc, destination_po]

    # 3) Різні області
    return [origin_po, origin_sc, origin_dc, dest_dc, dest_sc, destination_po]
