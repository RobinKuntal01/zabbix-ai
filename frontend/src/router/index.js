import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import AgentView from '../views/AgentView.vue'
import AddDoxView from '../views/AddDoxView.vue'

const routes = [
  {
    path: '/',
    name: 'Chat',
    component: ChatView
  },
  {
    path: '/agent',
    name: 'Agent',
    component: AgentView
  },
  {
    path: '/add-dox',
    name: 'AddDox',
    component: AddDoxView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
