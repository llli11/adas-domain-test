<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <!-- 品牌欢迎卡 -->
      <n-card rounded-10>
        <div flex items-center>
          <icon-custom-logo text-60 color-primary mr-20></icon-custom-logo>
          <div>
            <p text-22 font-bold style="color: #1f2329">智驾域测试管理系统</p>
            <p mt-5 text-14 op-60>
              {{ $t('views.workbench.text_hello', { username: userStore.name }) }}，{{
                $t('views.workbench.text_welcome')
              }}
            </p>
          </div>
        </div>
      </n-card>

      <!-- 一级菜单快捷入口 -->
      <div grid grid-cols-2 gap-15 mt-15 md:grid-cols-4>
        <n-card
          v-for="item in shortcuts"
          :key="item.path"
          class="cursor-pointer"
          hover:card-shadow
          rounded-10
          @click="router.push(item.path)"
        >
          <div flex-col items-center f-c-c py-10>
            <div w-44 h-44 rounded-full f-c-c style="background: rgba(14, 163, 113, 0.12)">
              <span text-20 font-bold color-primary>{{ item.short }}</span>
            </div>
            <p mt-12 text-16 font-medium>{{ item.title }}</p>
          </div>
        </n-card>
      </div>

      <!-- 系统简介 -->
      <n-card mt-15 rounded-10 size="small" :segmented="true" title="系统简介">
        <p text-14 op-70 leading-relaxed>
          智驾域测试管理系统面向智驾域测试全流程，覆盖车辆管理、工具管理、版本管理、费用管理、测试路线等核心业务，助力测试数据数字化与协作高效化。
        </p>
      </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { usePermissionStore, useUserStore } from '@/store'
import { useI18n } from 'vue-i18n'

const { t } = useI18n({ useScope: 'global' })
const userStore = useUserStore()
const router = useRouter()
const permissionStore = usePermissionStore()

const shortcuts = computed(() => {
  return permissionStore.menus
    .filter((r) => r.path && r.path !== '/' && r.meta?.title)
    .sort((a, b) => (a.meta?.order || 0) - (b.meta?.order || 0))
    .map((r) => ({
      title: r.meta.title,
      path: r.path,
      short: r.meta.title.slice(0, 1),
    }))
})
</script>
