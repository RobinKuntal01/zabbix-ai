import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import AgentView from '../views/AgentView.vue'
import AddDoxView from '../views/AddDoxView.vue'
import { supabase } from '../utils/supabase'
import LoginView from '../views/LoginView.vue'

const routes = [
  {
    path: '/',
    name: 'Chat',
    component: ChatView,
    meta: { requiresAuth: true }
  },
  {
    path: '/agent',
    name: 'Agent',
    component: AgentView,
    meta: { requiresAuth: true }
  },
  {
    path: '/add-dox',
    name: 'AddDox',
    component: AddDoxView,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    component: LoginView,
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Global route guard
router.beforeEach(async (to, from, next) => {
  const { data: { session } } = await supabase.auth.getSession()

  if (to.meta.requiresAuth && !session) {
    next('/login')
  } else if (to.path === '/login' && session) {
    next('/')
  } else {
    next()
  }
})

export default router
