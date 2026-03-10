from shipments.models import ShipmentStatus

ALLOWED_TRANSITIONS = {
    # створення
    ShipmentStatus.CREATED: {
        ShipmentStatus.AT_POST_OFFICE,
        ShipmentStatus.CANCELLED,
    },

    # посилка на пошті (може бути і origin PO, і destination PO коли вже приїхала)
    ShipmentStatus.AT_POST_OFFICE: {
        ShipmentStatus.IN_TRANSIT_TO_SORTING_CITY,        # PO -> SC
        ShipmentStatus.READY_FOR_PICKUP,                  # якщо це destination PO (перевіряємо логікою викликача)
        ShipmentStatus.CANCELLED,
    },

    # в дорозі до SC
    ShipmentStatus.IN_TRANSIT_TO_SORTING_CITY: {
        ShipmentStatus.AT_SORTING_CITY,
    },

    # на SC
    ShipmentStatus.AT_SORTING_CITY: {
        ShipmentStatus.SORTED_WAITING_FOR_DISPATCH,       # після сортування на SC
        ShipmentStatus.CANCELLED,
    },

    # відсортовано на SC, чекає відправлення
    ShipmentStatus.SORTED_WAITING_FOR_DISPATCH: {
        ShipmentStatus.IN_TRANSIT_TO_DISTRIBUTION_CENTER, # SC -> DC (типовий шлях)
        ShipmentStatus.IN_TRANSIT_TO_POST_OFFICE,         # SC -> PO (якщо кінцева PO в цьому ж районі/області)
        ShipmentStatus.CANCELLED,
    },

    # в дорозі до DC (це може бути як "до свого DC", так і "між DC")
    ShipmentStatus.IN_TRANSIT_TO_DISTRIBUTION_CENTER: {
        ShipmentStatus.AT_DISTRIBUTION_CENTER,
    },

    # на DC
    ShipmentStatus.AT_DISTRIBUTION_CENTER: {
        ShipmentStatus.SORTED_WAITING_FOR_POST_OFFICE,    # після сортування на DC
        ShipmentStatus.CANCELLED,
    },

    # відсортовано на DC, чекає наступний хоп (DC/SC/PO)
    ShipmentStatus.SORTED_WAITING_FOR_POST_OFFICE: {
        ShipmentStatus.IN_TRANSIT_TO_DISTRIBUTION_CENTER, # DC -> DC (інша область) або DC -> DC(центральний)
        ShipmentStatus.IN_TRANSIT_TO_SORTING_CITY,        # DC -> SC (район призначення)
        ShipmentStatus.IN_TRANSIT_TO_POST_OFFICE,         # DC -> PO (якщо дозволяєш прямий)
        ShipmentStatus.CANCELLED,
    },

    # в дорозі до PO
    ShipmentStatus.IN_TRANSIT_TO_POST_OFFICE: {
        ShipmentStatus.AT_POST_OFFICE,
    },

    # готово до видачі
    ShipmentStatus.READY_FOR_PICKUP: {
        ShipmentStatus.DELIVERED,
        ShipmentStatus.CANCELLED,  # якщо дозволяєш скасування до видачі
    },

    # фінальні
    ShipmentStatus.DELIVERED: set(),
    ShipmentStatus.CANCELLED: set(),
}
