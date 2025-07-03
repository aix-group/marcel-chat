import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '@/services/admin'

const HomeView = () => import('@/views/HomeView.vue')
const AdminHomeView = () => import('@/views/admin/AdminHomeView.vue')
const AdminLayout = () => import('@/layouts/AdminLayout.vue')
const LoginView = () => import('@/views/admin/LoginView.vue')
const ConversationsView = () => import('@/views/admin/ConversationsView.vue')
const ConversationView = () => import('@/views/admin/ConversationView.vue')
const PrivacyView = () => import('@/views/PrivacyView.vue')
const PathNotFound = () => import('@/views/PathNotFound.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        requiresAuth: false
      }
    },
    {
      path: '/c/:id',
      name: 'chat',
      component: HomeView,
      meta: {
        requiresAuth: false
      }
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: PrivacyView,
      meta: {
        requiresAuth: false
      }
    },
    {
      path: '/admin/login/',
      name: 'login',
      component: LoginView,
      meta: {
        requiresAuth: false
      }
    },
    {
      path: '/admin',
      component: AdminLayout,
      children: [
        {
          path: '',
          name: 'AdminHome',
          component: AdminHomeView,
          meta: {
            requiresAuth: true
          }
        },
        {
          path: 'conversations',
          name: 'conversations',
          component: ConversationsView,
          meta: {
            requiresAuth: true
          }
        },
        {
          path: 'conversations/:id',
          name: 'conversation',
          component: ConversationView,
          meta: {
            requiresAuth: true
          }
        }
      ]
    },
    { path: '/:pathMatch(.*)*', component: PathNotFound }
  ]
})

router.beforeEach(async (to) => {
  if (to.meta.requiresAuth) {
    const authenticated = await isAuthenticated()
    if (!authenticated && to.name !== 'login') {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (authenticated && to.name == 'login') {
      return { name: 'conversations' }
    }
  }
})

export default router
