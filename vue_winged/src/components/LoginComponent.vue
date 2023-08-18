<template>
    <div>
      <h1>Login</h1>
      <form @submit.prevent="handleLogin">
        <input v-model="username" type="text" placeholder="Username" required />
        <input v-model="password" type="password" placeholder="Password" required />
        <button type="submit">Login</button>
        <p v-if="error">{{ error }}</p>
      </form>
    </div>
  </template>
  
  <script>
  import axiosAuthentication from '/src/axiosAuthentication.js';

  
  export default {
    data() {
      return {
        username: '',
        password: '',
        error: null,
      };
    },
    methods: {
      async handleLogin() {
        try {
          await axiosAuthentication.login(this.username, this.password);
          // Redirect to a protected route or update the app state to reflect successful login
          this.$router.push('/'); // Example if using Vue Router
        } catch (err) {
          // Handle error, such as showing an error message to the user
          this.error = 'Invalid username or password';
        }
      },
    },
  };
  </script>
  
  <style>
  /* Add your styling here */
  </style>
  