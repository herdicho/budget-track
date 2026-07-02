<template>
  <div class="transaction-review">
    <div class="glass-panel review-card">
      <h2 class="review-title">{{ isEditMode ? 'Ubah Rincian Transaksi' : 'Tinjau Transaksi' }}</h2>
      <p class="review-subtitle">{{ isEditMode ? 'Sesuaikan data transaksi yang ingin Anda ubah.' : 'Verifikasi dan sesuaikan data nota sebelum disimpan.' }}</p>

      <!-- Optional Receipt Photo Preview Toggle -->
      <div v-if="localTx.receipt_url" class="receipt-preview-section">
        <button type="button" @click="showReceiptPhoto = !showReceiptPhoto" class="btn btn-secondary btn-small">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="btn-icon"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
          {{ showReceiptPhoto ? 'Sembunyikan Foto Nota' : 'Lihat Foto Nota' }}
        </button>
        <Transition name="expand">
          <div v-if="showReceiptPhoto" class="photo-container">
            <img :src="localTx.receipt_url" alt="Foto Nota" class="receipt-img" />
          </div>
        </Transition>
      </div>

      <form @submit.prevent="saveTransaction" class="review-form">
        <!-- Amount (Highlight) -->
        <div class="amount-field-wrapper">
          <label class="form-label text-center">
            {{ localTx.category === 'Transfer' ? 'Jumlah Transfer' : (localTx.category === 'Pendapatan' ? 'Jumlah Pendapatan' : 'Total Belanja') }}
          </label>
          <div class="currency-input-container">
            <span class="currency-prefix">Rp</span>
            <input 
              type="number" 
              v-model="localTx.amount" 
              class="amount-input" 
              required
              min="0"
            />
          </div>
        </div>

        <!-- Merchant / Description -->
        <div class="form-group">
          <label for="merchant" class="form-label">
            {{ localTx.category === 'Transfer' ? 'Keterangan Transfer' : (localTx.category === 'Pendapatan' ? 'Keterangan Pendapatan' : 'Nama Toko / Merchant') }}
          </label>
          <input 
            id="merchant"
            type="text" 
            v-model="localTx.merchant" 
            class="form-input" 
            :placeholder="localTx.category === 'Transfer' ? 'Contoh: Pindah Saldo (opsional)' : (localTx.category === 'Pendapatan' ? 'Contoh: Gaji Bulanan / Bonus' : 'Toko Kelontong / Restoran')"
            :required="localTx.category !== 'Transfer'"
          />
        </div>

        <div class="form-row">
          <!-- Date -->
          <div class="form-group half">
            <label for="date" class="form-label">Tanggal</label>
            <input 
              id="date"
              type="date" 
              v-model="localTx.date" 
              class="form-input" 
              required
            />
          </div>

          <!-- Category -->
          <div class="form-group half">
            <label for="category" class="form-label">Kategori</label>
            <select id="category" v-model="localTx.category" class="form-input select-input" required>
              <option v-for="cat in categories" :key="cat.id || cat.name" :value="cat.name">
                {{ cat.emoji }} {{ cat.name }}
              </option>
            </select>
          </div>
        </div>

        <!-- Payment Source -->
        <div class="form-group">
          <label for="payment_source" class="form-label">
            {{ localTx.category === 'Transfer' ? 'Transfer Dari (Sumber)' : (localTx.category === 'Pendapatan' ? 'Diterima Di (Sumber)' : 'Sumber Dana') }}
          </label>
          <select id="payment_source" v-model="localTx.payment_source" class="form-input select-input" required>
            <option v-for="source in localSources" :key="source.id || source.name" :value="source.name">
              {{ source.name }}
            </option>
          </select>
        </div>

        <!-- Transfer Destination (Only for Transfer Category) -->
        <div v-if="localTx.category === 'Transfer'" class="form-group">
          <label for="transfer_to" class="form-label">Transfer Ke (Tujuan)</label>
          <select id="transfer_to" v-model="localTx.transfer_to" class="form-input select-input" required>
            <option value="" disabled selected>Pilih rekening/e-wallet tujuan...</option>
            <option 
              v-for="source in localSources.filter(s => s.name !== localTx.payment_source)" 
              :key="source.id || source.name" 
              :value="source.name"
            >
              {{ source.name }}
            </option>
          </select>
        </div>

        <!-- Who shopped (User Select) -->
        <div class="form-group">
          <label class="form-label">Siapa yang Belanja?</label>
          <div class="segment-control">
            <button 
              type="button" 
              class="segment-btn" 
              :class="{ active: localTx.user_name === 'Suami' }"
              @click="localTx.user_name = 'Suami'"
            >
              🙋‍♂️ Suami
            </button>
            <button 
              type="button" 
              class="segment-btn" 
              :class="{ active: localTx.user_name === 'Istri' }"
              @click="localTx.user_name = 'Istri'"
            >
              🙋‍♀️ Istri
            </button>
          </div>
        </div>

        <!-- Items Breakdown Details -->
        <div v-if="localTx.items && localTx.items.length > 0" class="items-breakdown">
          <span class="form-label">Rincian Barang</span>
          <div class="items-list">
            <div v-for="(item, idx) in localTx.items" :key="idx" class="item-row">
              <span class="item-name">{{ item.name }} (x{{ item.quantity }})</span>
              <span class="item-price">{{ formatCurrency(item.price) }}</span>
            </div>
          </div>
        </div>

        <div class="action-buttons">
          <button type="submit" class="btn btn-primary" :disabled="saving">
            <span v-if="saving" class="spinner"></span>
            <span v-else>{{ isEditMode ? 'Simpan Perubahan' : 'Simpan Transaksi' }}</span>
          </button>
          <button type="button" @click="$emit('cancel')" class="btn btn-secondary" :disabled="saving">
            Batal
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, reactive, watch, computed } from 'vue'

export default {
  name: 'TransactionReview',
  props: {
    apiUrl: {
      type: String,
      required: true
    },
    authPassword: {
      type: String,
      required: true
    },
    extractedData: {
      type: Object,
      required: true
    },
    paymentSources: {
      type: Array,
      required: true
    },
    categories: {
      type: Array,
      required: true
    }
  },
  emits: ['cancel', 'save-success'],
  setup(props, { emit }) {
    const localTx = reactive({
      merchant: props.extractedData?.merchant || '',
      date: props.extractedData?.date || new Date().toISOString().substring(0, 10),
      category: props.extractedData?.category || 'Lain-lain',
      payment_source: props.extractedData?.payment_source || 'Cash',
      amount: props.extractedData?.amount || 0.0,
      user_name: props.extractedData?.user_name || 'Suami',
      items: props.extractedData?.items || [],
      receipt_url: props.extractedData?.receipt_url || '',
      transfer_to: props.extractedData?.transfer_to || ''
    })

    // categories is received dynamically as a prop

    const localSources = ref([...props.paymentSources])

    const saving = ref(false)
    const showReceiptPhoto = ref(false)

    // Normalize payment source from Gemini's prediction or defaults
    if (localTx.payment_source) {
      const matched = localSources.value.find(
        s => s.name.toLowerCase() === localTx.payment_source.toLowerCase()
      )
      if (matched) {
        localTx.payment_source = matched.name
      } else {
        localSources.value.unshift({
          name: localTx.payment_source,
          type: 'bank'
        })
      }
    } else {
      localTx.payment_source = localSources.value.length > 0 ? localSources.value[0].name : 'Cash'
    }

    const formatCurrency = (val) => {
      return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        maximumFractionDigits: 0
      }).format(val || 0)
    }

    // Watch payment source to reset transfer_to if they clash
    watch(() => localTx.payment_source, (newVal) => {
      if (localTx.category === 'Transfer' && localTx.transfer_to === newVal) {
        localTx.transfer_to = ''
      }
    })

    const isEditMode = computed(() => !!(props.extractedData && props.extractedData.id))

    const saveTransaction = async () => {
      saving.value = true
      try {
        // Prepare payload copy to normalize values
        const payload = { ...localTx }
        if (payload.category === 'Transfer') {
          const oldDest = props.extractedData?.transfer_to || ''
          const defaultOldMerchant = `Pindah Dana ke ${oldDest}`
          if (!payload.merchant || payload.merchant === defaultOldMerchant) {
            payload.merchant = `Pindah Dana ke ${payload.transfer_to}`
          }
        } else {
          payload.transfer_to = null
        }

        const url = isEditMode.value
          ? `${props.apiUrl}/api/transactions/${props.extractedData.id}`
          : `${props.apiUrl}/api/transactions`
        const method = isEditMode.value ? 'PUT' : 'POST'

        const response = await fetch(url, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'X-App-Password': props.authPassword
          },
          body: JSON.stringify(payload)
        })

        if (response.ok) {
          emit('save-success')
        } else {
          alert('Gagal menyimpan transaksi. Coba lagi.')
        }
      } catch (err) {
        console.error("Error saving transaction:", err)
        alert('Kesalahan koneksi ke server backend.')
      } finally {
        saving.value = false
      }
    }

    return {
      localTx,
      localSources,
      saving,
      showReceiptPhoto,
      formatCurrency,
      saveTransaction,
      isEditMode
    }
  }
}
</script>

<style scoped>
.transaction-review {
  width: 100%;
  padding: 24px 16px;
}

.review-card {
  padding: 24px 20px;
}

.review-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 6px;
  text-align: center;
}

.review-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 24px;
}

/* Photo preview styling */
.receipt-preview-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  margin-bottom: 24px;
}

.btn-small {
  padding: 8px 16px;
  font-size: 13px;
  border-radius: 10px;
  width: auto;
}

.photo-container {
  margin-top: 14px;
  width: 100%;
  max-height: 250px;
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid var(--glass-border);
}

.receipt-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: black;
}

/* Amount Highlighting Input */
.amount-field-wrapper {
  margin-bottom: 24px;
  text-align: center;
}

.currency-input-container {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-bottom: 2px dashed rgba(139, 92, 246, 0.4);
  padding: 4px 8px;
  margin-top: 8px;
}

.currency-prefix {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-primary-light);
  margin-right: 6px;
}

.amount-input {
  background: transparent;
  border: none;
  font-family: inherit;
  font-size: 32px;
  font-weight: 800;
  color: var(--text-primary);
  outline: none;
  width: 180px;
  text-align: center;
}

/* Form row structure */
.form-row {
  display: flex;
  gap: 16px;
}

.half {
  flex: 1;
  min-width: 0; /* Prevents overflow in flex child */
}

.select-input {
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 14px center;
  background-size: 16px;
  padding-right: 40px;
}

/* Items breakdown list */
.items-breakdown {
  margin-top: 10px;
  margin-bottom: 24px;
}

.items-list {
  background: rgba(0, 0, 0, 0.15);
  border: 1px solid var(--glass-border);
  border-radius: 14px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.item-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 500;
}

.item-name {
  color: var(--text-primary);
  text-align: left;
}

.item-price {
  color: var(--text-secondary);
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 24px;
}

/* Expand transition animation */
.expand-enter-active, .expand-leave-active {
  transition: all 0.3s ease-out;
  max-height: 250px;
}
.expand-enter-from, .expand-leave-to {
  max-height: 0;
  opacity: 0;
}

/* Segment controls */
.segment-control {
  display: flex;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--glass-border);
  border-radius: 14px;
  padding: 4px;
  width: 100%;
}

.segment-btn {
  flex: 1;
  padding: 10px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.segment-btn.active {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  color: white;
  box-shadow: 0 4px 10px rgba(139, 92, 246, 0.2);
}
</style>
