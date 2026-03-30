// utils/roleConfig.js

/**
 * Централізована конфігурація ролей
 * Використовується для уникнення хаосу з if role === ...
 */

import {
  HomeIcon,
  PackageIcon,
  PlusIcon,
  TruckIcon,
  InboxIcon,
  PackagesIcon,
  SortIcon,
  RouteIcon,
  MapIcon,
  DispatchIcon,
  UsersIcon,
  UserPlusIcon,
  BuildingIcon,
  SettingsIcon,
  AnalyticsIcon,
} from '@/components/icons';

import PostalDashboard from '@/pages/postal/PostalDashboard';
import WarehouseDashboard from '@/pages/warehouse/WarehouseDashboard';
import LogistDashboard from '@/pages/logist/LogistDashboard';
import DriverDashboard from '@/pages/driver/DriverDashboard';
import CustomerDashboard from '@/pages/customer/CustomerDashboard';
import HRDashboard from '@/pages/hr/HRDashboard';
import AdminDashboard from '@/pages/admin/AdminDashboard';

// ============================================================================
// КОНСТАНТИ РОЛЕЙ
// ============================================================================

export const ROLES = {
  CUSTOMER: 'customer',
  POSTAL_WORKER: 'postal_worker',
  SORTING_CENTER_WORKER: 'sorting_center_worker',
  DISTRIBUTION_CENTER_WORKER: 'distribution_center_worker',
  DRIVER: 'driver',
  LOGIST: 'logist',
  HR: 'hr',
  ADMIN: 'admin',
};

// Об'єднані ролі warehouse workers
export const WAREHOUSE_ROLES = [
  ROLES.SORTING_CENTER_WORKER,
  ROLES.DISTRIBUTION_CENTER_WORKER,
];

// Всі внутрішні ролі (не customer)
export const INTERNAL_ROLES = [
  ROLES.POSTAL_WORKER,
  ...WAREHOUSE_ROLES,
  ROLES.DRIVER,
  ROLES.LOGIST,
  ROLES.HR,
  ROLES.ADMIN,
];

// ============================================================================
// HOME ROUTES — куди редиректити після логіну
// ============================================================================

export const ROLE_HOME_ROUTES = {
  [ROLES.CUSTOMER]: '/customer/dashboard',
  [ROLES.POSTAL_WORKER]: '/postal/dashboard',
  [ROLES.SORTING_CENTER_WORKER]: '/warehouse/dashboard',
  [ROLES.DISTRIBUTION_CENTER_WORKER]: '/warehouse/dashboard',
  [ROLES.DRIVER]: '/driver/dashboard',
  [ROLES.LOGIST]: '/logist/dashboard',
  [ROLES.HR]: '/hr/dashboard',
  [ROLES.ADMIN]: '/admin/dashboard',
};

// ============================================================================
// DASHBOARD COMPONENTS — який dashboard показувати
// ============================================================================

export const ROLE_DASHBOARDS = {
  [ROLES.CUSTOMER]: CustomerDashboard,
  [ROLES.POSTAL_WORKER]: PostalDashboard,
  [ROLES.SORTING_CENTER_WORKER]: WarehouseDashboard,
  [ROLES.DISTRIBUTION_CENTER_WORKER]: WarehouseDashboard,
  [ROLES.DRIVER]: DriverDashboard,
  [ROLES.LOGIST]: LogistDashboard,
  [ROLES.HR]: HRDashboard,
  [ROLES.ADMIN]: AdminDashboard,
};

// ============================================================================
// NAVIGATION — меню для кожної ролі
// ============================================================================

export const ROLE_NAVIGATION = {
  [ROLES.CUSTOMER]: [
    {
      icon: HomeIcon,
      label: 'Головна',
      to: '/customer/dashboard',
    },
    {
      icon: PackageIcon,
      label: 'Мої посилки',
      to: '/customer/shipments',
    },
  ],

  [ROLES.POSTAL_WORKER]: [
    {
      icon: HomeIcon,
      label: 'Головна',
      to: '/postal/dashboard',
    },
    {
      icon: PackageIcon,
      label: 'Посилки',
      to: '/postal/shipments',
    },
    {
      icon: PlusIcon,
      label: 'Створити посилку',
      to: '/postal/shipments/create',
    },
    {
      icon: TruckIcon,
      label: 'Dispatch',
      to: '/postal/dispatch',
    },
  ],

  [ROLES.SORTING_CENTER_WORKER]: [
    {
      icon: HomeIcon,
      label: 'Головна',
      to: '/warehouse/dashboard',
    },
    {
      icon: InboxIcon,
      label: 'Вхідні групи',
      to: '/warehouse/incoming',
    },
    {
      icon: PackagesIcon,
      label: 'Посилки',
      to: '/warehouse/parcels',
    },
    {
      icon: SortIcon,
      label: 'Сортування',
      to: '/warehouse/sorting',
    },
  ],

  [ROLES.DISTRIBUTION_CENTER_WORKER]: [
    {
      icon: HomeIcon,
      label: 'Головна',
      to: '/warehouse/dashboard',
    },
    {
      icon: InboxIcon,
      label: 'Вхідні групи',
      to: '/warehouse/incoming',
    },
    {
      icon: PackagesIcon,
      label: 'Посилки',
      to: '/warehouse/parcels',
    },
    {
      icon: SortIcon,
      label: 'Сортування',
      to: '/warehouse/sorting',
    },
  ],

  [ROLES.DRIVER]: [
    {
      icon: HomeIcon,
      label: 'Головна',
      to: '/driver/dashboard',
    },
    {
      icon: RouteIcon,
      label: 'Маршрути',
      to: '/driver/routes',
    },
  ],

  [ROLES.LOGIST]: [
    {
      icon: HomeIcon,
      label: 'Головна',
      to: '/logist/dashboard',
    },
    {
      icon: RouteIcon,
      label: 'Маршрути',
      to: '/logist/routes',
    },
    {
      icon: PlusIcon,
      label: 'Створити маршрут',
      to: '/logist/routes/create',
    },
    {
      icon: DispatchIcon,
      label: 'Dispatch групи',
      to: '/logist/dispatches',
    },
    {
      icon: MapIcon,
      label: 'Вузли',
      to: '/logist/nodes',
    },
  ],

  [ROLES.HR]: [
    {
      icon: HomeIcon,
      label: 'Головна',
      to: '/hr/dashboard',
    },
    {
      icon: UsersIcon,
      label: 'Працівники',
      to: '/hr/users',
    },
    {
      icon: UserPlusIcon,
      label: 'Додати працівника',
      to: '/hr/users/create',
    },
    {
      icon: BuildingIcon,
      label: 'Локації',
      to: '/hr/locations',
    },
  ],

  [ROLES.ADMIN]: [
    {
      icon: HomeIcon,
      label: 'Огляд системи',
      to: '/admin/dashboard',
    },
    {
      icon: PackageIcon,
      label: 'Посилки',
      to: '/admin/shipments',
    },
    {
      icon: RouteIcon,
      label: 'Маршрути',
      to: '/admin/routes',
    },
    {
      icon: UsersIcon,
      label: 'Користувачі',
      to: '/admin/users',
    },
    {
      icon: BuildingIcon,
      label: 'Локації',
      to: '/admin/locations',
    },
    {
      icon: AnalyticsIcon,
      label: 'Аналітика',
      to: '/admin/analytics',
    },
    {
      icon: SettingsIcon,
      label: 'Налаштування',
      to: '/admin/settings',
    },
  ],
};

// ============================================================================
// PERMISSIONS — які дії дозволені для ролі
// ============================================================================

export const ROLE_PERMISSIONS = {
  [ROLES.CUSTOMER]: {
    canViewOwnShipments: true,
    canTrackShipment: true,
  },

  [ROLES.POSTAL_WORKER]: {
    canCreateShipment: true,
    canViewLocationShipments: true,
    canUpdateShipmentStatus: true,
    canHandOverShipment: true,
    canCreateDispatchGroup: true,
    canViewLocationDispatches: true,
  },

  [ROLES.SORTING_CENTER_WORKER]: {
    canReceiveDispatchGroup: true,
    canSortShipments: true,
    canViewNodeShipments: true,
    canUpdateShipmentStatus: true,
    canCreateDispatchGroup: true,
  },

  [ROLES.DISTRIBUTION_CENTER_WORKER]: {
    canReceiveDispatchGroup: true,
    canSortShipments: true,
    canViewNodeShipments: true,
    canUpdateShipmentStatus: true,
    canCreateDispatchGroup: true,
  },

  [ROLES.DRIVER]: {
    canViewAssignedRoutes: true,
    canConfirmDeparture: true,
    canConfirmArrival: true,
    canConfirmHandover: true,
  },

  [ROLES.LOGIST]: {
    canCreateRoute: true,
    canViewRegionRoutes: true,
    canEditRoute: true,
    canCancelRoute: true,
    canViewRegionDispatches: true,
    canViewNodes: true,
  },

  [ROLES.HR]: {
    canCreateUser: true,
    canViewAllUsers: true,
    canEditUser: true,
    canDeactivateUser: true,
    canViewLocations: true,
  },

  [ROLES.ADMIN]: {
    canViewAllShipments: true,
    canViewAllRoutes: true,
    canViewAllUsers: true,
    canManageLocations: true,
    canViewAnalytics: true,
    canManageSettings: true,
    canDeactivateHR: true, // Спеціальний дозвіл
  },
};

// ============================================================================
// LAYOUT CONFIG — який layout використовувати
// ============================================================================

export const ROLE_LAYOUTS = {
  [ROLES.CUSTOMER]: 'CustomerLayout',
  [ROLES.POSTAL_WORKER]: 'InternalLayout',
  [ROLES.SORTING_CENTER_WORKER]: 'InternalLayout',
  [ROLES.DISTRIBUTION_CENTER_WORKER]: 'InternalLayout',
  [ROLES.DRIVER]: 'DriverLayout',
  [ROLES.LOGIST]: 'InternalLayout',
  [ROLES.HR]: 'InternalLayout',
  [ROLES.ADMIN]: 'AdminLayout',
};

// ============================================================================
// ХЕЛПЕРИ
// ============================================================================

/**
 * Отримати home route для ролі
 */
export const getHomeRoute = (role) => {
  return ROLE_HOME_ROUTES[role] || '/';
};

/**
 * Отримати навігацію для ролі
 */
export const getNavigation = (role) => {
  return ROLE_NAVIGATION[role] || [];
};

/**
 * Отримати dashboard компонент для ролі
 */
export const getDashboard = (role) => {
  return ROLE_DASHBOARDS[role] || null;
};

/**
 * Перевірити чи має роль певний дозвіл
 */
export const hasPermission = (role, permission) => {
  return ROLE_PERMISSIONS[role]?.[permission] || false;
};

/**
 * Перевірити чи роль належить до internal staff
 */
export const isInternalRole = (role) => {
  return INTERNAL_ROLES.includes(role);
};

/**
 * Перевірити чи роль є warehouse worker
 */
export const isWarehouseRole = (role) => {
  return WAREHOUSE_ROLES.includes(role);
};

/**
 * Отримати label для ролі
 */
export const getRoleLabel = (role) => {
  const labels = {
    [ROLES.CUSTOMER]: 'Клієнт',
    [ROLES.POSTAL_WORKER]: 'Працівник відділення',
    [ROLES.SORTING_CENTER_WORKER]: 'Працівник сортувального центру',
    [ROLES.DISTRIBUTION_CENTER_WORKER]: 'Працівник розподільчого центру',
    [ROLES.DRIVER]: 'Водій',
    [ROLES.LOGIST]: 'Логіст',
    [ROLES.HR]: 'HR',
    [ROLES.ADMIN]: 'Адміністратор',
  };
  return labels[role] || role;
};
