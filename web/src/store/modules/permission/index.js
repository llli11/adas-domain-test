import { defineStore } from 'pinia'
import { basicRoutes, asyncRoutes, vueModules } from '@/router/routes'
import Layout from '@/layout/index.vue'
import api from '@/api'

function getComponent(componentPath) {
  if (!componentPath) return null
  
  let comp = null
  
  const resolveKey = (pattern) => {
    // 尝试两种key格式：绝对路径 /src/views/... 和 相对路径 ../../views/...
    return vueModules[pattern] || vueModules[pattern.replace('/src/', '../../')]
  }
  
  // 方式1: /src/views/ecu/target.vue
  comp = resolveKey(`/src/views${componentPath}.vue`)
  if (comp) return comp
  
  // 方式2: /src/views/ecu/target/index.vue
  comp = resolveKey(`/src/views${componentPath}/index.vue`)
  if (comp) return comp
  
  // 方式3: /src/views/target/index.vue (去掉ecu前缀)
  if (componentPath.startsWith('/ecu/')) {
    const shortPath = componentPath.replace('/ecu', '')
    comp = resolveKey(`/src/views${shortPath}/index.vue`)
    if (comp) return comp
    comp = resolveKey(`/src/views${shortPath}.vue`)
    if (comp) return comp
  }
  
  // 方式4: 完全去掉ecu，只保留最后的路径
  const parts = componentPath.split('/')
  const lastPart = parts[parts.length - 1]
  comp = resolveKey(`/src/views/${lastPart}/index.vue`)
  if (comp) return comp
  comp = resolveKey(`/src/views/${lastPart}.vue`)
  if (comp) return comp
  
  return comp
}

function buildRoutes(routes = []) {
  return routes.map((e) => {
    // 处理动态路由参数 (:xxx)
    const pathWithParams = e.path.includes(':') ? e.path : null
    
    const route = {
      name: e.name,
      path: e.path,
      component: shallowRef(Layout),
      isHidden: e.is_hidden,
      redirect: e.redirect || (e.children && e.children.length > 0 ? e.children[0].path : ''),
      meta: {
        title: e.name,
        icon: e.icon,
        order: e.order,
        keepAlive: e.keepalive,
      },
      children: [],
    }

    // 如果是一级菜单且有动态子路由，添加完整路径
    if (pathWithParams && e.children && e.children.length > 0) {
      route.path = e.path  // 保持动态路由
    }

    if (e.children && e.children.length > 0) {
      route.children = e.children.map((e_child) => {
        const childPath = e_child.path.includes(':') ? e_child.path : e_child.path
        return {
          name: e_child.name,
          path: childPath,
          component: getComponent(e_child.component),
          isHidden: e_child.is_hidden,
          meta: {
            title: e_child.name,
            icon: e_child.icon,
            order: e_child.order,
            keepAlive: e_child.keepalive,
          },
        }
      })
    } else {
      route.children.push({
        name: `${e.name}Default`,
        path: '',
        component: getComponent(e.component),
        isHidden: true,
        meta: {
          title: e.name,
          icon: e.icon,
          order: e.order,
          keepAlive: e.keepalive,
        },
      })
    }

    return route
  })
}

export const usePermissionStore = defineStore('permission', {
  state() {
    return {
      accessRoutes: [],
      accessApis: [],
    }
  },
  getters: {
    routes() {
      return basicRoutes.concat(asyncRoutes).concat(this.accessRoutes)
    },
    menus() {
      return this.routes.filter((route) => route.name && !route.isHidden)
    },
    apis() {
      return this.accessApis
    },
  },
  actions: {
    async generateRoutes() {
      const res = await api.getUserMenu()
      this.accessRoutes = buildRoutes(res.data)
      return this.accessRoutes
    },
    async getAccessApis() {
      const res = await api.getUserApi()
      this.accessApis = res.data
      return this.accessApis
    },
    resetPermission() {
      this.$reset()
    },
  },
})
