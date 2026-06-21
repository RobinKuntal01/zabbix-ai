<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../utils/supabase' // Path to your utility file

const router = useRouter()

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  errorMessage.value = ''
  isLoading.value = true

  try {
    // 1. Send authentication request straight to Supabase API
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email.value,
      password: password.value,
    })

    if (error) throw error

    // 2. Success! The session is now saved in local storage automatically.
    console.log('Logged in user:', data.user)
    
    // 3. Redirect the user to the main app screen
    router.push('/')

  } catch (error) {
    errorMessage.value = error.message || 'Invalid email or password.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h2>Welcome Back</h2>
      <p class="subtitle">Sign in to your account</p>

      <form @submit.prevent="handleLogin" class="login-form">
        <div v-if="errorMessage" class="alert alert-error">
          {{ errorMessage }}
        </div>
        
        <div v-if="successMessage" class="alert alert-success">
          {{ successMessage }}
        </div>

        <div class="form-group">
          <label for="email">Email Address</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="••••••••"
            required
            :disabled="isLoading"
          />
        </div>

        <button type="submit" :disabled="isLoading" class="btn-submit">
          <span v-if="isLoading">Signing in...</span>
          <span v-else>Sign In</span>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* Basic Clean Styling */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f3f4f6;
  font-family: system-ui, -apple-system, sans-serif;
}

.login-card {
  background: #ffffff;
  padding: 2.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  width: 100%;
  max-width: 400px;
}

h2 {
  margin: 0 0 0.5rem 0;
  color: #1f2937;
  text-align: center;
}

.subtitle {
  margin: 0 0 2rem 0;
  color: #6b7280;
  text-align: center;
  font-size: 0.9rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

input {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

input:disabled {
  background-color: #f3f4f6;
  cursor: not-allowed;
}

.btn-submit {
  background-color: #4f46e5;
  color: white;
  padding: 0.75rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background-color: #4338ca;
}

.btn-submit:disabled {
  background-color: #a5b4fc;
  cursor: not-allowed;
}

.alert {
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.alert-error {
  background-color: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.alert-success {
  background-color: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}
</style>