<template>
      <button v-if="container.children.length > 0"
        class="collapse-triangle"
        v-on:click="toggleChildrenContainers">
        {{ collapsed }}</button>
      <span v-else class="dot">•</span>

      <a v-on:click="$emit('new-active', container)"
        v-bind:class="{ active: activeContainer === container }">
        {{container.name}}</a>

        <ul v-if="container.children.length > 0" :class="['children-list', container.id, { 'collapsed': container.is_collapsed }]">
          <li v-for="children_container in container.children">
            <container :activeContainer="activeContainer" v-on:new-active="reportUpdateActive" v-on:get-container-detail="repotGetContainerDetail" v-bind:container="children_container"></container>
          </li>
        </ul>
  </template>
  
  <script>
  import axiosInstance from '../axiosInstance'

  export default {
    emits: ['get-container-detail', 'new-active'],
    name: 'Container',
    //container prop is send from parent Container.vue components, is_active comes from App.vue
    props: ['container', 'activeContainer'],
    data(){
      return {
        collapsed: this.container.is_collapsed ? '▹' : '▿',
      }
    },
    components: {
      'container': 'Container'
    },
    methods : {
      reportUpdateActive : function(container){
        this.$emit('new-active', container)
      },
      repotGetContainerDetail: function(containerId) {
        this.$emit('get-container-detail', containerId)
      },
      toggleCollapsed(){
        this.collapsed = this.container.is_collapsed ? '▹' : '▿';
      },
      toggleChildrenContainers() {
        axiosInstance.put('/containers/'+ String(this.container.id)+'/', {
          is_collapsed : !this.container.is_collapsed,
        }, {
        partial: true
        })
        .then(response => {
          console.log('Container updated.')
          this.container.is_collapsed = !this.container.is_collapsed
          this.toggleCollapsed()
        })
        .catch(error => {
          console.error('Error updating container:', error)
        })
      }
    }
  }
  </script>


<style>
ul {
  margin: 0;
}

.collapsed {
  display: none;
}

.collapse-triangle {
  background-color: transparent;
  color: white;
  border: none;
}

.dot {
  padding: 0 .5rem
}
</style>
