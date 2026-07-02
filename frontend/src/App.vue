<template>
  <div class="app-layout">
    <!-- View Switcher with Transition -->
    <Transition name="fade" mode="out-in">
      <!-- 1. Login View -->
      <Login 
        v-if="currentView === 'login'" 
        :apiUrl="apiUrl" 
        @login-success="onLoginSuccess" 
      />

      <!-- 2. Dashboard View -->
      <Dashboard 
        v-else-if="currentView === 'dashboard'" 
        :apiUrl="apiUrl" 
        :authPassword="authPassword" 
        :paymentSources="paymentSources"
        :categories="categories"
        ref="dashboardRef"
        @logout="onLogout"
        @trigger-upload="currentView = 'uploader'"
        @trigger-manual="triggerManualTransaction"
        @trigger-report="currentView = 'report'"
        @trigger-edit="triggerEditTransaction"
        @refresh-sources="fetchPaymentSources"
        @refresh-categories="fetchCategories"
        @view-all="currentView = 'transactions'"
      />

      <!-- 3. Receipt Uploader View -->
      <ReceiptUploader 
        v-else-if="currentView === 'uploader'" 
        :apiUrl="apiUrl" 
        :authPassword="authPassword" 
        @cancel="currentView = 'dashboard'"
        @upload-success="onUploadSuccess"
      />

      <!-- 4. Transaction Review View -->
      <TransactionReview 
        v-else-if="currentView === 'review'" 
        :apiUrl="apiUrl" 
        :authPassword="authPassword" 
        :extractedData="extractedData"
        :paymentSources="paymentSources"
        :categories="categories"
        @cancel="currentView = 'dashboard'"
        @save-success="onSaveSuccess"
      />

      <!-- 5. Transactions List View -->
      <TransactionList 
        v-else-if="currentView === 'transactions'" 
        :apiUrl="apiUrl" 
        :authPassword="authPassword" 
        :paymentSources="paymentSources"
        :categories="categories"
        @trigger-edit="triggerEditTransaction"
        @back="currentView = 'dashboard'"
      />

      <!-- 6. Monthly Report View -->
      <MonthlyReport
        v-else-if="currentView === 'report'"
        :apiUrl="apiUrl"
        :authPassword="authPassword"
        :paymentSources="paymentSources"
        :categories="categories"
        @back="currentView = 'dashboard'"
      />
    </Transition>

    <!-- Floating Action Button for Scan Nota (Only shown on Dashboard & Transaction List) -->
    <button 
      v-if="currentView === 'dashboard' || currentView === 'transactions'" 
      @click="currentView = 'uploader'" 
      class="fab pulse-glow"
      title="Scan Nota Belanja"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
    </button>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import Login from './components/Login.vue'
import Dashboard from './components/Dashboard.vue'
import ReceiptUploader from './components/ReceiptUploader.vue'
import TransactionReview from './components/TransactionReview.vue'
import TransactionList from './components/TransactionList.vue'
import MonthlyReport from './components/MonthlyReport.vue'

export default {
  name: 'App',
  components: {
    Login,
    Dashboard,
    ReceiptUploader,
    TransactionReview,
    TransactionList,
    MonthlyReport
  },
  setup() {
    const currentView = ref('login')
    const authPassword = ref('')
    const extractedData = ref(null)
    const dashboardRef = ref(null)
    const paymentSources = ref([])
    const categories = ref([])

    // Dynamic API URL: automatically resolves to the host's IP/domain
    // This allows seamless testing on mobile devices in the same local network
    const apiUrl = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8080`

    const fetchPaymentSources = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/payment-sources`)
        if (response.ok) {
          paymentSources.value = await response.json()
        }
      } catch (err) {
        console.error("Error fetching payment sources:", err)
      }
    }

    const fetchCategories = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/categories`)
        if (response.ok) {
          categories.value = await response.json()
        }
      } catch (err) {
        console.error("Error fetching categories:", err)
      }
    }

    onMounted(() => {
      // Auto-login if password is saved in localStorage
      const savedPass = localStorage.getItem('app_password')
      if (savedPass) {
        authPassword.value = savedPass
        currentView.value = 'dashboard'
      }
      fetchPaymentSources()
      fetchCategories()
    })

    const onLoginSuccess = (password) => {
      authPassword.value = password
      currentView.value = 'dashboard'
    }

    const onLogout = () => {
      localStorage.removeItem('app_password')
      authPassword.value = ''
      currentView.value = 'login'
    }

    const onUploadSuccess = (data) => {
      extractedData.value = data
      currentView.value = 'review'
    }

    const triggerManualTransaction = () => {
      extractedData.value = {
        merchant: '',
        date: new Date().toLocaleDateString('sv-SE'),
        category: 'Lain-lain',
        payment_source: 'Cash',
        amount: 0.0,
        user_name: 'Suami',
        items: [],
        receipt_url: '',
        transfer_to: null
      }
      currentView.value = 'review'
    }

    const triggerEditTransaction = (tx) => {
      extractedData.value = {
        id: tx.id,
        merchant: tx.merchant,
        date: tx.date,
        category: tx.category,
        payment_source: tx.payment_source,
        amount: tx.amount,
        user_name: tx.user_name,
        items: tx.items || [],
        receipt_url: tx.receipt_url || '',
        transfer_to: tx.transfer_to || null
      }
      currentView.value = 'review'
    }

    const onSaveSuccess = () => {
      currentView.value = 'dashboard'
      fetchPaymentSources()
      // Refresh dashboard data
      if (dashboardRef.value) {
        dashboardRef.value.fetchSummary()
      }
    }

    return {
      currentView,
      authPassword,
      extractedData,
      apiUrl,
      dashboardRef,
      paymentSources,
      fetchPaymentSources,
      categories,
      fetchCategories,
      onLoginSuccess,
      onLogout,
      onUploadSuccess,
      onSaveSuccess,
      triggerManualTransaction,
      triggerEditTransaction
    }
  }
}
</script>

<style>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  width: 100%;
}
</style>
