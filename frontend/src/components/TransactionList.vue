<template>
  <div class="transaction-list-page">
    <header class="list-header glass-panel">
      <button @click="$emit('back')" class="back-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
      </button>
      <h2>Riwayat Transaksi</h2>
      <div class="header-placeholder"></div>
    </header>

    <!-- Beautiful Content Loader -->
    <div v-if="loading" class="loading-view">
      <div class="loader-glow-ring">
        <span class="loader-icon">📜</span>
      </div>
      <h3 class="loading-text">Memuat Riwayat Transaksi...</h3>
      <p class="loading-subtext">Mengambil daftar transaksi dari database</p>
    </div>

    <template v-else>
      <!-- Filters Section -->
    <section class="filters-card glass-panel">
      <div class="form-row">
        <div class="form-group half">
          <label for="search" class="form-label">Cari Toko / Merchant</label>
          <input 
            id="search"
            type="text" 
            v-model="searchQuery" 
            class="form-input search-input" 
            placeholder="Ketik nama toko..."
          />
        </div>
        <div class="form-group half">
          <label for="filter-user" class="form-label">Belanja Oleh</label>
          <select id="filter-user" v-model="selectedUser" class="form-input select-input">
            <option value="">Semua</option>
            <option value="Suami">Suami</option>
            <option value="Istri">Istri</option>
          </select>
        </div>
      </div>

      <div class="form-row">
        <!-- Category Filter -->
        <div class="form-group half">
          <label for="filter-category" class="form-label">Kategori</label>
          <select id="filter-category" v-model="selectedCategory" class="form-input select-input">
            <option value="">Semua</option>
            <option v-for="cat in categories" :key="cat.id || cat.name" :value="cat.name">
              {{ cat.emoji }} {{ cat.name }}
            </option>
          </select>
        </div>

        <!-- Source Filter -->
        <div class="form-group half">
          <label for="filter-source" class="form-label">Sumber Dana</label>
          <select id="filter-source" v-model="selectedSource" class="form-input select-input">
            <option value="">Semua</option>
            <option v-for="source in paymentSources" :key="source.id || source.name" :value="source.name">
              {{ source.name }}
            </option>
          </select>
        </div>
      </div>
    </section>

    <!-- Transactions List -->
    <section class="list-card glass-panel">
      <div v-if="filteredTransactions.length === 0" class="empty-state">
        Tidak ada transaksi yang cocok dengan filter.
      </div>

      <div v-else>
        <!-- Info count -->
        <div class="pagination-info">
          Menampilkan {{ paginationStart }}-{{ paginationEnd }} dari {{ filteredTransactions.length }} transaksi
        </div>

        <div class="transactions-list">
          <div v-for="tx in paginatedTransactions" :key="tx.id" class="tx-item">
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
                <span class="tx-meta">
                  {{ formatDateFull(tx.date) }} &bull; 
                  <span v-if="tx.category === 'Transfer'">
                    {{ tx.payment_source }} ➔ {{ tx.transfer_to }}
                  </span>
                  <span v-else>
                    {{ tx.payment_source }}
                  </span>
                </span>
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

        <!-- Pagination Controls -->
        <div v-if="totalPages > 1" class="pagination-controls">
          <button 
            @click="goToPage(currentPage - 1)" 
            :disabled="currentPage === 1" 
            class="page-btn nav-page-btn"
          >
            &larr; Prev
          </button>
          
          <div class="page-numbers">
            <button 
              v-for="page in visiblePages" 
              :key="page" 
              @click="goToPage(page)" 
              class="page-btn" 
              :class="{ 'active-page': page === currentPage }"
            >
              {{ page }}
            </button>
          </div>

          <button 
            @click="goToPage(currentPage + 1)" 
            :disabled="currentPage === totalPages" 
            class="page-btn nav-page-btn"
          >
            Next &rarr;
          </button>
        </div>
      </div>
    </section>
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'

export default {
  name: 'TransactionList',
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
  emits: ['back', 'trigger-edit'],
  setup(props) {
    const loading = ref(true)
    const transactions = ref([])
    const searchQuery = ref('')
    const selectedCategory = ref('')
    const selectedSource = ref('')
    const selectedUser = ref('')
    const currentPage = ref(1)
    const itemsPerPage = 15

    const fetchTransactions = async () => {
      loading.value = true
      try {
        const response = await fetch(`${props.apiUrl}/api/transactions`, {
          headers: {
            'X-App-Password': props.authPassword
          }
        })
        if (response.ok) {
          transactions.value = await response.json()
        }
      } catch (err) {
        console.error("Error fetching transactions:", err)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      fetchTransactions()
    })

    const filteredTransactions = computed(() => {
      return transactions.value.filter(tx => {
        const merchantName = tx.merchant || ''
        const matchSearch = merchantName.toLowerCase().includes((searchQuery.value || '').toLowerCase())
        const matchCategory = !selectedCategory.value || tx.category === selectedCategory.value
        const matchSource = !selectedSource.value || tx.payment_source === selectedSource.value
        const matchUser = !selectedUser.value || tx.user_name === selectedUser.value
        return matchSearch && matchCategory && matchSource && matchUser
      })
    })

    // Reset page when filters change
    watch([searchQuery, selectedCategory, selectedSource, selectedUser], () => {
      currentPage.value = 1
    })

    const totalPages = computed(() => {
      return Math.max(1, Math.ceil(filteredTransactions.value.length / itemsPerPage))
    })

    const paginatedTransactions = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredTransactions.value.slice(start, end)
    })

    const paginationStart = computed(() => {
      if (filteredTransactions.value.length === 0) return 0
      return (currentPage.value - 1) * itemsPerPage + 1
    })

    const paginationEnd = computed(() => {
      return Math.min(currentPage.value * itemsPerPage, filteredTransactions.value.length)
    })

    const visiblePages = computed(() => {
      const pages = []
      const total = totalPages.value
      const current = currentPage.value
      
      let start = Math.max(1, current - 2)
      let end = Math.min(total, current + 2)
      
      // Ensure we always show 5 pages if available
      if (end - start < 4) {
        if (start === 1) {
          end = Math.min(total, start + 4)
        } else {
          start = Math.max(1, end - 4)
        }
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    })

    const goToPage = (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page
        // Scroll to top of list
        document.querySelector('.list-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }

    const formatCurrency = (val) => {
      return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        maximumFractionDigits: 0
      }).format(val || 0)
    }

    const formatDateFull = (dateStr) => {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      if (isNaN(d.getTime())) return dateStr
      return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
    }

    const getCategoryColor = (catName) => {
      if (!catName) return '#ff5555'
      const cat = props.categories.find(c => c.name && c.name.toLowerCase() === catName.toLowerCase())
      if (cat && cat.color) return cat.color
      const colors = {
        'Makanan': '#ff79c6',
        'Transportasi': '#8be9fd',
        'Kebutuhan Bulanan': '#50fa7b',
        'Kebutuhan Bayi': '#ffb86c',
        'Hiburan': '#bd93f9',
        'Transfer': '#0ea5e9',
        'Pendapatan': '#50fa7b',
        'Lain-lain': '#ff5555'
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
          fetchTransactions()
        }
      } catch (err) {
        console.error("Error deleting transaction:", err)
      }
    }

    return {
      loading,
      transactions,
      searchQuery,
      selectedCategory,
      selectedSource,
      selectedUser,
      currentPage,
      totalPages,
      filteredTransactions,
      paginatedTransactions,
      paginationStart,
      paginationEnd,
      visiblePages,
      goToPage,
      formatCurrency,
      formatDateFull,
      getCategoryColor,
      getCategoryEmoji,
      deleteTransaction
    }
  }
}
</script>

<style scoped>
.transaction-list-page {
  width: 100%;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.list-header {
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-btn {
  background: transparent;
  border: none;
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.05);
}

.list-header h2 {
  font-size: 16px;
  font-weight: 700;
  margin: 0;
}

.header-placeholder {
  width: 32px; /* same width as back-btn for centering */
}

/* Filters */
.filters-card {
  padding: 20px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.half {
  flex: 1;
  min-width: 0;
}

.select-input {
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 14px;
  padding-right: 32px;
}

.search-input {
  font-size: 14px;
  padding: 12px 14px;
}

/* Transactions list styling */
.list-card {
  padding: 20px;
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
  text-align: left;
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

.empty-state {
  text-align: center;
  padding: 32px;
  font-size: 13px;
  color: var(--text-muted);
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

/* Pagination */
.pagination-info {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.page-numbers {
  display: flex;
  gap: 4px;
}

.page-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--glass-border);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 36px;
  text-align: center;
}

.page-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-btn.active-page {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.nav-page-btn {
  font-size: 11px;
  padding: 6px 10px;
}
</style>
