from shipments.models import ShipmentStatus

ALLOWED_TRANSITIONS = {

    ShipmentStatus.ACCEPTED: {
        ShipmentStatus.PICKED_UP_BY_DRIVER,
        ShipmentStatus.CANCELLED,
    },

    ShipmentStatus.PICKED_UP_BY_DRIVER: {
        ShipmentStatus.IN_TRANSIT,
    },

    ShipmentStatus.IN_TRANSIT: {
        ShipmentStatus.ARRIVED_AT_FACILITY,
    },

    ShipmentStatus.ARRIVED_AT_FACILITY: {
        ShipmentStatus.SORTED,
    },

    ShipmentStatus.SORTED: {
        ShipmentStatus.OUT_FOR_DELIVERY,
        ShipmentStatus.IN_TRANSIT,
    },

    ShipmentStatus.OUT_FOR_DELIVERY: {
        ShipmentStatus.AVAILABLE_FOR_PICKUP,
        ShipmentStatus.DELIVERED,
    },

    ShipmentStatus.AVAILABLE_FOR_PICKUP: {
        ShipmentStatus.DELIVERED,
    },

    ShipmentStatus.DELIVERED: set(),

    ShipmentStatus.CANCELLED: set(),

    ShipmentStatus.RETURNED: set(),
}