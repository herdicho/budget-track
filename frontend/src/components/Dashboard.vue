<template>
  <div class="dashboard">
    <!-- Header with Month Selector & Logout -->
    <header class="dashboard-header glass-panel">
      <div class="header-top">
        <span class="user-greeting">Halo, Bersama ❤️</span>
        <div style="display: flex; gap: 8px; align-items: center;">
          <button @click="$emit('trigger-report')" class="report-link-btn" style="background: rgba(255, 255, 255, 0.08); border: 1px solid var(--glass-border); padding: 6px 12px; border-radius: 10px; font-size: 11px; font-weight: 600; color: var(--text-primary); cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s ease;">
            📊 Laporan Bulanan
          </button>
          <button @click="$emit('logout')" class="logout-btn" title="Keluar">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
          </button>
        </div>
      </div>
      <div class="month-selector">
        <button @click="changeMonth(-1)" class="month-nav-btn">&larr;</button>
        <h2 class="current-month-label">{{ formatMonthLabel(currentMonth) }}</h2>
        <button @click="changeMonth(1)" class="month-nav-btn">&rarr;</button>
      </div>
    </header>

    <!-- Main Budget Progress Card -->
    <section class="budget-card glass-panel">
      <div class="budget-header">
        <div style="display: flex; gap: 32px; flex-wrap: wrap;">
          <div>
            <span class="section-subtitle">Sisa Anggaran Belanja</span>
            <h1 class="remaining-value" :class="{ 'warning-text': remainingPercent < 20, 'danger-text': remainingPercent <= 0 }">
              {{ formatCurrency(summary.remaining) }}
            </h1>
          </div>
          <div>
            <span class="section-subtitle">Sisa Uang (Net)</span>
            <h1 class="remaining-value" :class="{ 'danger-text': summary.net_balance <= 0 }">
              {{ formatCurrency(summary.net_balance) }}
            </h1>
          </div>
        </div>
        <button @click="openBudgetEdit" class="edit-budget-btn" title="Edit Anggaran & Pendapatan">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="16 3 21 8 8 21 3 21 3 16 16 3"></polygon></svg>
        </button>
      </div>

      <div class="progress-bar-wrapper">
        <div class="progress-bar-track">
          <div 
            class="progress-bar-fill" 
            :style="{ width: `${Math.min(spentPercent, 100)}%` }"
            :class="{ 'warning-bg': spentPercent >= 80, 'danger-bg': spentPercent >= 100 }"
          ></div>
        </div>
        <div class="progress-labels">
          <span>Terpakai: {{ spentPercent.toFixed(0) }}%</span>
          <span>Sisa: {{ Math.max(remainingPercent, 0).toFixed(0) }}%</span>
        </div>
      </div>

      <div class="budget-grid">
        <div class="budget-grid-item">
          <span class="grid-item-label">Batas Anggaran</span>
          <span class="grid-item-val font-primary">{{ formatCurrency(summary.budget) }}</span>
        </div>
        <div class="budget-grid-item">
          <span class="grid-item-label">Total Pendapatan</span>
          <span class="grid-item-val font-success">{{ formatCurrency(summary.income) }}</span>
        </div>
        <div class="budget-grid-item text-right">
          <span class="grid-item-label">Total Terpakai</span>
          <span class="grid-item-val font-danger">{{ formatCurrency(summary.total_spent) }}</span>
        </div>
      </div>
    </section>

    <!-- Upload Receipt Quick Action -->
    <section class="upload-promo-card glass-panel" @click="$emit('trigger-upload')">
      <div class="promo-content">
        <div class="promo-icon-box">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
        </div>
        <div class="promo-text">
          <h3>Scan Nota Belanja</h3>
          <p>Foto nota untuk deteksi otomatis oleh Gemini AI</p>
        </div>
      </div>
      <div class="promo-arrow">&rarr;</div>
    </section>

    <!-- Add Manual Transaction Quick Action -->
    <section class="upload-promo-card manual-promo-card glass-panel" @click="triggerManualAdd" style="margin-top: 16px;">
      <div class="promo-content">
        <div class="promo-icon-box manual-icon-box">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </div>
        <div class="promo-text">
          <h3>Tambah Transaksi Manual</h3>
          <p>Catat pengeluaran atau transfer secara manual</p>
        </div>
      </div>
      <div class="promo-arrow">&rarr;</div>
    </section>

    <!-- Account Balances Card -->
    <section v-if="summary.balances && Object.keys(summary.balances).length > 0" class="sources-card glass-panel" style="margin-top: 16px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <h3 class="section-title" style="margin-bottom: 0;">Saldo Sumber Dana</h3>
        <button @click="showAddSourceForm = !showAddSourceForm" class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px; width: auto; height: auto; min-height: unset; margin: 0;">
          {{ showAddSourceForm ? 'Batal' : '+ Tambah' }}
        </button>
      </div>
      <p class="section-subtitle" style="font-size: 11px; color: var(--text-muted); margin-bottom: 12px; margin-top: -4px;">
        Dana tersedia saat ini di masing-masing tempat penyimpanan.
      </p>

      <!-- Inline Add Source Form -->
      <div v-if="showAddSourceForm" style="border: 1px solid var(--glass-border); background: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 12px; margin-bottom: 16px;">
        <form @submit.prevent="addNewSource" style="display: flex; flex-direction: column; gap: 8px;">
          <div class="form-group" style="margin-bottom: 0;">
            <input 
              type="text" 
              v-model="newSourceName" 
              class="form-input" 
              placeholder="Nama (misal: SeaBank, OVO)" 
              required
              style="text-align: left; padding: 8px 12px; font-size: 13px;"
            />
          </div>
          <div class="form-group" style="margin-bottom: 0;">
            <select v-model="newSourceType" class="form-input select-input" style="text-align: left; background-position: right 12px center; padding: 8px 12px; font-size: 13px;">
              <option value="bank">Bank (🏦)</option>
              <option value="ewallet">E-Wallet (📱)</option>
              <option value="cash">Tunai (💵)</option>
            </select>
          </div>
          <button 
            type="submit" 
            class="btn btn-primary btn-small"
            :disabled="addingSource || !newSourceName"
            style="align-self: flex-end; padding: 6px 12px; font-size: 12px;"
          >
            <span v-if="addingSource" class="spinner"></span>
            <span v-else>Simpan</span>
          </button>
        </form>
      </div>
      <div class="sources-list">
        <div v-for="(balance, name) in summary.balances" :key="name" class="source-item">
          <div class="source-info">
            <span class="source-icon">{{ getSourceIcon(name) }}</span>
            <span class="source-name">{{ name }}</span>
          </div>
          <span class="source-amount" :class="{ 'danger-text': balance < 0 }">
            {{ formatCurrency(balance) }}
          </span>
        </div>
      </div>
    </section>

    <!-- Payment Source Accounts Breakdown -->
    <section v-if="hasSources" class="sources-card glass-panel">
      <h3 class="section-title">Sumber Dana Terpakai</h3>
      <div class="sources-list">
        <div v-for="(amount, name) in summary.sources" :key="name" class="source-item">
          <div class="source-info">
            <span class="source-icon">{{ getSourceIcon(name) }}</span>
            <span class="source-name">{{ name }}</span>
          </div>
          <span class="source-amount">{{ formatCurrency(amount) }}</span>
        </div>
      </div>
    </section>

    <!-- User Spending Breakdown (Suami vs Istri) -->
    <section class="users-card glass-panel" v-if="summary.users">
      <h3 class="section-title">Pembagian Pengeluaran</h3>
      <div class="users-split-container">
        <!-- Suami progress -->
        <div class="user-split-item">
          <div class="user-split-label">
            <span class="user-split-name">🙋‍♂️ Suami</span>
            <span class="user-split-amount">{{ formatCurrency(summary.users.Suami || 0) }} ({{ getUserPercent('Suami') }}%)</span>
          </div>
          <div class="user-split-track">
            <div class="user-split-fill suami" :style="{ width: `${getUserPercent('Suami')}%` }"></div>
          </div>
        </div>

        <!-- Istri progress -->
        <div class="user-split-item">
          <div class="user-split-label">
            <span class="user-split-name">🙋‍♀️ Istri</span>
            <span class="user-split-amount">{{ formatCurrency(summary.users.Istri || 0) }} ({{ getUserPercent('Istri') }}%)</span>
          </div>
          <div class="user-split-track">
            <div class="user-split-fill istri" :style="{ width: `${getUserPercent('Istri')}%` }"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- Categories Breakdown -->
    <section class="categories-card glass-panel">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <h3 class="section-title" style="margin-bottom: 0;">Pengeluaran per Kategori</h3>
        <button @click="showAddCategoryForm = !showAddCategoryForm" class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px; width: auto; height: auto; min-height: unset; margin: 0;">
          {{ showAddCategoryForm ? 'Batal' : '+ Kategori' }}
        </button>
      </div>

      <!-- Inline Add Category Form -->
      <div v-if="showAddCategoryForm" style="border: 1px solid var(--glass-border); background: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 12px; margin-bottom: 16px; margin-top: 8px;">
        <form @submit.prevent="addNewCategory" style="display: flex; flex-direction: column; gap: 8px;">
          <div class="form-group" style="margin-bottom: 0;">
            <input 
              type="text" 
              v-model="newCategoryName" 
              class="form-input" 
              placeholder="Nama Kategori (misal: Kesehatan)" 
              required
              style="text-align: left; padding: 8px 12px; font-size: 13px;"
            />
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <div class="form-group" style="margin-bottom: 0; flex: 1;">
              <input 
                type="text" 
                v-model="newCategoryEmoji" 
                class="form-input text-center" 
                placeholder="Emoji (misal: 🏥)" 
                required
                style="padding: 8px 12px; font-size: 13px;"
              />
            </div>
            <div class="form-group" style="margin-bottom: 0; flex: 1; display: flex; align-items: center; gap: 8px;">
              <label style="font-size: 11px; color: var(--text-muted);">Warna:</label>
              <input 
                type="color" 
                v-model="newCategoryColor" 
                style="width: 38px; height: 38px; border-radius: 8px; border: 1px solid var(--glass-border); background: transparent; cursor: pointer; padding: 0;"
              />
            </div>
          </div>
          <button 
            type="submit" 
            class="btn btn-primary btn-small"
            :disabled="addingCategory || !newCategoryName"
            style="align-self: flex-end; padding: 6px 12px; font-size: 12px;"
          >
            <span v-if="addingCategory" class="spinner"></span>
            <span v-else>Simpan</span>
          </button>
        </form>
      </div>
      
      <div v-if="!hasCategories" class="empty-state">
        Belum ada transaksi di bulan ini.
      </div>
      
      <div v-else class="categories-list">
        <div v-for="(amount, cat) in summary.categories" :key="cat" class="category-item">
          <div class="category-info">
            <span class="category-name-wrapper">
              <span class="category-bullet" :style="{ backgroundColor: getCategoryColor(cat) }"></span>
              {{ cat }}
            </span>
            <span class="category-amount">{{ formatCurrency(amount) }} ({{ getCategoryPercent(amount) }}%)</span>
          </div>
          <div class="category-progress-track">
            <div 
              class="category-progress-fill" 
              :style="{ width: `${getCategoryPercent(amount)}%`, backgroundColor: getCategoryColor(cat) }"
            ></div>
          </div>
        </div>
      </div>
    </section>

    <!-- Recent Transactions List -->
    <section class="transactions-card glass-panel">
      <div class="section-header">
        <h3 class="section-title">Riwayat Transaksi</h3>
        <button 
          v-if="summary.recent_transactions && summary.recent_transactions.length > 0" 
          @click="$emit('view-all')" 
          class="text-link-btn"
        >
          Lihat Semua
        </button>
      </div>

      <div v-if="!summary.recent_transactions || summary.recent_transactions.length === 0" class="empty-state">
        Tidak ada transaksi terbaru.
      </div>

      <div v-else class="transactions-list">
        <div v-for="tx in summary.recent_transactions" :key="tx.id" class="tx-item">
          <div class="tx-left">
            <div class="tx-category-icon" :style="{ background: getCategoryColor(tx.category) + '22', color: getCategoryColor(tx.category) }">
              {{ getCategoryEmoji(tx.category) }}
            </div>
            <div class="tx-details">
              <span class="tx-merchant">
                {{ tx.merchant }}
                <span class="tx-user-badge" :class="tx.user_name?.toLowerCase() === 'istri' ? 'istri-badge' : 'suami-badge'">
                  {{ tx.user_name === 'Istri' ? 'I' : 'S' }}
                </span>
              </span>
              <span class="tx-meta">{{ formatDateShort(tx.date) }} &bull; {{ tx.payment_source }}</span>
            </div>
          </div>
          <div class="tx-right">
            <span class="tx-amount">{{ formatCurrency(tx.amount) }}</span>
            <button @click="$emit('trigger-edit', tx)" class="edit-tx-btn" title="Ubah" style="background: transparent; border: none; color: #8be9fd; cursor: pointer; padding: 4px; margin-right: 8px; transition: all 0.2s ease; display: inline-flex; align-items: center; justify-content: center;">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="16 3 21 8 8 21 3 21 3 16 16 3"></polygon></svg>
            </button>
            <button @click="deleteTransaction(tx.id)" class="delete-tx-btn" title="Hapus">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Inline Budget Edit Modal -->
    <div v-if="editingBudget" class="modal-overlay" @click.self="editingBudget = false">
      <div class="modal-content glass-panel">
        <h3>Atur Keuangan Bulan Ini</h3>
        <p class="modal-desc">Tentukan batas anggaran belanja untuk bulan {{ formatMonthLabel(currentMonth) }}</p>
        
        <form @submit.prevent="saveBudget" class="budget-form">
          <div class="form-group" style="margin-bottom: 20px;">
            <label class="form-label" style="text-align: left; display: block; margin-bottom: 6px;">Batas Anggaran Belanja (Rp)</label>
            <input 
              type="number" 
              v-model="newBudgetAmount" 
              class="form-input text-center budget-input" 
              placeholder="Batas Anggaran (Rp)"
              required
              min="0"
              ref="budgetInputRef"
            />
          </div>


          <div class="modal-actions" style="margin-top: 20px;">
            <button type="button" @click="editingBudget = false" class="btn btn-secondary">Batal</button>
            <button type="submit" class="btn btn-primary" :disabled="savingBudget">Simpan</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, nextTick } from 'vue'

export default {
  name: 'Dashboard',
  props: {
    apiUrl: {
      type: String,
      required: true
    },
    authPassword: {
      type: String,
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
  emits: ['logout', 'trigger-upload', 'trigger-manual', 'trigger-report', 'trigger-edit', 'refresh-sources', 'refresh-categories', 'view-all'],
  setup(props, { emit }) {
    const currentMonth = ref(new Date().toISOString().substring(0, 7)) // Format: YYYY-MM
    const summary = ref({
      month: currentMonth.value,
      budget: 0.0,
      income: 0.0,
      total_spent: 0.0,
      remaining: 0.0,
      net_balance: 0.0,
      categories: {},
      sources: {},
      balances: {},
      recent_transactions: []
    })
    
    const editingBudget = ref(false)
    const newBudgetAmount = ref(0)
    const newIncomeAmount = ref(0)
    const savingBudget = ref(false)
    const budgetInputRef = ref(null)

    // Percentage Computations
    const spentPercent = computed(() => {
      if (summary.value.budget <= 0) return 0
      return (summary.value.total_spent / summary.value.budget) * 100
    })

    const remainingPercent = computed(() => {
      if (summary.value.budget <= 0) return 100
      return Math.max(0, (summary.value.remaining / summary.value.budget) * 100)
    })

    const hasCategories = computed(() => {
      return summary.value.categories && Object.keys(summary.value.categories).length > 0
    })

    const hasSources = computed(() => {
      return summary.value.sources && Object.keys(summary.value.sources).length > 0
    })

    const fetchSummary = async () => {
      try {
        const response = await fetch(`${props.apiUrl}/api/dashboard/summary?month=${currentMonth.value}`, {
          headers: {
            'X-App-Password': props.authPassword
          }
        })
        if (response.ok) {
          summary.value = await response.json()
        }
      } catch (err) {
        console.error("Failed to fetch summary:", err)
      }
    }

    onMounted(() => {
      fetchSummary()
    })

    watch(currentMonth, () => {
      fetchSummary()
    })

    // Navigation and Helpers
    const changeMonth = (offset) => {
      const [year, month] = currentMonth.value.split('-').map(Number)
      const d = new Date(Date.UTC(year, month - 1 + offset, 1))
      currentMonth.value = d.toISOString().substring(0, 7)
    }

    const formatMonthLabel = (monthStr) => {
      const [year, month] = monthStr.split('-')
      const monthNames = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
      ]
      return `${monthNames[parseInt(month) - 1]} ${year}`
    }

    const formatCurrency = (val) => {
      return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        maximumFractionDigits: 0
      }).format(val || 0)
    }

    const formatDateShort = (dateStr) => {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
    }

    const getCategoryPercent = (amount) => {
      if (summary.value.total_spent <= 0) return 0
      return Math.round((amount / summary.value.total_spent) * 100)
    }

    const getCategoryColor = (catName) => {
      if (!catName) return '#ff5555'
      const cat = props.categories.find(c => c.name && c.name.toLowerCase() === catName.toLowerCase())
      if (cat && cat.color) return cat.color
      const colors = {
        'Makanan': '#ff79c6',       // Pink
        'Transportasi': '#8be9fd',  // Cyan
        'Kebutuhan Bulanan': '#50fa7b', // Green
        'Kebutuhan Bayi': '#ffb86c', // Orange
        'Hiburan': '#bd93f9',        // Purple
        'Transfer': '#0ea5e9',
        'Pendapatan': '#50fa7b',
        'Lain-lain': '#ff5555'       // Red
      }
      return colors[catName] || '#ffd166'
    }

    const getCategoryEmoji = (catName) => {
      if (!catName) return '📦'
      const cat = props.categories.find(c => c.name && c.name.toLowerCase() === catName.toLowerCase())
      if (cat && cat.emoji) return cat.emoji
      const emojis = {
        'Makanan': '🍔',
        'Transportasi': '🚗',
        'Kebutuhan Bulanan': '🛒',
        'Kebutuhan Bayi': '👶',
        'Hiburan': '🎬',
        'Transfer': '🔄',
        'Pendapatan': '💰',
        'Lain-lain': '📦'
      }
      return emojis[catName] || '💰'
    }

    const getSourceIcon = (sourceName) => {
      const source = props.paymentSources.find(s => s.name.toLowerCase() === sourceName.toLowerCase())
      if (source) {
        if (source.type === 'bank') return '🏦'
        if (source.type === 'ewallet') return '📱'
        if (source.type === 'cash') return '💵'
      }
      const s = sourceName.toLowerCase()
      if (s.includes('cash') || s.includes('tunai')) return '💵'
      if (s.includes('bca') || s.includes('bank') || s.includes('mandiri')) return '🏦'
      if (s.includes('gopay') || s.includes('ovo') || s.includes('shopee') || s.includes('dana') || s.includes('wallet')) return '📱'
      return '💳'
    }

    // Budget Editor
    const openBudgetEdit = () => {
      newBudgetAmount.value = summary.value.budget
      newIncomeAmount.value = summary.value.income || 0
      editingBudget.value = true
      nextTick(() => {
        if (budgetInputRef.value) budgetInputRef.value.focus()
      })
    }

    const saveBudget = async () => {
      savingBudget.value = true
      try {
        const response = await fetch(`${props.apiUrl}/api/budget`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-App-Password': props.authPassword
          },
          body: JSON.stringify({
            month: currentMonth.value,
            amount: parseFloat(newBudgetAmount.value),
            income: parseFloat(newIncomeAmount.value)
          })
        })
        if (response.ok) {
          await fetchSummary()
          editingBudget.value = false
        }
      } catch (err) {
        console.error("Error setting budget:", err)
      } finally {
        savingBudget.value = false
      }
    }

    const triggerManualAdd = () => {
      emit('trigger-manual')
    }

    // Delete transaction
    const deleteTransaction = async (id) => {
      if (!confirm("Hapus transaksi ini?")) return
      
      try {
        const response = await fetch(`${props.apiUrl}/api/transactions/${id}`, {
          method: 'DELETE',
          headers: {
            'X-App-Password': props.authPassword
          }
        })
        if (response.ok) {
          fetchSummary()
        }
      } catch (err) {
        console.error("Error deleting transaction:", err)
      }
    }

    const getUserPercent = (user) => {
      const total = summary.value.total_spent || 0
      if (total <= 0) return 0
      const userSpent = summary.value.users ? (summary.value.users[user] || 0) : 0
      return Math.round((userSpent / total) * 100)
    }

    const newSourceName = ref('')
    const newSourceType = ref('bank')
    const addingSource = ref(false)
    const showAddSourceForm = ref(false)

    const addNewSource = async () => {
      if (!newSourceName.value) return
      addingSource.value = true
      try {
        const response = await fetch(`${props.apiUrl}/api/payment-sources`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-App-Password': props.authPassword
          },
          body: JSON.stringify({
            name: newSourceName.value,
            type: newSourceType.value
          })
        })
        if (response.ok) {
          newSourceName.value = ''
          newSourceType.value = 'bank'
          showAddSourceForm.value = false
          emit('refresh-sources')
          await fetchSummary()
        } else {
          const errData = await response.json()
          alert(errData.detail || 'Gagal menambahkan sumber dana')
        }
      } catch (err) {
        console.error("Error adding source:", err)
        alert('Gagal menghubungi server')
      } finally {
        addingSource.value = false
      }
    }

    const showAddCategoryForm = ref(false)
    const newCategoryName = ref('')
    const newCategoryEmoji = ref('📦')
    const newCategoryColor = ref('#ff5555')
    const addingCategory = ref(false)

    const addNewCategory = async () => {
      if (!newCategoryName.value) return
      addingCategory.value = true
      try {
        const response = await fetch(`${props.apiUrl}/api/categories`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-App-Password': props.authPassword
          },
          body: JSON.stringify({
            name: newCategoryName.value,
            emoji: newCategoryEmoji.value,
            color: newCategoryColor.value
          })
        })
        if (response.ok) {
          newCategoryName.value = ''
          newCategoryEmoji.value = '📦'
          newCategoryColor.value = '#ff5555'
          showAddCategoryForm.value = false
          emit('refresh-categories')
          await fetchSummary()
        } else {
          const errData = await response.json()
          alert(errData.detail || 'Gagal menambahkan kategori')
        }
      } catch (err) {
        console.error("Error adding category:", err)
        alert('Gagal menghubungi server')
      } finally {
        addingCategory.value = false
      }
    }

    return {
      currentMonth,
      summary,
      spentPercent,
      remainingPercent,
      hasCategories,
      hasSources,
      editingBudget,
      newBudgetAmount,
      newIncomeAmount,
      savingBudget,
      budgetInputRef,
      changeMonth,
      formatMonthLabel,
      formatCurrency,
      formatDateShort,
      getCategoryPercent,
      getUserPercent,
      getCategoryColor,
      getCategoryEmoji,
      getSourceIcon,
      openBudgetEdit,
      saveBudget,
      triggerManualAdd,
      deleteTransaction,
      fetchSummary,
      newSourceName,
      newSourceType,
      addingSource,
      addNewSource,
      showAddSourceForm,
      showAddCategoryForm,
      newCategoryName,
      newCategoryEmoji,
      newCategoryColor,
      addingCategory,
      addNewCategory
    }
  }
}
</script>

<style scoped>
.dashboard {
  width: 100%;
  padding: 24px 16px 80px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Header styling */
.dashboard-header {
  padding: 16px 20px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.user-greeting {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.logout-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 4px;
  transition: color 0.2s ease;
}

.logout-btn:hover {
  color: var(--color-danger-light);
}

.month-selector {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.month-nav-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  width: 32px;
  height: 32px;
  border-radius: 10px;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.month-nav-btn:active {
  background: rgba(255, 255, 255, 0.12);
  transform: scale(0.9);
}

.current-month-label {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

/* Budget Card Styling */
.budget-card {
  padding: 24px 20px;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.section-subtitle {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--text-secondary);
  font-weight: 600;
}

.remaining-value {
  font-size: 30px;
  font-weight: 800;
  margin-top: 4px;
  color: var(--color-success-light);
  letter-spacing: -0.5px;
}

.warning-text {
  color: var(--color-warning-light);
}

.danger-text {
  color: var(--color-danger-light);
}

.edit-budget-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--glass-border);
  color: var(--text-secondary);
  width: 34px;
  height: 34px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.edit-budget-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.1);
}

.progress-bar-wrapper {
  margin-bottom: 20px;
}

.progress-bar-track {
  width: 100%;
  height: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 8px;
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border-radius: 5px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.warning-bg {
  background: linear-gradient(90deg, var(--color-warning) 0%, var(--color-warning-light) 100%);
}

.danger-bg {
  background: linear-gradient(90deg, var(--color-danger) 0%, var(--color-danger-light) 100%);
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.budget-grid {
  display: flex;
  justify-content: space-between;
  border-top: 1px solid var(--glass-border);
  padding-top: 16px;
}

.budget-grid-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.text-right {
  text-align: right;
}

.grid-item-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
}

.grid-item-val {
  font-size: 15px;
  font-weight: 600;
}

.font-primary {
  color: var(--text-primary);
}

.font-danger {
  color: var(--color-danger-light);
}

.font-success {
  color: var(--color-success-light);
}

.manual-promo-card {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(6, 182, 212, 0.03) 100%) !important;
  border-color: rgba(14, 165, 233, 0.2) !important;
}

.manual-promo-card:hover {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(6, 182, 212, 0.06) 100%) !important;
  border-color: rgba(14, 165, 233, 0.35) !important;
}

.manual-icon-box {
  background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%) !important;
}

/* Scan Nota Promo Card */
.upload-promo-card {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(217, 70, 239, 0.03) 100%);
  border-color: rgba(139, 92, 246, 0.2);
}

.upload-promo-card:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(217, 70, 239, 0.06) 100%);
  border-color: rgba(139, 92, 246, 0.35);
  transform: translateY(-2px);
}

.upload-promo-card:active {
  transform: translateY(0);
}

.promo-content {
  display: flex;
  gap: 16px;
  align-items: center;
}

.promo-icon-box {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.promo-text h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.promo-text p {
  font-size: 12px;
  color: var(--text-secondary);
}

.promo-arrow {
  color: var(--text-secondary);
  font-size: 18px;
  font-weight: 700;
}

/* Payment Sources */
.sources-card {
  padding: 20px;
}

.section-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 16px;
  letter-spacing: -0.2px;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.source-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.source-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.source-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.source-icon {
  font-size: 18px;
}

.source-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.source-amount {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

/* Categories Styling */
.categories-card {
  padding: 20px;
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.category-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 500;
}

.category-name-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
}

.category-bullet {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.category-amount {
  color: var(--text-secondary);
}

.category-progress-track {
  width: 100%;
  height: 6px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.category-progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}

.empty-state {
  text-align: center;
  padding: 24px;
  font-size: 13px;
  color: var(--text-muted);
}

/* Recent Transactions */
.transactions-card {
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.text-link-btn {
  background: transparent;
  border: none;
  color: var(--color-primary-light);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px;
}

.transactions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tx-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.tx-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.tx-left {
  display: flex;
  gap: 14px;
  align-items: center;
}

.tx-category-icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
}

.tx-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tx-merchant {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.tx-meta {
  font-size: 12px;
  color: var(--text-muted);
}

.tx-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tx-amount {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.delete-tx-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.delete-tx-btn:hover {
  color: var(--color-danger-light);
  background: rgba(244, 63, 94, 0.08);
}

/* Modals */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-content {
  width: 100%;
  max-width: 360px;
  padding: 24px;
  text-align: center;
}

.modal-content h3 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 6px;
}

.modal-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.budget-input {
  font-size: 20px;
  font-weight: 700;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.modal-actions .btn {
  flex: 1;
}

/* User Spending Splits styles */
.users-card {
  padding: 20px;
}

.users-split-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.user-split-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.user-split-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 500;
}

.user-split-name {
  color: var(--text-primary);
}

.user-split-amount {
  color: var(--text-secondary);
}

.user-split-track {
  width: 100%;
  height: 8px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.user-split-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.user-split-fill.suami {
  background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.3);
}

.user-split-fill.istri {
  background: linear-gradient(90deg, #ec4899 0%, #f472b6 100%);
  box-shadow: 0 0 8px rgba(236, 72, 153, 0.3);
}

.tx-user-badge {
  font-size: 9px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 6px;
  margin-left: 6px;
  text-transform: uppercase;
  letter-spacing: 0.2px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  vertical-align: middle;
  line-height: 1;
}

.suami-badge {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.istri-badge {
  background: rgba(236, 72, 153, 0.15);
  color: #f472b6;
  border: 1px solid rgba(236, 72, 153, 0.3);
}
</style>
