import axios from 'axios'

// ✅ 把 baseURL 改为相对路径，配合 vite 代理工作
const request = axios.create({
  baseURL: import.meta.env.VITE_BASE_API || '/api/v1',  // 👈 重点修改这里
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = 'Bearer ' + token
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('请求异常：', error)
    return Promise.reject(error)
  }
)

export default request