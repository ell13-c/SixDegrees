<!--
ROOT COMPONENT - This is the main wrapper for our whole app
TODO: Import and render the Login component for now
Later we can add router-view here for multiple pages
-->

<template>
  <div id="app">
    <Login />
  </div>
</template>

<script setup>
import Login from './views/Login.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
</style>
