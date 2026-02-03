// frontend/src/main.js
// Main entry point for Vue app

import { createApp } from "vue";
import App from "./App.vue";

// Initialize Vue app
createApp(App).mount("#app");

// Log Supabase connection status (for debugging)
import { supabase } from "./lib/supabase";
console.log(
    "✅ Supabase client initialized:",
    supabase ? "Connected" : "Failed",
);
