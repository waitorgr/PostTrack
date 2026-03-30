from .models import ShipmentStatus


TERMINAL_STATUSES = frozenset({
    ShipmentStatus.DELIVERED,
    ShipmentStatus.CANCELLED,
    ShipmentStatus.RETURNED,
})


ALLOWED_TRANSITIONS = {
    ShipmentStatus.ACCEPTED: {
        ShipmentStatus.PICKED_UP_BY_DRIVER,
        ShipmentStatus.CANCELLED,
    },

    ShipmentStatus.PICKED_UP_BY_DRIVER: {
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.ARRIVED_AT_FACILITY,
    },

    ShipmentStatus.IN_TRANSIT: {
        ShipmentStatus.ARRIVED_AT_FACILITY,
    },

    ShipmentStatus.ARRIVED_AT_FACILITY: {
        ShipmentStatus.SORTED,
        ShipmentStatus.AVAILABLE_FOR_PICKUP,
    },

    ShipmentStatus.SORTED: {
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.OUT_FOR_DELIVERY,
        ShipmentStatus.AVAILABLE_FOR_PICKUP,
    },

    ShipmentStatus.OUT_FOR_DELIVERY: {
        ShipmentStatus.DELIVERED,
        ShipmentStatus.AVAILABLE_FOR_PICKUP,
    },

    ShipmentStatus.AVAILABLE_FOR_PICKUP: {
        ShipmentStatus.DELIVERED,
    },

    ShipmentStatus.DELIVERED: {
        ShipmentStatus.RETURNED,
    },

    ShipmentStatus.CANCELLED: set(),

    ShipmentStatus.RETURNED: set(),
}


def get_allowed_next_statuses(current_status: str) -> set[str]:
    """
    Повертає множину дозволених наступних статусів.
    Якщо статус невідомий — повертає порожню множину.
    """
    return set(ALLOWED_TRANSITIONS.get(current_status, set()))


def is_terminal_status(status: str) -> bool:
    return status in TERMINAL_STATUSES


def is_transition_allowed(current_status: str, new_status: str) -> bool:
    """
    Перевіряє, чи дозволений перехід між статусами.
    Однаковий статус -> False, щоб не плодити зайві tracking events.
    """
    if current_status == new_status:
        return False

    return new_status in ALLOWED_TRANSITIONS.get(current_status, set())


def validate_status_transition(current_status: str, new_status: str) -> None:
    """
    Кидає ValueError, якщо перехід недопустимий.
    """
    valid_statuses = set(ShipmentStatus.values)

    if current_status not in valid_statuses:
        raise ValueError(f"Невідомий поточний статус: '{current_status}'.")

    if new_status not in valid_statuses:
        raise ValueError(f"Невідомий новий статус: '{new_status}'.")

    if current_status == new_status:
        raise ValueError("Новий статус збігається з поточним.")

    allowed_statuses = get_allowed_next_statuses(current_status)
    if new_status not in allowed_statuses:
        allowed_display = ", ".join(sorted(allowed_statuses)) if allowed_statuses else "немає"
        raise ValueError(
            f"Перехід зі статусу '{current_status}' у '{new_status}' заборонений. "
            f"Дозволені переходи: {allowed_display}."
        )