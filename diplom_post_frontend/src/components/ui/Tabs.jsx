import { Tabs as MuiTabs, Tab } from '@mui/material'

export default function Tabs({ value, onChange, items = [] }) {
  return (
    <MuiTabs value={value} onChange={onChange}>
      {items.map((item) => (
        <Tab key={item.value} value={item.value} label={item.label} />
      ))}
    </MuiTabs>
  )
}