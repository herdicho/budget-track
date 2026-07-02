<template>
  <div class="login-container">
    <div class="glass-panel login-card">
      <div class="logo-area">
        <div class="heart-icon">❤️</div>
        <h1>BukuKas Kita</h1>
        <p class="tagline">Pelacak anggaran bulanan suami & istri</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="password" class="form-label text-center">Masukkan Sandi Akses</label>
          <div class="input-wrapper">
            <input 
              id="password"
              type="password" 
              v-model="password" 
              class="form-input text-center" 
              placeholder="••••"
              autocomplete="current-password"
              ref="passwordInput"
              required
            />
          </div>
        </div>

        <button type="submit" class="btn btn-primary" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>Masuk</span>
        </button>

        <Transition name="fade">
          <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>
        </Transition>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'Login',
  props: {
    apiUrl: {
      type: String,
      required: true
    }
  },
  emits: ['login-success'],
  setup(props, { emit }) {
    const password = ref('')
    const loading = ref(false)
    const errorMsg = ref('')
    const passwordInput = ref(null)

    onMounted(() => {
      if (passwordInput.value) {
        passwordInput.value.focus()
      }
    })

    const handleLogin = async () => {
      if (!password.value) return
      
      loading.value = true
      errorMsg.value = ''
      
      try {
        const response = await fetch(`${props.apiUrl}/api/auth/verify`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ password: password.value })
        })

        const data = await response.json()

        if (response.ok) {
          // Store in localStorage
          localStorage.setItem('app_password', password.value)
          emit('login-success', password.value)
        } else {
          errorMsg.value = data.detail || 'Sandi salah. Coba lagi!'
          password.value = ''
          if (passwordInput.value) passwordInput.value.focus()
        }
      } catch (err) {
        errorMsg.value = 'Gagal terhubung ke server backend.'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    return {
      password,
      loading,
      errorMsg,
      passwordInput,
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  width: 100%;
}

.login-card {
  width: 100%;
  max-width: 360px;
  padding: 40px 30px;
  text-align: center;
}

.logo-area {
  margin-bottom: 35px;
}

.heart-icon {
  font-size: 40px;
  margin-bottom: 12px;
  filter: drop-shadow(0 0 10px rgba(217, 70, 239, 0.4));
  animation: heartBeat 2s infinite ease-in-out;
}

@keyframes heartBeat {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.12); }
}

h1 {
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--text-primary) 30%, var(--color-primary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 6px;
  letter-spacing: -0.5px;
}

.tagline {
  font-size: 13px;
  color: var(--text-secondary);
}

.text-center {
  text-align: center;
}

.input-wrapper {
  margin-top: 10px;
}

.form-input.text-center {
  font-size: 24px;
  letter-spacing: 6px;
  height: 56px;
}

.error-text {
  color: var(--color-danger-light);
  font-size: 13px;
  margin-top: 15px;
  font-weight: 500;
}

.btn {
  margin-top: 10px;
  height: 50px;
}
</style>
