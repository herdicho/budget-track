<template>
  <div class="report-container">
    <!-- Header Section -->
    <header class="report-header">
      <button @click="$emit('back')" class="btn-back">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
        Kembali ke Dashboard
      </button>
      
      <!-- Month Navigator -->
      <div class="month-navigator">
        <button @click="changeMonth(-1)" class="nav-btn">&lsaquo;</button>
        <span class="month-title">{{ formatMonthLabel(selectedMonth) }}</span>
        <button @click="changeMonth(1)" class="nav-btn">&rsaquo;</button>
      </div>
    </header>

    <!-- Main Content Loader -->
    <div v-if="loading" class="loading-view">
      <div class="loader-glow-ring">
        <span class="loader-icon">📊</span>
      </div>
      <h3 class="loading-text">Memuat Laporan Keuangan...</h3>
      <p class="loading-subtext">Menganalisis pengeluaran dan pemasukan Anda</p>
    </div>

    <div v-else class="report-content">
      <!-- 1. Metrics Grid Card -->
      <section class="metrics-grid">
        <!-- Inflow Card -->
        <div class="metric-card glass-panel inflow">
          <div class="metric-icon">💵</div>
          <div class="metric-info">
            <span class="metric-label">Total Pendapatan</span>
            <h3 class="metric-val text-green">{{ formatCurrency(summary.income) }}</h3>
          </div>
        </div>

        <!-- Outflow Card -->
        <div class="metric-card glass-panel outflow">
          <div class="metric-icon">🛒</div>
          <div class="metric-info">
            <span class="metric-label">Total Belanja</span>
            <h3 class="metric-val text-pink">{{ formatCurrency(summary.total_spent) }}</h3>
          </div>
        </div>

        <!-- Net Savings Card -->
        <div class="metric-card glass-panel savings">
          <div class="metric-icon">💰</div>
          <div class="metric-info">
            <span class="metric-label">Sisa Uang Net</span>
            <h3 class="metric-val text-teal" :class="{ 'danger-text': summary.net_balance < 0 }">
              {{ formatCurrency(summary.net_balance) }}
            </h3>
          </div>
        </div>

        <!-- Budget Compliance Card -->
        <div class="metric-card glass-panel compliance">
          <div class="metric-icon">📊</div>
          <div class="metric-info">
            <span class="metric-label">Batas Anggaran Belanja</span>
            <div class="compliance-header">
              <span class="metric-val small-val">{{ formatCurrency(spentForBudget) }} / {{ formatCurrency(summary.budget) }}</span>
              <span class="status-tag" :class="budgetStatusClass">{{ budgetStatusLabel }}</span>
            </div>
            <div class="compliance-progress">
              <div class="compliance-fill" :style="{ width: `${budgetSpentPercent}%` }" :class="budgetStatusClass"></div>
            </div>
          </div>
        </div>
      </section>

      <!-- 2. Main Donut Chart (Full Width Layout) -->
      <section class="chart-card glass-panel full-width-chart">
        <h3 class="section-title">Proporsi Pengeluaran Kategori</h3>
        
        <div v-if="chartSegments.length === 0" class="empty-state">
          Tidak ada data pengeluaran bulan ini.
        </div>

        <div v-else class="chart-donut-container">
          <!-- Pure SVG Donut Chart -->
          <div class="donut-wrapper">
            <svg width="220" height="220" viewBox="0 0 140 140" class="donut-svg">
              <!-- Background circle -->
              <circle 
                cx="70" 
                cy="70" 
                r="50" 
                fill="transparent" 
                stroke="rgba(255, 255, 255, 0.05)" 
                stroke-width="14" 
              />
              <!-- Segment circles -->
              <circle 
                v-for="seg in chartSegments" 
                :key="seg.name" 
                cx="70" 
                cy="70" 
                r="50" 
                fill="transparent" 
                :stroke="seg.color" 
                stroke-width="14" 
                :stroke-dasharray="seg.strokeDasharray" 
                :stroke-dashoffset="seg.strokeDashoffset" 
                transform="rotate(-90 70 70)"
                class="donut-segment"
              />
              <!-- Center Label -->
              <text x="70" y="65" text-anchor="middle" class="donut-center-title">TOTAL BELANJA</text>
              <text x="70" y="85" text-anchor="middle" class="donut-center-value">{{ formatCurrencyShort(spentForBudget) }}</text>
            </svg>
          </div>

          <!-- Legend List -->
          <div class="legend-list">
            <div v-for="seg in chartSegments" :key="seg.name" class="legend-item">
              <span class="legend-bullet" :style="{ backgroundColor: seg.color }"></span>
              <span class="legend-emoji">{{ seg.emoji }}</span>
              <span class="legend-name">{{ seg.name }}</span>
              <span class="legend-percent">{{ seg.percentage }}%</span>
              <span class="legend-value">{{ formatCurrencyShort(seg.amount) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 3. Weekly Spending Breakdown -->
      <section class="chart-card glass-panel full-width-chart">
        <h3 class="section-title">📅 Pengeluaran per Minggu</h3>
        
        <div v-if="weeklyData.length === 0" class="empty-state">
          Tidak ada data pengeluaran bulan ini.
        </div>

        <div v-else class="weekly-breakdown">
          <div v-for="week in weeklyData" :key="week.label" class="weekly-row-container">
            <!-- Clickable Week Row -->
            <div class="weekly-row" :class="{ 'has-data': week.total > 0 }" @click="toggleWeek(week.label)">
              <div class="weekly-info">
                <span class="weekly-label">
                  <span class="weekly-chevron" :class="{ 'expanded': expandedWeeks[week.label] }">›</span>
                  {{ week.label }}
                </span>
                <span class="weekly-date-range">{{ week.dateRange }}</span>
              </div>
              <div class="weekly-bar-wrapper">
                <div class="weekly-bar-track">
                  <div 
                    v-if="week.total > 0"
                    class="weekly-bar-fill" 
                    :style="{ width: `${week.percent}%` }"
                  ></div>
                </div>
                <span class="weekly-amount" :class="{ 'has-value': week.total > 0 }">{{ formatCurrencyShort(week.total) }}</span>
              </div>
            </div>

            <!-- Collapsible Transaction Details -->
            <Transition name="collapse">
              <div v-if="expandedWeeks[week.label] && week.transactions.length > 0" class="weekly-details">
                <div v-for="tx in week.transactions" :key="tx.id" class="weekly-tx-item">
                  <div class="weekly-tx-left">
                    <span class="weekly-tx-emoji">{{ getCategoryEmoji(tx.category) }}</span>
                    <div class="weekly-tx-info">
                      <span class="weekly-tx-merchant">{{ tx.merchant }}</span>
                      <span class="weekly-tx-meta">{{ formatDateShort(tx.date) }} • {{ tx.payment_source }}</span>
                    </div>
                  </div>
                  <span class="weekly-tx-amount">{{ formatCurrencyShort(tx.amount) }}</span>
                </div>
              </div>
            </Transition>

            <!-- Empty state for expanded week with no data -->
            <div v-if="expandedWeeks[week.label] && week.transactions.length === 0" class="weekly-details-empty">
              Tidak ada pengeluaran di minggu ini.
            </div>
          </div>

          <!-- Weekly Total Summary -->
          <div class="weekly-summary">
            <span class="weekly-summary-label">Rata-rata / minggu</span>
            <span class="weekly-summary-value">{{ formatCurrency(weeklyAverage) }}</span>
          </div>
        </div>
      </section>

      <!-- 4. Secondary Reports (Side-by-side Below) -->
      <div class="secondary-charts-layout">
        <!-- Split card -->
        <section class="chart-card glass-panel">
          <h3 class="section-title">Pembagian Belanja Keluarga</h3>
          <div class="split-comparison">
            <!-- Suami Bar -->
            <div class="split-user-row">
              <div class="split-user-info">
                <span class="split-name">🙋‍♂️ Suami</span>
                <span class="split-amount">{{ formatCurrency(summary.users?.Suami || 0) }} ({{ userSpentPercent('Suami') }}%)</span>
              </div>
              <div class="split-progress">
                <div class="split-progress-fill suami" :style="{ width: `${userSpentPercent('Suami')}%` }"></div>
              </div>
            </div>

            <!-- Istri Bar -->
            <div class="split-user-row">
              <div class="split-user-info">
                <span class="split-name">🙋‍♀️ Istri</span>
                <span class="split-amount">{{ formatCurrency(summary.users?.Istri || 0) }} ({{ userSpentPercent('Istri') }}%)</span>
              </div>
              <div class="split-progress">
                <div class="split-progress-fill istri" :style="{ width: `${userSpentPercent('Istri')}%` }"></div>
              </div>
            </div>
          </div>
        </section>

        <!-- Dynamic Financial Insight Card -->
        <section class="insight-card glass-panel">
          <h3 class="section-title">Rekomendasi & Analisis Saku</h3>
          <div class="insight-content">
            <div class="insight-emoji">{{ insightEmoji }}</div>
            <div class="insight-text-wrapper">
              <h4 class="insight-heading">{{ insightTitle }}</h4>
              <p class="insight-desc">{{ insightDescription }}</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'

export default {
  name: 'MonthlyReport',
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
  emits: ['back'],
  setup(props) {
    const selectedMonth = ref(new Date().toISOString().substring(0, 7))
    const loading = ref(false)
    const summary = ref({
      month: selectedMonth.value,
      budget: 0.0,
      income: 0.0,
      total_spent: 0.0,
      remaining: 0.0,
      net_balance: 0.0,
      categories: {},
      sources: {},
      users: {}
    })

    const fetchReportData = async () => {
      loading.value = true
      try {
        const response = await fetch(`${props.apiUrl}/api/dashboard/summary?month=${selectedMonth.value}`, {
          headers: {
            'X-App-Password': props.authPassword
          }
        })
        if (response.ok) {
          summary.value = await response.json()
        }
      } catch (err) {
        console.error("Error fetching report data:", err)
      } finally {
        loading.value = false
      }
    }

    watch(selectedMonth, () => {
      fetchReportData()
      fetchTransactionsForWeekly()
    })

    // Fetch transactions for weekly breakdown
    const monthTransactions = ref([])

    const fetchTransactionsForWeekly = async () => {
      try {
        const response = await fetch(`${props.apiUrl}/api/transactions?month=${selectedMonth.value}`, {
          headers: {
            'X-App-Password': props.authPassword
          }
        })
        if (response.ok) {
          monthTransactions.value = await response.json()
        }
      } catch (err) {
        console.error("Error fetching transactions for weekly:", err)
      }
    }

    onMounted(() => {
      fetchReportData()
      fetchTransactionsForWeekly()
    })

    // Weekly spending calculation
    const expandedWeeks = ref({})

    const toggleWeek = (label) => {
      expandedWeeks.value[label] = !expandedWeeks.value[label]
    }

    const weeklyData = computed(() => {
      const txs = monthTransactions.value || []
      // Filter out transfers, income, saldo awal, AND keluarga
      const expenses = txs.filter(t => !['Transfer', 'Pendapatan', 'Saldo Awal', 'Keluarga'].includes(t.category))
      
      if (expenses.length === 0) return []

      const weeks = [
        { label: 'Minggu 1', start: 4, end: 10, dateRange: 'Tgl 4 - 10', total: 0, transactions: [] },
        { label: 'Minggu 2', start: 11, end: 17, dateRange: 'Tgl 11 - 17', total: 0, transactions: [] },
        { label: 'Minggu 3', start: 18, end: 24, dateRange: 'Tgl 18 - 24', total: 0, transactions: [] },
        { label: 'Minggu 4', start: 25, end: 31, dateRange: 'Tgl 25 - 31', total: 0, transactions: [] }
      ]

      for (const tx of expenses) {
        const day = new Date(tx.date).getDate()
        const amount = parseFloat(tx.amount) || 0
        for (const w of weeks) {
          if (day >= w.start && day <= w.end) {
            w.total += amount
            w.transactions.push(tx)
            break
          }
        }
      }

      // Sort transactions within each week by date descending
      for (const w of weeks) {
        w.transactions.sort((a, b) => new Date(b.date) - new Date(a.date))
      }

      // Find max for bar scaling
      const maxTotal = Math.max(...weeks.map(w => w.total), 1)

      return weeks.map(w => ({
          ...w,
          percent: w.total > 0 ? Math.max(Math.round((w.total / maxTotal) * 100), 3) : 0
        }))
    })

    const formatDateShort = (dateStr) => {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
    }

    const weeklyAverage = computed(() => {
      const data = weeklyData.value.filter(w => w.total > 0)
      if (data.length === 0) return 0
      const total = data.reduce((sum, w) => sum + w.total, 0)
      return Math.round(total / data.length)
    })

    const changeMonth = (offset) => {
      const [year, month] = selectedMonth.value.split('-').map(Number)
      const d = new Date(Date.UTC(year, month - 1 + offset, 1))
      selectedMonth.value = d.toISOString().substring(0, 7)
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

    const formatCurrencyShort = (val) => {
      if (!val) return 'Rp 0'
      if (val >= 1000000) {
        const jt = val / 1000000
        return `Rp ${jt % 1 === 0 ? jt.toFixed(0) : jt.toFixed(1)}jt`
      }
      if (val >= 1000) {
        return `Rp ${Math.round(val / 1000)}rb`
      }
      return `Rp ${val}`
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

    // Calculations - exclude Keluarga from budget
    const spentForBudget = computed(() => {
      const total = summary.value.total_spent || 0
      const cats = summary.value.categories || {}
      const keluargaKey = Object.keys(cats).find(k => k.toLowerCase() === 'keluarga')
      const keluargaSpent = keluargaKey ? (cats[keluargaKey] || 0) : 0
      return Math.max(0, total - keluargaSpent)
    })

    const budgetSpentPercent = computed(() => {
      const limit = summary.value.budget || 0
      if (limit <= 0) return 0
      return Math.min(Math.round((spentForBudget.value / limit) * 100), 100)
    })

    const budgetStatusClass = computed(() => {
      const percent = (spentForBudget.value / (summary.value.budget || 1)) * 100
      if (percent > 100) return 'danger'
      if (percent > 85) return 'warning'
      return 'success'
    })

    const budgetStatusLabel = computed(() => {
      const percent = (spentForBudget.value / (summary.value.budget || 1)) * 100
      if (percent > 100) return 'Over Budget 🚨'
      if (percent > 85) return 'Waspada ⚠️'
      return 'Hemat 👍'
    })

    const userSpentPercent = (user) => {
      const total = summary.value.total_spent || 0
      if (total <= 0) return 0
      const userSpent = summary.value.users ? (summary.value.users[user] || 0) : 0
      return Math.round((userSpent / total) * 100)
    }

    // SVG Donut segments calculations
    const chartSegments = computed(() => {
      const cats = summary.value.categories || {}
      // Exclude Keluarga from chart
      const filteredCats = Object.entries(cats).filter(([name]) => name.toLowerCase() !== 'keluarga')
      const total = filteredCats.reduce((a, [, b]) => a + b, 0)
      if (total <= 0) return []

      let cumulativeOffset = 0
      const circumference = 2 * Math.PI * 50 // 314.159

      return filteredCats.map(([name, amount]) => {
        const percentage = (amount / total) * 100
        const segLen = (amount / total) * circumference
        const seg = {
          name,
          amount,
          percentage: Math.round(percentage),
          strokeDasharray: `${segLen} ${circumference - segLen}`,
          strokeDashoffset: `${-cumulativeOffset}`,
          color: getCategoryColor(name),
          emoji: getCategoryEmoji(name)
        }
        cumulativeOffset += segLen
        return seg
      })
    })

    // Financial Insights generator
    const insightEmoji = computed(() => {
      const spent = summary.value.total_spent || 0
      const budget = summary.value.budget || 0
      const income = summary.value.income || 0

      if (spent > budget && budget > 0) return '🤒'
      if (spent > income && income > 0) return '😱'
      if (spent > 0 && spent < budget * 0.5) return '🥳'
      return '💡'
    })

    const insightTitle = computed(() => {
      const spent = summary.value.total_spent || 0
      const budget = summary.value.budget || 0
      const income = summary.value.income || 0

      if (spent > budget && budget > 0) return 'Bocor Alus! Anggaran Terlampaui'
      if (spent > income && income > 0) return 'Defisit Tabungan (Gali Lobang)'
      if (spent > 0 && spent < budget * 0.5) return 'Saku Sangat Sehat!'
      return 'Analisis Ringkas Bulan Ini'
    })

    const insightDescription = computed(() => {
      const spent = summary.value.total_spent || 0
      const budget = summary.value.budget || 0
      const income = summary.value.income || 0
      const cats = summary.value.categories || {}

      if (Object.keys(cats).length === 0) {
        return 'Belum ada data belanja tercatat. Mulai catat belanja Anda untuk melihat analisis saku.'
      }

      // Find top expense category
      const topCat = Object.entries(cats).reduce((max, curr) => curr[1] > max[1] ? curr : max, ['', 0])

      let desc = `Pengeluaran terbesar keluarga berada pada kategori "${topCat[0]}" sebesar ${formatCurrency(topCat[1])}. `

      if (spent > budget && budget > 0) {
        desc += 'Pengeluaran bulanan Anda sudah melewati batas rencana anggaran belanja. Cobalah untuk menunda pembelian non-primer di sisa hari ini.'
      } else if (spent > 0 && spent < budget * 0.5) {
        desc += 'Luar biasa! Pengeluaran belanja bulanan Anda masih di bawah 50% dari rencana anggaran belanja. Anda memiliki ruang tabungan yang sangat baik!'
      } else {
        desc += 'Pencatatan saku berjalan stabil. Tetap pantau pengeluaran Anda agar sisa tabungan dapat dialokasikan ke rekening investasi/cadangan.'
      }
      return desc
    })

    return {
      selectedMonth,
      loading,
      summary,
      spentForBudget,
      changeMonth,
      formatMonthLabel,
      formatCurrency,
      formatCurrencyShort,
      formatDateShort,
      getCategoryColor,
      getCategoryEmoji,
      budgetSpentPercent,
      budgetStatusClass,
      budgetStatusLabel,
      userSpentPercent,
      chartSegments,
      weeklyData,
      weeklyAverage,
      expandedWeeks,
      toggleWeek,
      insightEmoji,
      insightTitle,
      insightDescription
    }
  }
}
</script>

<style scoped>
.report-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 16px;
  color: var(--text-primary);
  width: 100%;
}

.report-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.btn-back {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  border-radius: 12px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.12);
}

.month-navigator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  padding: 10px 16px;
}

.nav-btn {
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 24px;
  cursor: pointer;
  padding: 0 8px;
  line-height: 1;
}

.month-title {
  font-size: 14px;
  font-weight: 700;
  min-width: 110px;
  text-align: center;
}

/* Unused .loader-container styling removed in favor of global .loading-view */

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  box-sizing: border-box;
}

.metric-icon {
  font-size: 24px;
  background: rgba(255, 255, 255, 0.05);
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--glass-border);
}

.metric-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-val {
  font-size: 18px;
  font-weight: 800;
  margin: 0;
}

.metric-val.small-val {
  font-size: 13px;
  font-weight: 700;
}

.text-green {
  color: #50fa7b;
}

.text-pink {
  color: #ff79c6;
}

.text-teal {
  color: #8be9fd;
}

.danger-text {
  color: #ff5555;
}

.compliance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.status-tag {
  font-size: 9px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 6px;
}

.status-tag.success {
  background: rgba(80, 250, 123, 0.15);
  color: #50fa7b;
}

.status-tag.warning {
  background: rgba(255, 184, 108, 0.15);
  color: #ffb86c;
}

.status-tag.danger {
  background: rgba(255, 85, 85, 0.15);
  color: #ff5555;
}

.compliance-progress {
  height: 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  overflow: hidden;
  margin-top: 4px;
  width: 100%;
}

.compliance-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.compliance-fill.success {
  background: #50fa7b;
}

.compliance-fill.warning {
  background: #ffb86c;
}

.compliance-fill.danger {
  background: #ff5555;
}

/* Charts layout */
.secondary-charts-layout {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  padding: 20px;
}

.full-width-chart {
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 16px;
  letter-spacing: -0.2px;
}

.chart-donut-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  margin-top: 10px;
}

.donut-wrapper {
  position: relative;
  display: flex;
  justify-content: center;
}

.donut-segment {
  transition: stroke-dashoffset 0.4s ease;
}

.donut-center-title {
  font-size: 7px;
  font-weight: 600;
  fill: var(--text-muted);
}

.donut-center-value {
  font-size: 12px;
  font-weight: 800;
  fill: var(--text-primary);
}

.legend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  border-top: 1px solid var(--glass-border);
  padding-top: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  font-size: 12px;
  font-weight: 500;
  width: 100%;
}

.legend-bullet {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  flex-shrink: 0;
}

.legend-emoji {
  margin-right: 8px;
}

.legend-name {
  color: var(--text-muted);
  flex-grow: 1;
}

.legend-percent {
  font-weight: 700;
  margin-right: 12px;
  width: 32px;
  text-align: right;
}

.legend-value {
  font-weight: 600;
  color: var(--text-primary);
}

/* Right side charts */
.secondary-charts-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.split-comparison {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.split-user-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.split-user-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
}

.split-name {
  color: var(--text-muted);
}

.split-amount {
  color: var(--text-primary);
}

.split-progress {
  height: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  overflow: hidden;
}

.split-progress-fill {
  height: 100%;
  border-radius: 6px;
  width: 0;
  transition: width 0.3s ease;
}

.split-progress-fill.suami {
  background: linear-gradient(90deg, #8be9fd, #0ea5e9);
}

.split-progress-fill.istri {
  background: linear-gradient(90deg, #ff79c6, #bd93f9);
}

/* Insight card */
.insight-card {
  padding: 18px;
  background: rgba(139, 233, 253, 0.03);
  border: 1px solid rgba(139, 233, 253, 0.15);
}

.insight-content {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.insight-emoji {
  font-size: 26px;
  line-height: 1;
}

.insight-text-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.insight-heading {
  font-size: 13px;
  font-weight: 700;
  color: #8be9fd;
  margin: 0;
}

.insight-desc {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
}

/* Mobile responsive */
@media (max-width: 650px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  .chart-donut-container {
    gap: 24px;
  }
  .secondary-charts-layout {
    grid-template-columns: 1fr;
  }
}

/* Weekly Breakdown */
.weekly-breakdown {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.weekly-row-container {
  border-radius: 10px;
  overflow: hidden;
}

.weekly-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.weekly-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.weekly-row.has-data {
  cursor: pointer;
}

.weekly-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.weekly-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.weekly-chevron {
  display: inline-block;
  font-size: 16px;
  font-weight: 800;
  color: var(--text-muted);
  transition: transform 0.25s ease;
  transform: rotate(0deg);
  width: 12px;
  text-align: center;
}

.weekly-chevron.expanded {
  transform: rotate(90deg);
  color: var(--text-primary);
}

.weekly-date-range {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

.weekly-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weekly-bar-track {
  flex: 1;
  height: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  overflow: hidden;
}

.weekly-bar-fill {
  height: 100%;
  border-radius: 6px;
  background: linear-gradient(90deg, #8b5cf6 0%, #d946ef 100%);
  transition: width 0.4s ease;
}

.weekly-amount {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  min-width: 70px;
  text-align: right;
}

.weekly-amount.has-value {
  color: var(--text-primary);
}

/* Collapsible Details */
.weekly-details {
  padding: 0 12px 12px 30px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.weekly-details-empty {
  padding: 8px 12px 12px 30px;
  font-size: 11px;
  color: var(--text-muted);
  font-style: italic;
}

.weekly-tx-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.weekly-tx-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.weekly-tx-emoji {
  font-size: 14px;
  flex-shrink: 0;
}

.weekly-tx-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.weekly-tx-merchant {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.weekly-tx-meta {
  font-size: 10px;
  color: var(--text-muted);
}

.weekly-tx-amount {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  flex-shrink: 0;
  margin-left: 8px;
}

/* Collapse transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}

.weekly-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--glass-border);
}

.weekly-summary-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
}

.weekly-summary-value {
  font-size: 14px;
  font-weight: 800;
  color: #8be9fd;
}
</style>
