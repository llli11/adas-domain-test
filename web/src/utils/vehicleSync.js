const TK = '_vehicle_data_ts'
const AK = 'vehicle_auto_sync_enabled'

export function notifyVehicleDataChanged() { localStorage.setItem(TK, Date.now().toString()) }
export function getVehicleDataTimestamp() { return parseInt(localStorage.getItem(TK) || '0') }
export function getAutoSyncEnabled() { return localStorage.getItem(AK) === 'true' }
export function setAutoSyncEnabled(v) { localStorage.setItem(AK, String(v)) }
