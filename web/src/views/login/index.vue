<template>
  <div class="login-bg">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
    <div class="blob blob-4"></div>
    <div class="dots"></div>

    <div class="login-card">
      <div flex-col items-center f-c-c mb-35>
        <icon-custom-logo class="logo-drive" text-80 color-primary></icon-custom-logo>
        <h1 mt-18 text-30 font-bold class="gradient-title">{{ $t('app_name') }}</h1>
        <p mt-10 text-15 op-50>欢迎登录，请输入您的账号</p>
      </div>

      <n-input
        v-model:value="loginInfo.username"
        autofocus
        size="large"
        class="h-54 text-16"
        placeholder="请输入用户名"
        :maxlength="20"
      />
      <n-input
        v-model:value="loginInfo.password"
        size="large"
        class="mt-18 h-54 text-16"
        type="password"
        show-password-on="mousedown"
        placeholder="请输入密码"
        :maxlength="20"
        @keypress.enter="handleLogin"
      />

      <n-button
        class="mt-30 login-btn"
        h-54
        w-full
        rounded-8
        text-16
        type="primary"
        :loading="loading"
        @click="handleLogin"
      >
        {{ $t('views.login.text_login') }}
      </n-button>

      <p mt-30 text-center text-12 op-40>© 智驾域测试管理系统</p>
    </div>
  </div>
</template>

<script setup>
import { useMessage } from 'naive-ui'
import { lStorage, setToken } from '@/utils'
import api from '@/api'
import { addDynamicRoutes } from '@/router'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { query } = useRoute()
const { t } = useI18n({ useScope: 'global' })
const $message = useMessage()

const loginInfo = ref({
  username: '',
  password: '',
})

initLoginInfo()

function initLoginInfo() {
  const localLoginInfo = lStorage.get('loginInfo')
  if (localLoginInfo) {
    loginInfo.value.username = localLoginInfo.username || ''
    loginInfo.value.password = localLoginInfo.password || ''
  }
}

const loading = ref(false)
async function handleLogin() {
  const { username, password } = loginInfo.value
  if (!username || !password) {
    $message.warning(t('views.login.message_input_username_password'))
    return
  }
  try {
    loading.value = true
    $message.loading(t('views.login.message_verifying'))
    const res = await api.login({ username, password: password.toString() })
    $message.success(t('views.login.message_login_success'))
    setToken(res.data.access_token)
    await addDynamicRoutes()
    if (query.redirect) {
      const path = query.redirect
      console.log('path', { path, query })
      Reflect.deleteProperty(query, 'redirect')
      router.push({ path, query })
    } else {
      router.push('/')
    }
  } catch (e) {
    console.error('login error', e)
    $message.error(e?.message || '登录失败，请检查账号密码或网络连接')
  }
  loading.value = false
}
</script>

<style scoped>
.login-bg {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e7f3ef 0%, #e3edfa 35%, #ece7f7 70%, #e7f3ef 100%);
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(75px);
  opacity: 0.5;
  pointer-events: none;
}
.blob-1 {
  width: 560px;
  height: 560px;
  background: radial-gradient(circle, #0ea371, transparent 70%);
  top: -140px;
  left: -120px;
  animation: float-a 20s ease-in-out infinite;
}
.blob-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #1677ff, transparent 70%);
  bottom: -150px;
  right: -130px;
  animation: float-b 24s ease-in-out infinite;
}
.blob-3 {
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, #06b6d4, transparent 70%);
  top: 30%;
  left: 48%;
  animation: float-c 28s ease-in-out infinite;
}
.blob-4 {
  width: 380px;
  height: 380px;
  background: radial-gradient(circle, #8b5cf6, transparent 70%);
  top: 60%;
  left: 10%;
  animation: float-d 32s ease-in-out infinite;
}

.dots {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(14, 99, 163, 0.08) 1px, transparent 1px);
  background-size: 24px 24px;
  pointer-events: none;
}

.login-card {
  position: relative;
  z-index: 2;
  width: 520px;
  max-width: 92vw;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(22px);
  padding: 56px;
  box-shadow: 0 16px 48px rgba(14, 99, 163, 0.14), 0 2px 10px rgba(0, 0, 0, 0.04);
  animation: card-in 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

.gradient-title {
  background: linear-gradient(90deg, #1677ff, #0ea371, #06b6d4);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  letter-spacing: 1px;
}

.logo-drive {
  animation: logo-drive 4s ease-in-out infinite;
}

.login-btn {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(22, 119, 255, 0.35);
}
.login-btn:active {
  transform: translateY(0);
}

@keyframes float-a {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(90px, 70px) scale(1.12); }
}
@keyframes float-b {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-80px, -60px) scale(1.1); }
}
@keyframes float-c {
  0%, 100% { transform: translate(-50%, 0) scale(1); }
  50% { transform: translate(-40%, -50px) scale(1.15); }
}
@keyframes float-d {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(60px, -40px) scale(1.1); }
}
@keyframes card-in {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes logo-drive {
  0% { transform: translateX(-10px); }
  50% { transform: translateX(10px); }
  100% { transform: translateX(-10px); }
}
</style>
