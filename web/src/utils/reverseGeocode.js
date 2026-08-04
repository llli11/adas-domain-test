/** 逆地理编码 — 经后端代理调用 Nominatim */
import { request } from './http'

export async function reverseGeocode(lat, lng) {
  if (lat == null || lng == null) return ''
  try {
    const res = await request.get('/vehicle/reverse-geocode', { params: { lat, lng } })
    return res?.data?.address || ''
  } catch {
    return ''
  }
}
