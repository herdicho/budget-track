/**
 * ==============================================================================
 * GOOGLE APPS SCRIPT: AUTO-SYNC EMAIL TRANSAKSI KE BUDGET-TRACK
 * ==============================================================================
 * Panduan Pemasangan:
 * 1. Buka https://script.google.com/ dari akun Gmail yang menerima email resi.
 * 2. Klik "New project" (Proyek baru).
 * 3. Hapus semua kode bawaan, lalu copas (copy-paste) seluruh kode di file ini.
 * 4. Ganti BACKEND_URL dengan URL backend Render Anda (contoh: https://budget-track-api.onrender.com).
 * 5. Ganti APP_PASSWORD dengan password/PIN aplikasi Budget-Track Anda (sama dengan di .env).
 * 6. Klik tombol "Save" (Icon Disket).
 * 7. Klik "Triggers" (Icon Jam di sidebar kiri) -> "Add Trigger" (Tambah Pemicu):
 *    - Choose function: syncTransactionsToBudgetTrack
 *    - Select event source: Time-driven (Berdasarkan waktu)
 *    - Select type of time based trigger: Minutes timer (Pengukur waktu menit)
 *    - Select minute interval: Every 5 minutes (Setiap 5 menit)
 * 8. Klik Save & Berikan Izin Akses Gmail saat pertama kali diminta.
 * ==============================================================================
 */

// CONFIGURATION (Sesuaikan 3 variabel di bawah ini):
var BACKEND_URL = "https://budget-track-api.onrender.com"; // Ganti dengan URL backend Render Anda
var APP_PASSWORD = "1234"; // Ganti dengan APP_PASSWORD Anda
var DEFAULT_USER_NAME = "Istri"; // Nama user bawaan untuk email masuk ini ("Suami" atau "Istri")

function syncTransactionsToBudgetTrack() {
  // Label untuk menandai email yang sudah berhasil diproses agar tidak ter-input 2x
  var LABEL_NAME = "BudgetTrack-Processed";
  var label = GmailApp.getUserLabelByName(LABEL_NAME);
  if (!label) {
    label = GmailApp.createLabel(LABEL_NAME);
  }

  // Query pencarian email transaksi dari Grab, Gojek, Shopee, Mandiri, BNI, dll
  // Hanya mencari email di inbox yang belum ada label 'BudgetTrack-Processed'
  var query = 'in:inbox -label:' + LABEL_NAME + ' (from:grab OR from:gojek OR from:shopee OR from:bankmandiri OR from:bni OR subject:"Bukti Transaksi" OR subject:"Resi" OR subject:"E-Receipt" OR subject:"Rincian Pesanan" OR subject:"Transfer")';
  
  var threads = GmailApp.search(query, 0, 10); // Ambil maks 10 email per interval
  
  if (threads.length === 0) {
    Logger.log("Tidak ada email transaksi baru.");
    return;
  }
  
  Logger.log("Ditemukan " + threads.length + " email transaksi baru.");
  
  for (var i = 0; i < threads.length; i++) {
    var messages = threads[i].getMessages();
    var lastMessage = messages[messages.length - 1]; // Ambil pesan terbaru di thread
    
    var subject = lastMessage.getSubject();
    var sender = lastMessage.getFrom();
    var body = lastMessage.getPlainBody() || lastMessage.getBody();
    
    // Potong isi body agar tidak terlalu panjang saat dikirim
    var cleanBody = body.substring(0, 5000);
    
    var payload = {
      subject: subject,
      sender: sender,
      body: cleanBody,
      user_name: DEFAULT_USER_NAME
    };
    
    var options = {
      method: "post",
      contentType: "application/json",
      headers: {
        "X-App-Password": APP_PASSWORD
      },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };
    
    try {
      var response = UrlFetchApp.fetch(BACKEND_URL + "/api/webhooks/email", options);
      var result = JSON.parse(response.getContentText());
      Logger.log("Hasil pemrosesan: " + JSON.stringify(result));
      
      // Beri label agar tidak diproses ulang di penjelajahan berikutnya
      threads[i].addLabel(label);
    } catch (e) {
      Logger.log("Error sending webhook: " + e.toString());
    }
  }
}
