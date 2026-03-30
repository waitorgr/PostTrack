// src/utils/navigationConfig.js

export const NAVIGATION_CONFIG = {
  customer: [
    { label: 'Головна', to: '/customer/dashboard' },
    { label: 'Мої посилки', to: '/customer/shipments' },
  ],

  postal_worker: [
    { label: 'Головна', to: '/postal/dashboard' },
    { label: 'Посилки', to: '/postal/shipments' },
    { label: 'Створити посилку', to: '/postal/shipments/create' },
    { label: 'Dispatch', to: '/postal/dispatch' },
  ],

  warehouse_worker: [
    { label: 'Головна', to: '/warehouse/dashboard' },
    { label: 'Вхідні групи', to: '/warehouse/incoming' },
    { label: 'Посилки вузла', to: '/warehouse/parcels' },
    { label: 'Сортування', to: '/warehouse/sorting' },
  ],

  logist: [
    { label: 'Головна', to: '/logist/dashboard' },
    { label: 'Маршрути', to: '/logist/routes' },
    { label: 'Створити маршрут', to: '/logist/routes/create' },
    { label: 'Dispatch overview', to: '/logist/dispatches' },
    { label: 'Вузли', to: '/logist/nodes' },
  ],

  driver: [
    { label: 'Головна', to: '/driver/dashboard' },
    { label: 'Мої маршрути', to: '/driver/routes' },
  ],

  hr: [
    { label: 'Головна', to: '/hr/dashboard' },
    { label: 'Працівники', to: '/hr/users' },
    { label: 'Створити працівника', to: '/hr/users/create' },
    { label: 'Локації', to: '/hr/locations' },
  ],

  admin: [
    { label: 'Головна', to: '/admin/dashboard' },
    { label: 'Посилки', to: '/admin/shipments' },
    { label: 'Користувачі', to: '/admin/users' },
    { label: 'Локації', to: '/admin/locations' },
    { label: 'Маршрути', to: '/admin/routes' },
    { label: 'Аналітика', to: '/admin/analytics' },
    { label: 'Налаштування', to: '/admin/settings' },
  ],
}