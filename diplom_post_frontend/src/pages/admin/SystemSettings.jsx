import { Stack, Typography } from '@mui/material'
import PageHeader from '../../components/common/PageHeader'
import Card from '../../components/ui/Card'

export default function SystemSettings() {
  return (
    <>
      <PageHeader
        title="Системні налаштування"
        subtitle="Інформація про конфігурацію та майбутні точки розширення"
      />

      <Stack spacing={3}>
        <Card>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Поточний стан
          </Typography>

          <Stack spacing={1}>
            <Typography>
              • Авторизація та рольовий доступ працюють через frontend routing і auth store.
            </Typography>
            <Typography>
              • Основні модулі системи вже розділені по ролях: postal, warehouse, logist, driver, hr, customer, admin.
            </Typography>
            <Typography>
              • Налаштування статусів, ролей і навігації винесені в конфігураційні файли frontend.
            </Typography>
          </Stack>
        </Card>

        <Card>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Що можна винести в реальні системні налаштування пізніше
          </Typography>

          <Stack spacing={1}>
            <Typography>• дефолтний page size для списків</Typography>
            <Typography>• правила відображення статусів</Typography>
            <Typography>• системні назви ролей і доступів</Typography>
            <Typography>• параметри інтеграції логістики</Typography>
            <Typography>• параметри трекінгу та логування подій</Typography>
          </Stack>
        </Card>

        <Card>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Примітка
          </Typography>

          <Typography color="text.secondary">
            Ця сторінка поки не змінює backend-конфігурацію. Щоб зробити її повноцінною,
            потрібні окремі API endpoints для читання та оновлення системних налаштувань.
          </Typography>
        </Card>
      </Stack>
    </>
  )
}