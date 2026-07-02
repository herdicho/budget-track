<template>
  <div class="uploader-overlay" @click.self="$emit('cancel')">
    <div class="glass-panel uploader-card">
      <button @click="$emit('cancel')" class="close-btn" :disabled="loading">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>

      <!-- Standard Upload Step -->
      <div v-if="!loading" class="upload-step">
        <div class="icon-glow">
          <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
        </div>
        
        <h2>Foto Nota Belanja</h2>
        <p class="desc">Unggah foto nota dari galeri atau ambil langsung dengan kamera handphone.</p>

        <div class="action-buttons">
          <!-- Hidden Inputs -->
          <input 
            type="file" 
            ref="fileInput" 
            @change="onFileChange" 
            accept="image/*" 
            class="hidden-input" 
          />
          <input 
            type="file" 
            ref="cameraInput" 
            @change="onFileChange" 
            accept="image/*" 
            capture="environment" 
            class="hidden-input" 
          />

          <!-- Mobile Specific Camera Trigger -->
          <button @click="triggerCamera" class="btn btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="btn-icon"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
            Ambil Foto (Kamera)
          </button>

          <button @click="triggerFile" class="btn btn-secondary">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="btn-icon"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
            Pilih dari Galeri
          </button>
        </div>
      </div>

      <!-- Loading / Gemini Processing Step -->
      <div v-else class="loading-step">
        <div class="loader-animation-container">
          <div class="glow-ring"></div>
          <div class="scanner-line"></div>
          <div class="loader-icon">🤖</div>
        </div>

        <h2>Membaca Nota...</h2>
        
        <div class="status-tracker">
          <div v-for="(step, idx) in statusSteps" :key="idx" class="status-item" :class="getStatusClass(idx)">
            <span class="status-indicator"></span>
            <span class="status-text">{{ step }}</span>
          </div>
        </div>

        <p class="loading-note">Gemini AI sedang membaca rincian harga, toko, dan barang belanjaan Anda.</p>
      </div>

      <Transition name="fade">
        <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>
      </Transition>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'ReceiptUploader',
  props: {
    apiUrl: {
      type: String,
      required: true
    },
    authPassword: {
      type: String,
      required: true
    }
  },
  emits: ['cancel', 'upload-success'],
  setup(props, { emit }) {
    const loading = ref(false)
    const errorMsg = ref('')
    const fileInput = ref(null)
    const cameraInput = ref(null)
    
    // Status Steps Tracker
    const currentStepIndex = ref(0)
    const statusSteps = [
      "Mengunggah gambar nota...",
      "Membaca teks nota (OCR)...",
      "Mengekstrak data transaksi (Gemini AI)...",
      "Membuat form tinjauan..."
    ]
    let timer = null

    const triggerFile = () => {
      errorMsg.value = ''
      fileInput.value.click()
    }

    const triggerCamera = () => {
      errorMsg.value = ''
      cameraInput.value.click()
    }

    const onFileChange = (e) => {
      const files = e.target.files
      if (files && files.length > 0) {
        uploadFile(files[0])
      }
    }

    const startStatusAnimation = () => {
      currentStepIndex.value = 0
      timer = setInterval(() => {
        if (currentStepIndex.value < statusSteps.length - 1) {
          currentStepIndex.value++
        }
      }, 2500) // update status text every 2.5s
    }

    const stopStatusAnimation = () => {
      if (timer) {
        clearInterval(timer)
        timer = null
      }
    }

    onUnmounted(() => {
      stopStatusAnimation()
    })

    const uploadFile = async (file) => {
      loading.value = true
      errorMsg.value = ''
      startStatusAnimation()

      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await fetch(`${props.apiUrl}/api/receipts/process`, {
          method: 'POST',
          headers: {
            'X-App-Password': props.authPassword
          },
          body: formData
        })

        const data = await response.json()

        if (response.ok) {
          emit('upload-success', data)
        } else {
          errorMsg.value = data.detail || 'Gagal memproses gambar nota. Silakan coba lagi.'
          loading.value = false
          stopStatusAnimation()
        }
      } catch (err) {
        errorMsg.value = 'Terjadi kesalahan koneksi saat mengunggah nota.'
        console.error(err)
        loading.value = false
        stopStatusAnimation()
      }
    }

    const getStatusClass = (index) => {
      if (index < currentStepIndex.value) return 'completed'
      if (index === currentStepIndex.value) return 'active'
      return 'pending'
    }

    return {
      loading,
      errorMsg,
      fileInput,
      cameraInput,
      statusSteps,
      triggerFile,
      triggerCamera,
      onFileChange,
      getStatusClass
    }
  }
}
</script>

<style scoped>
.uploader-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(12px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.uploader-card {
  width: 100%;
  max-width: 380px;
  padding: 36px 24px;
  text-align: center;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.close-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.close-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.hidden-input {
  display: none;
}

/* Upload Step */
.icon-glow {
  background: rgba(139, 92, 246, 0.1);
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary-light);
  margin: 0 auto 20px auto;
  border: 1px solid rgba(139, 92, 246, 0.25);
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.15);
}

h2 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 8px;
}

.desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 28px;
  line-height: 1.5;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-icon {
  margin-right: 4px;
}

/* Loading / Gemini step */
.loader-animation-container {
  width: 100px;
  height: 100px;
  margin: 10px auto 24px auto;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.glow-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px dashed var(--color-primary-light);
  opacity: 0.4;
  animation: spinRing 12s linear infinite;
}

@keyframes spinRing {
  100% { transform: rotate(360deg); }
}

.scanner-line {
  position: absolute;
  width: 90%;
  height: 4px;
  background: linear-gradient(90deg, transparent, var(--color-secondary), transparent);
  animation: scanEffect 2s ease-in-out infinite;
  box-shadow: 0 0 8px var(--color-secondary);
}

@keyframes scanEffect {
  0%, 100% { top: 10%; }
  50% { top: 90%; }
}

.loader-icon {
  font-size: 40px;
  z-index: 2;
  filter: drop-shadow(0 0 10px rgba(139, 92, 246, 0.4));
}

.status-tracker {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  max-width: 280px;
  margin: 24px auto;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  display: inline-block;
  transition: all 0.3s ease;
}

.status-item.pending {
  color: var(--text-muted);
}

.status-item.active {
  color: var(--text-primary);
  transform: scale(1.05) translate(4px);
}

.status-item.active .status-indicator {
  background: var(--color-secondary);
  box-shadow: 0 0 8px var(--color-secondary);
  animation: pulseGlow 1s infinite ease-in-out;
}

.status-item.completed {
  color: var(--color-success-light);
}

.status-item.completed .status-indicator {
  background: var(--color-success);
}

.loading-note {
  font-size: 12px;
  color: var(--text-muted);
}

.error-text {
  color: var(--color-danger-light);
  font-size: 13px;
  margin-top: 20px;
  font-weight: 500;
}
</style>
