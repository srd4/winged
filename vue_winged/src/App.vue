<template>
  <div class="container">
    <div class="containers-container">
      <ul style="padding:0;">
      <li v-for="container in container_list" :key="container.id">
        <container
        v-on:new-active="updateActive"
        :activeContainer="activeContainer" v-bind:container="container"></container>
      </li>
      </ul>
    </div>

    <container_detail :container="activeContainer"></container_detail>
  </div>
</template>

<script>
import Container_detail from './components/Container_detail.vue'
import Container from './components/Container.vue'
import axiosInstance from './axiosInstance'

export default {
  name: 'App',
  data(){
    return{
      activeContainer : null,
      container_list : [],
      items: [],
    }
  },
  components:{
    'container_detail': Container_detail,
    'container': Container,
  },
  methods: {
    updateActive : function(container){
      this.activeContainer = container;
    },
    getContainers(){
      axiosInstance.get('/containerTrees/')
        .then(response => {
          this.container_list = response.data
        })
    }
  },
  mounted(){
    this.getContainers()
  }
}

</script>


<style>
.container {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  width: 100%;
  height: 100%;
}

p {
  margin: 0;
}

a{
  cursor: pointer;
}

.containers-container {
  flex: 1;
  width: 20%;
  background-color: #131415;
  color: #e3e3e3;
  overflow-x: auto;
}

template {
  font-family: Arial, Helvetica, sans-serif;
}

.active {
  color: #ffdb59;
}

ul {
  list-style: none;
}

li {
  display: table;
}
</style>
