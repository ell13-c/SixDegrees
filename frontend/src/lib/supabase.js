// frontend/src/lib/supabase.js

/**
 * Supabase Client Configuration for SixDegrees
 *
 * This initializes the Supabase client for frontend use.
 * Handles authentication, database queries, and real-time subscriptions.
 */

import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Validate environment variables
if (!supabaseUrl || !supabaseAnonKey) {
    console.error("❌ Missing Supabase environment variables!");
    console.error("Please create a .env file based on .env.example");
    throw new Error("Supabase configuration missing. Check your .env file.");
}

// Create and export Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
    },
});

// Helper function to check if user is authenticated
export const isAuthenticated = async () => {
    const {
        data: { session },
    } = await supabase.auth.getSession();
    return !!session;
};

// Helper function to get current user
export const getCurrentUser = async () => {
    const {
        data: { user },
    } = await supabase.auth.getUser();
    return user;
};

// Helper function to sign out
export const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    localStorage.removeItem("supabase_token");
    localStorage.removeItem("user_id");
};
