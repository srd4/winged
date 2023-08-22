import { createApp } from 'vue'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router';
import LoginComponent from './components/LoginComponent.vue';
import DashboardComponent from './components/DashboardComponent.vue';

const routes = [
  { path: '/login', component: LoginComponent },
  { path: '/', component: DashboardComponent, meta: { requiresAuth: true } },
];


const router = createRouter({
    history: createWebHistory(),
    routes,
});


router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('token');

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
  } else {
    next(); // Change this to next() to allow navigation to the original target route
  }
});

const app = createApp(App);
app.use(router);
app.mount('#app');